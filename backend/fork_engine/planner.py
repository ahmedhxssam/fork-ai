"""Bounded deterministic OR-Tools Routing with joint commodity budgets."""
from copy import deepcopy
from itertools import product
import networkx as nx
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

COMMODITIES = ('ambient', 'chilled')
LOAD_SECONDS = 120
POLICIES = {
    'velocity': dict(meal_penalty=1800, priority_power=0, lateness_per_second=12, distance_weight=1, reserve_ambient=0, reserve_chilled=0),
    'resilience': dict(meal_penalty=1800, priority_power=1, lateness_per_second=4, distance_weight=1, reserve_ambient=32, reserve_chilled=0),
    'equity': dict(meal_penalty=1800, priority_power=3, lateness_per_second=16, distance_weight=1, reserve_ambient=0, reserve_chilled=0),
}


def road_data(scenario):
    graph=nx.DiGraph()
    graph.add_nodes_from(n['id'] for n in scenario['nodes'])
    for e in scenario['edges']:
        graph.add_edge(e['source'],e['target'],**e)
    paths=dict(nx.all_pairs_dijkstra_path(graph,weight='seconds'))
    travel={}; distance={}
    for a, targets in paths.items():
        for b,path in targets.items():
            es=[graph[u][v] for u,v in zip(path,path[1:])]
            travel[a,b]=sum(e['seconds'] for e in es)
            distance[a,b]=sum(e['distance_m'] for e in es)
    return graph,paths,travel,distance


def _config(policy, config):
    if policy not in POLICIES:
        raise ValueError('policy must be velocity, resilience or equity')
    p=deepcopy(POLICIES[policy])
    if config:
        if set(config)-set(p):
            raise ValueError('Unknown policy configuration key')
        for k,v in config.items():
            if not isinstance(v,int) or isinstance(v,bool) or not 0<=v<=100000:
                raise ValueError('Policy values must be nonnegative bounded integers')
        p.update(config)
    if p['priority_power']>4:
        raise ValueError('priority_power exceeds bounded objective range')
    return p


