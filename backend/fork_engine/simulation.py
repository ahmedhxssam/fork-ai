"""Physical discrete-event execution and bounded genuine residual replanning."""
from copy import deepcopy
import math
import hashlib
import json
from .planner import COMMODITIES, LOAD_SECONDS, road_data, recover_plan


def _zero():
    return {c:0 for c in COMMODITIES}


def _route_operations(scenario, routes, revision):
    graph,paths,_,_=road_data(scenario)
    nodes={n['id']:n for n in scenario['nodes']}
    operations=[]
    for route in routes:
        vid=route['vehicle_id']; t=route['preload_ready']; at=route['preload_node']
        def drive(target):
            nonlocal t,at
            for a,b in zip(paths[at][target],paths[at][target][1:]):
                e=graph[a][b]
                operations.append(dict(kind='travel',vehicle_id=vid,start=t,end=t+e['seconds'],from_id=a,to_id=b,edge_id=e['id'],distance_m=e['distance_m'],revision=revision))
                t+=e['seconds']
            at=target
        if route['reload']:
            drive(scenario['depot_id'])
            if sum(route['manifest'].values()):
                operations.append(dict(kind='load',vehicle_id=vid,start=t,end=t+LOAD_SECONDS,node_id=at,manifest=deepcopy(route['manifest']),revision=revision))
                t+=LOAD_SECONDS
            # Planned start includes bounded loading duration even for an empty grant.
            t=max(t,route['ready_at'])
        schedule={s['node_id']:s['service_start'] for s in route['schedule']}
        for target in route['stops']:
            drive(target)
            n=nodes[target]; t=max(t,schedule[target],n['window_start'])
            operations.append(dict(kind='service',vehicle_id=vid,start=t,end=t+n['service_seconds'],node_id=target,quantity=n['demand'],commodity=n['commodity'],revision=revision))
            t+=n['service_seconds']
        drive(scenario['depot_id'])
    return operations


def _project(scenario, operations, shock):
    """Actual state at shock, plus separately projected locked completions."""
    states={v['id']:dict(node_id=scenario['depot_id'],ready=shock,onboard=_zero()) for v in scenario['vehicles']}
    depot=deepcopy(scenario['inventory']); done=set(); locked={}
    for op in sorted(operations,key=lambda x:(x['end'],x['vehicle_id'])):
        st=states[op['vehicle_id']]
        if op['end']<=shock:
            if op['kind']=='travel': st['node_id']=op['to_id']
            if op['kind']=='load':
                for c in COMMODITIES:
                    st['onboard'][c]+=op['manifest'][c]; depot[c]-=op['manifest'][c]
            if op['kind']=='service':
                st['onboard'][op['commodity']]-=op['quantity']; done.add(op['node_id'])
        elif op['start']<shock:
            locked[op['vehicle_id']]=op
    return states,depot,done,locked