def _solve(scenario, policy, config, orders, states, free_stock, reloads, initial=False):
    """Each routing vehicle has commodity grants, constrained jointly by stock."""
    graph,paths,travel,dist=road_data(scenario)
    by={n['id']:n for n in scenario['nodes']}
    veh={v['id']:v for v in scenario['vehicles']}
    volunteers={v['id']:v for v in scenario['volunteers']}
    active=[]
    for vid in sorted(states):
        v=veh[vid]; st=deepcopy(states[vid]); vol=volunteers[v['driver_id']]
        st['deadline']=min(v['shift_end'],vol['shift_end'],scenario['horizon'])
        st['ready']=max(st['ready'],v['shift_start'],vol['shift_start'])
        st['preload_node']=st['node_id']; st['preload_ready']=st['ready']
        if reloads.get(vid):
            if (st['node_id'],scenario['depot_id']) not in travel:
                continue
            st['ready']+=travel[st['node_id'],scenario['depot_id']]+LOAD_SECONDS
            st['node_id']=scenario['depot_id']
        if (st['node_id'],scenario['depot_id']) not in travel or st['ready']+travel[st['node_id'],scenario['depot_id']]>st['deadline']:
            continue
        active.append((vid,st))
    if not active:
        return None
    ids=[n['id'] for n in orders]+[st['node_id'] for _,st in active]+[scenario['depot_id']]
    count=len(orders); depot_index=len(ids)-1
    manager=pywrapcp.RoutingIndexManager(len(ids),len(active),list(range(count,count+len(active))),[depot_index]*len(active))
    routing=pywrapcp.RoutingModel(manager)
    solver=routing.solver()
    def time_callback(i,j):
        a,b=manager.IndexToNode(i),manager.IndexToNode(j)
        return travel.get((ids[a],ids[b]),1000000)+(by[ids[a]]['service_seconds'] if a<count else 0)
    ti=routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(ti,scenario['horizon'],scenario['horizon'],False,'Time')
    times=routing.GetDimensionOrDie('Time')
    for vi,(vid,st) in enumerate(active):
        times.CumulVar(routing.Start(vi)).SetRange(st['ready'],st['ready'])
        times.CumulVar(routing.End(vi)).SetRange(0,st['deadline'])
        def cost(i,j,vid=vid):
            a,b=ids[manager.IndexToNode(i)],ids[manager.IndexToNode(j)]
            return dist.get((a,b),1000000)*config['distance_weight']
        ci=routing.RegisterTransitCallback(cost)
        routing.SetArcCostEvaluatorOfVehicle(ci,vi)
    feasible=[]
    for ni,n in enumerate(orders):
        ix=manager.NodeToIndex(ni)
        latest=n['window_end']-n['service_seconds']
        eligible=[vi for vi,(vid,st) in enumerate(active) if (n['commodity']!='chilled' or veh[vid]['chilled']) and (st['node_id'],n['id']) in travel and (n['id'],scenario['depot_id']) in travel]
        if latest<n['window_start'] or not eligible:
            solver.Add(routing.ActiveVar(ix)==0)
        else:
            times.CumulVar(ix).SetRange(n['window_start'],latest)
            routing.VehicleVar(ix).SetValues([-1]+eligible)
            times.SetCumulVarSoftUpperBound(ix,max(0,n['due']-n['service_seconds']),config['lateness_per_second']*max(1,n['priority']**config['priority_power']))
        penalty=n['demand']*config['meal_penalty']*max(1,n['priority']**config['priority_power'])
        routing.AddDisjunction([ix],penalty)
    grants={}
    for vi,(vid,st) in enumerate(active):
        grant_list=[]
        for c in COMMODITIES:
            upper=min(free_stock.get(c,0),veh[vid]['capacity']) if reloads.get(vid) and (c!='chilled' or veh[vid]['chilled']) else 0
            grant=solver.IntVar(0,upper,f'grant_{vid}_{c}')
            grants[vid,c]=grant; grant_list.append(grant)
            assigned=[solver.IsEqualCstVar(routing.VehicleVar(manager.NodeToIndex(ni)),vi)*n['demand'] for ni,n in enumerate(orders) if n['commodity']==c]
            solver.Add(solver.Sum(assigned)<=st['onboard'].get(c,0)+grant)
        solver.Add(solver.Sum(grant_list)+sum(st['onboard'].values())<=veh[vid]['capacity'])
    for c in COMMODITIES:
        solver.Add(solver.Sum([grants[vid,c] for vid,_ in active])<=free_stock.get(c,0))
    params=pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT
    params.solution_limit=1
    params.time_limit.seconds=3
    solution=routing.SolveWithParameters(params)
    if not solution:
        return None
    routes=[]
    for vi,(vid,st) in enumerate(active):
        index=routing.Start(vi); stops=[]; schedule=[]; amounts={c:0 for c in COMMODITIES}
        while not routing.IsEnd(index):
            ni=manager.IndexToNode(index)
            if ni<count:
                n=orders[ni]; stops.append(n['id']); amounts[n['commodity']]+=n['demand']
                schedule.append(dict(node_id=n['id'],service_start=solution.Value(times.CumulVar(index))))
            index=solution.Value(routing.NextVar(index))
        manifest={c:max(0,amounts[c]-st['onboard'].get(c,0)) for c in COMMODITIES}
        routes.append(dict(vehicle_id=vid,stops=stops,manifest=manifest,schedule=schedule,start_node=st['node_id'],ready_at=st['ready'],return_at=solution.Value(times.CumulVar(index)),reload=bool(reloads.get(vid)),preload_node=st['preload_node'],preload_ready=st['preload_ready'],onboard=st['onboard']))
    return dict(routes=routes,objective=solution.ObjectiveValue(),status=int(routing.status()))


def _solver_meta(candidate_count=1):
    return dict(algorithm='OR-Tools Routing / parallel cheapest insertion',status='feasible_constructive_incumbent',budget={'solution_limit_per_candidate':1,'watchdog_seconds_per_candidate':3,'candidates':candidate_count},optimal=False,deterministic_work_limit=True,objective='Integer distance metres + meal omission penalties + service-start tardiness seconds; proxy objective, not exact on-time coverage.')


def plan_world(scenario: dict, policy: str, policy_config: dict | None = None) -> dict:
    config=_config(policy,policy_config)
    states={v['id']:dict(node_id=scenario['depot_id'],ready=v['shift_start'],onboard={c:0 for c in COMMODITIES}) for v in scenario['vehicles']}
    stock={c:max(0,scenario['inventory'][c]-config['reserve_'+c]) for c in COMMODITIES}
    orders=[n for n in scenario['nodes'] if n['kind']=='destination']
    solved=_solve(scenario,policy,config,orders,states,stock,{vid:True for vid in states},True)
    meta=_solver_meta()
    if solved is None:
        meta['status']='no_incumbent_empty_feasible_fallback'
    routes=solved['routes'] if solved else []
    return dict(routes=routes,manifests={r['vehicle_id']:r['manifest'] for r in routes},policy=policy,policy_config=config,solver=meta,initial_hash=scenario['hash'],omitted=[n['id'] for n in orders if not any(n['id'] in r['stops'] for r in routes)])