def _recover(scenario,plan,operations,disruption,adapt):
    shock=disruption['time']; failed=disruption['vehicle_id']
    actual,depot,done,locked=_project(scenario,operations,shock)
    failed_state=deepcopy(actual[failed]); failop=locked.get(failed)
    kept=[]
    for op in operations:
        if op['end']<=shock:
            kept.append(op)
        elif op['vehicle_id']==failed:
            if op['start']<shock:
                partial=deepcopy(op); partial['original_end']=op['end']; partial['end']=shock; partial['interrupted']=True
                kept.append(partial)
        elif not adapt or locked.get(op['vehicle_id']) is op:
            kept.append(op)
    nodes={n['id']:n for n in scenario['nodes']}
    position=[nodes[failed_state['node_id']]['x'],nodes[failed_state['node_id']]['y']]
    breakdown=dict(time=shock,kind='breakdown',vehicle_id=failed,node_id=failed_state['node_id'],position=position,stranded=failed_state['onboard'],distance_m=0,summary=f'Vehicle {failed} unavailable; onboard cargo stranded.')
    if failop and failop['kind']=='travel':
        a,b=nodes[failop['from_id']],nodes[failop['to_id']]
        progress=(shock-failop['start'])/(failop['end']-failop['start'])
        breakdown.update(node_id=None,edge_id=failop['edge_id'],edge_progress=progress,distance_m=math.floor(failop['distance_m']*progress),position=[a['x']+(b['x']-a['x'])*progress,a['y']+(b['y']-a['y'])*progress])
    if failop and failop['kind']=='load':
        breakdown['cancelled_load']=failop['manifest']
    if not adapt:
        return kept,[breakdown],None
    input_snapshot=dict(time=shock,vehicles=deepcopy(actual),depot_inventory=deepcopy(depot),completed_orders=sorted(done),disruption=deepcopy(disruption))
    commitments=[deepcopy(locked[v]) for v in sorted(locked) if v!=failed]
    projected=deepcopy(actual); projected.pop(failed)
    for vid,op in locked.items():
        if vid==failed: continue
        st=projected[vid]; st['ready']=op['end']
        if op['kind']=='travel': st['node_id']=op['to_id']
        if op['kind']=='service':
            st['onboard'][op['commodity']]-=op['quantity']; done.add(op['node_id'])
        if op['kind']=='load':
            for c in COMMODITIES:
                st['onboard'][c]+=op['manifest'][c]; depot[c]-=op['manifest'][c]
    recovered=recover_plan(scenario,plan,projected,depot,done)
    recovered['input_snapshot']=input_snapshot
    recovered['locked_commitments']=commitments
    recovered['input_state_hash']=hashlib.sha256(json.dumps(dict(snapshot=input_snapshot,locked_commitments=commitments),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    # If no solver incumbent exists, finish only locked actions and return safely.
    assigned={r['vehicle_id'] for r in recovered['routes']}
    for vid,st in projected.items():
        if vid not in assigned:
            recovered['routes'].append(dict(vehicle_id=vid,stops=[],manifest=_zero(),schedule=[],start_node=st['node_id'],ready_at=st['ready'],preload_node=st['node_id'],preload_ready=st['ready'],reload=False,onboard=st['onboard']))
    kept+=_route_operations(scenario,recovered['routes'],1)
    metadata=[breakdown,dict(time=shock,kind='replan',summary='Residual routes recomputed from physical readiness, locked commitments and shared depot stock.',excluded_orders=sorted(done),projected_states=projected,free_depot_inventory=depot),dict(time=shock,kind='plan_accepted',revision=1,summary='Recovery plan accepted.',routes=recovered['routes'],solver=recovered['solver'])]
    return kept,metadata,recovered


def _events(scenario,operations,metadata,plan):
    nodes={n['id']:n for n in scenario['nodes']}
    rows=[(-1,'',-1,dict(time=0,kind='plan_accepted',revision=0,summary='Initial routing plan accepted.'))]
    trajectories=[]
    for i,op in enumerate(operations):
        vid=op['vehicle_id']; start=op['start']; end=op['end']; rev=op['revision']
        common=dict(vehicle_id=vid,revision=rev)
        if op['kind']=='load':
            rows.append((4,vid,i,dict(time=start,kind='load_start',node_id=op['node_id'],manifest=op['manifest'],complete_at=op.get('original_end',end),summary=f'{vid} loading at depot.',**common)))
            if not op.get('interrupted'):
                rows.append((0,vid,i,dict(time=end,kind='load',node_id=op['node_id'],manifest=op['manifest'],started_at=start,summary=f'{vid} loaded {sum(op["manifest"].values())} meals.',**common)))
        elif op['kind']=='service':
            rows.append((4,vid,i,dict(time=start,kind='service_start',node_id=op['node_id'],quantity=op['quantity'],commodity=op['commodity'],complete_at=op.get('original_end',end),summary=f'{vid} serving {nodes[op["node_id"]]["name"]}.',**common)))
            if not op.get('interrupted'):
                rows.append((0,vid,i,dict(time=end,kind='delivery',node_id=op['node_id'],quantity=op['quantity'],commodity=op['commodity'],service_start=start,delivery_id=f'{vid}-{op["node_id"]}',summary=f'{op["quantity"]} meals delivered to {nodes[op["node_id"]]["name"]}.',**common)))
        else:
            original_end=op.get('original_end',end)
            a,b=nodes[op['from_id']],nodes[op['to_id']]
            progress=(end-start)/(original_end-start)
            path=[[a['x'],a['y']],[a['x']+(b['x']-a['x'])*progress,a['y']+(b['y']-a['y'])*progress]]
            distance=math.floor(op['distance_m']*progress)
            rows.append((4,vid,i,dict(time=start,kind='depart',from_id=op['from_id'],to_id=op['to_id'],edge_id=op['edge_id'],arrive=original_end,distance_m=op['distance_m'],summary=f'{vid} travelling to {b["name"]}.',**common)))
            trajectories.append(dict(vehicle_id=vid,from_id=op['from_id'],to_id=f'breakdown:{vid}' if op.get('interrupted') else op['to_id'],depart=start,arrive=end,path=path,distance_m=distance,revision=rev,edge_id=op['edge_id'],progress=progress))
            if not op.get('interrupted'):
                rows.append((0,vid,i,dict(time=end,kind='arrive',from_id=op['from_id'],node_id=op['to_id'],edge_id=op['edge_id'],distance_m=distance,depart=start,summary=f'{vid} arrived at {b["name"]}.',**common)))
                if op['to_id']==scenario['depot_id']:
                    rows.append((0,vid,i+0.1,dict(time=end,kind='return',node_id=op['to_id'],summary=f'{vid} returned to depot.',**common)))
    for i,event in enumerate(metadata):
        rows.append((2 if event['kind']=='breakdown' else 3,'',i,event))
    rows.append((9,'',0,dict(time=scenario['horizon'],kind='horizon',summary='Mission horizon reached.')))
    rows.sort(key=lambda r:(r[3]['time'],r[0],r[1],r[2]))
    events=[]
    for i,(_,_,_,event) in enumerate(rows):
        events.append(dict(id=f'event-{i:04d}',seq=i,**event))
    trajectories.sort(key=lambda t:(t['depart'],t['vehicle_id']))
    return events,trajectories


def _summarize(scenario, events, trajectories):
    nodes={n['id']:n for n in scenario['nodes']}
    vehicles={v['id']:v for v in scenario['vehicles']}
    final=dict(depot_inventory=deepcopy(scenario['inventory']),onboard={v:_zero() for v in vehicles},stranded=_zero(),delivered=_zero(),vehicles={v:dict(node_id=scenario['depot_id'],status='available',position=[nodes[scenario['depot_id']]['x'],nodes[scenario['depot_id']]['y']]) for v in vehicles})
    deliveries=[]
    for e in events:
        vid=e.get('vehicle_id')
        if e['kind']=='load':
            for c in COMMODITIES:
                final['depot_inventory'][c]-=e['manifest'][c]; final['onboard'][vid][c]+=e['manifest'][c]
        elif e['kind']=='delivery':
            c=e['commodity']; q=e['quantity']; n=nodes[e['node_id']]
            final['onboard'][vid][c]-=q; final['delivered'][c]+=q
            deliveries.append(dict(id=e['delivery_id'],destination_id=e['node_id'],vehicle_id=vid,quantity=q,commodity=c,service_start=e['service_start'],completed_at=e['time'],priority=n['priority'],on_time=e['time']<=n['due']))
        elif e['kind']=='arrive':
            n=nodes[e['node_id']]; final['vehicles'][vid].update(node_id=n['id'],position=[n['x'],n['y']])
        elif e['kind']=='breakdown':
            for c in COMMODITIES:
                final['stranded'][c]+=final['onboard'][vid][c]; final['onboard'][vid][c]=0
            final['vehicles'][vid].update(status='failed',node_id=e.get('node_id'),position=e['position'])
    demand=sum(n['demand'] for n in nodes.values()); delivered=sum(d['quantity'] for d in deliveries)
    on_time=sum(d['quantity'] for d in deliveries if d['on_time'])
    priority_demand=sum(n['demand'] for n in nodes.values() if n['priority']==3)
    weighted_demand=sum(n['demand']*n['priority'] for n in nodes.values())
    distances={v:sum(t['distance_m'] for t in trajectories if t['vehicle_id']==v) for v in vehicles}
    metrics=dict(meals_delivered=delivered,demand=demand,coverage=delivered/demand if demand else 1,on_time_meals=on_time,on_time_coverage=on_time/demand if demand else 1,priority_coverage=sum(d['quantity'] for d in deliveries if d['priority']==3 and d['on_time'])/priority_demand if priority_demand else 1,priority_weighted_coverage=sum(d['quantity']*d['priority'] for d in deliveries if d['on_time'])/weighted_demand if weighted_demand else 1,destinations_served=len(deliveries),late_deliveries=sum(not d['on_time'] for d in deliveries),unserved_meals=demand-delivered,distance_m=sum(distances.values()),cost_cents=sum(round(distances[v]*vehicles[v]['cost_per_km']/1000) for v in vehicles),emissions_g=sum(round(distances[v]*vehicles[v]['emissions_per_km']/1000) for v in vehicles),violations=0)
    return final,deliveries,metrics


def simulate_world(scenario: dict, plan: dict, disruption: dict | None = None, adapt: bool = True) -> dict:
    if plan['initial_hash']!=scenario['hash']:
        raise ValueError('Plan scenario hash mismatch')
    if disruption:
        if disruption.get('vehicle_id') not in {v['id'] for v in scenario['vehicles']}:
            raise ValueError('Unknown disruption vehicle')
        if not isinstance(disruption.get('time'),int) or isinstance(disruption['time'],bool) or not 0<=disruption['time']<=scenario['horizon']:
            raise ValueError('Disruption time must be an integer within the horizon')
    plan=deepcopy(plan); scenario=deepcopy(scenario)
    operations=_route_operations(scenario,plan['routes'],0)
    metadata=[]; recovery=None
    if disruption:
        operations,metadata,recovery=_recover(scenario,plan,operations,disruption,adapt)
    events,trajectories=_events(scenario,operations,metadata,plan)
    final,deliveries,metrics=_summarize(scenario,events,trajectories)
    return dict(id=plan['policy'],policy=plan['policy'],name=plan['policy'].title(),initial_hash=scenario['hash'],plan=plan,trajectories=trajectories,deliveries=deliveries,events=events,final_state=final,metrics=metrics,solver=plan['solver'],policy_config=plan['policy_config'],mode='deterministic',disruption=deepcopy(disruption),adapt=adapt,recovery_plan=recovery,baseline_kind=plan.get('baseline_kind'))