def recover_plan(scenario, plan, states, depot_stock, excluded):
    config=plan['policy_config']; policy=plan['policy']
    orders=[n for n in scenario['nodes'] if n['kind']=='destination' and n['id'] not in excluded]
    candidates=[]
    for flags in product([False,True],repeat=len(states)):
        pattern=dict(zip(sorted(states),flags))
        candidate=_solve(scenario,policy,config,orders,states,depot_stock,pattern)
        if candidate:
            # Include the actual depot detours in the candidate proxy objective.
            _,_,_,distance=road_data(scenario)
            candidate['objective']+=sum(distance[states[v]['node_id'],scenario['depot_id']]*config['distance_weight'] for v in states if pattern[v])
            candidates.append(candidate)
    if not candidates:
        return dict(routes=[],solver={**_solver_meta(2**len(states)),'status':'no_incumbent_return_only_fallback'})
    chosen=min(candidates,key=lambda c:(c['objective'],str(c['routes'])))
    return dict(routes=chosen['routes'],solver=_solver_meta(2**len(states)))


def plan_baseline(scenario: dict, kind: str = 'greedy') -> dict:
    """Two conventional diagnostics; same stock, roads and physical simulator."""
    if kind=='solver_only':
        plan=plan_world(scenario,'velocity',dict(priority_power=0,lateness_per_second=0,reserve_ambient=0,reserve_chilled=0))
        plan['baseline_kind']=kind
        plan['solver']['objective']='Neutral meal-weighted omissions + travel metres; no priority, deadline or reserve preference.'
        return plan
    if kind!='greedy':
        raise ValueError('baseline kind must be greedy or solver_only')
    _,_,travel,distance=road_data(scenario)
    depot=scenario['depot_id']; stock=deepcopy(scenario['inventory'])
    remaining={n['id']:n for n in scenario['nodes'] if n['kind']=='destination'}
    volunteers={v['id']:v for v in scenario['volunteers']}
    routes=[]
    for vehicle in sorted(scenario['vehicles'],key=lambda v:v['id']):
        vid=vehicle['id']; vol=volunteers[vehicle['driver_id']]
        start=max(vehicle['shift_start'],vol['shift_start'])
        deadline=min(vehicle['shift_end'],vol['shift_end'],scenario['horizon'])
        t=start+LOAD_SECONDS; at=depot; manifest={c:0 for c in COMMODITIES}; stops=[]; schedule=[]
        while True:
            feasible=[]
            for id,node in sorted(remaining.items()):
                c=node['commodity']; q=node['demand']
                if (at,id) not in travel or (id,depot) not in travel: continue
                if c=='chilled' and not vehicle['chilled']: continue
                if q>stock[c] or sum(manifest.values())+q>vehicle['capacity']: continue
                service_start=max(t+travel[at,id],node['window_start'])
                completed=service_start+node['service_seconds']
                if completed>node['window_end'] or completed+travel[id,depot]>deadline: continue
                feasible.append((travel[at,id],distance[at,id],id,service_start,completed))
            if not feasible: break
            _,_,id,service_start,t=min(feasible)
            node=remaining.pop(id); stock[node['commodity']]-=node['demand']; manifest[node['commodity']]+=node['demand']
            stops.append(id); schedule.append(dict(node_id=id,service_start=service_start)); at=id
        routes.append(dict(vehicle_id=vid,stops=stops,manifest=manifest,schedule=schedule,start_node=depot,ready_at=start+LOAD_SECONDS,return_at=t+travel.get((at,depot),0),reload=True,preload_node=depot,preload_ready=start,onboard={c:0 for c in COMMODITIES}))
    config=_config('velocity',dict(priority_power=0,lateness_per_second=0,reserve_ambient=0,reserve_chilled=0))
    return dict(routes=routes,manifests={r['vehicle_id']:r['manifest'] for r in routes},policy='velocity',policy_config=config,solver=dict(algorithm='Fixed vehicle-order nearest-feasible greedy',status='feasible_heuristic',budget={'candidate_order':'vehicle ID, shortest travel seconds, distance, destination ID'},optimal=False,objective='Choose the nearest currently feasible whole order until no next order fits.'),initial_hash=scenario['hash'],omitted=sorted(remaining),baseline_kind='greedy')
