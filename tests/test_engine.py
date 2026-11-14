"""Behavioral engine checks: removal of routing/custody/timing causes failures."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest


def engine():
    assert Path('backend/fork_engine/scenario.py').exists(), 'Scenario engine not implemented'
    from backend.fork_engine.scenario import create_scenario
    from backend.fork_engine.planner import plan_world
    from backend.fork_engine.simulation import simulate_world
    return create_scenario, plan_world, simulate_world


def test_real_routes_reproducible_and_worlds_are_isolated():
    create, plan, simulate = engine()
    s = create(26)
    before = copy.deepcopy(s)
    results = [simulate(s, plan(s, p)) for p in ('velocity', 'resilience', 'equity')]
    assert s == before
    assert all(r['initial_hash'] == s['hash'] for r in results)
    assert all(r['metrics']['meals_delivered'] > 0 for r in results)
    assert all('OR-Tools' in r['solver']['algorithm'] for r in results)
    assert len({json.dumps(r['plan']['routes'], sort_keys=True) for r in results}) > 1
    assert plan(s, 'velocity') == plan(s, 'velocity')
    results[0]['final_state']['depot_inventory']['ambient'] = -999
    assert results[1]['final_state']['depot_inventory']['ambient'] >= 0


@pytest.mark.parametrize('vehicle', ['A', 'B', 'C'])
@pytest.mark.parametrize('shock_time', [0, 60, 120, 750, 2500, 7000, 14400])
def test_breakdowns_conserve_stock_and_preserve_completed_prefix(vehicle, shock_time):
    create, plan, simulate = engine()
    s = create()
    p = plan(s, 'resilience')
    base = simulate(s, p)
    r = simulate(s, p, {'vehicle_id': vehicle, 'time': shock_time})
    f = r['final_state']
    for c in ('ambient', 'chilled'):
        assert s['inventory'][c] == f['depot_inventory'][c] + f['stranded'][c] + f['delivered'][c] + sum(v[c] for v in f['onboard'].values())
    assert [e for e in base['events'] if e['time'] < shock_time] == [e for e in r['events'] if e['time'] < shock_time]
    assert not any(d['vehicle_id'] == vehicle and d['completed_at'] > shock_time for d in r['deliveries'])
    assert len({d['destination_id'] for d in r['deliveries']}) == len(r['deliveries'])
    assert all(t['arrive'] <= shock_time for t in r['trajectories'] if t['vehicle_id'] == vehicle)
    for v in s['vehicles']:
        if v['id'] != vehicle:
            assert f['vehicles'][v['id']]['node_id'] == s['depot_id']


def tiny_fixture():
    create, _, _ = engine()
    s = create()
    s['nodes'] = [dict(id='depot',name='Depot',x=0,y=0,kind='depot',demand=0,commodity='ambient',priority=0,window_start=0,window_end=14400,due=14400,service_seconds=0),dict(id='one',name='One',x=100,y=0,kind='destination',demand=10,commodity='ambient',priority=3,window_start=0,window_end=1000,due=300,service_seconds=60)]
    s['edges'] = [dict(id='out',source='depot',target='one',distance_m=1000,seconds=100),dict(id='back',source='one',target='depot',distance_m=1000,seconds=100)]
    s['vehicles'] = [s['vehicles'][0]]
    s['volunteers'] = [s['volunteers'][0]]
    s['inventory'] = {'ambient':10,'chilled':0}
    return s


def test_hand_calculated_route_and_mid_edge_failure():
    _, plan, simulate = engine()
    s=tiny_fixture()
    p=plan(s,'velocity')
    base=simulate(s,p)
    assert base['deliveries'][0]['service_start'] == 220
    assert base['deliveries'][0]['completed_at'] == 280
    assert base['metrics']['distance_m'] == 2000
    r=simulate(s,p,{'vehicle_id':'A','time':170})
    assert r['deliveries'] == []
    assert r['metrics']['distance_m'] == 500
    assert r['final_state']['stranded']['ambient'] == 10
    assert r['trajectories'][0]['arrive'] == 170
    assert r['trajectories'][0]['path'][-1] == [50,0]


@pytest.mark.parametrize('time,delivered,stranded,depot',[(60,0,0,10),(120,0,10,0),(250,0,10,0),(280,10,0,0)])
def test_atomic_loading_service_and_exact_completion_precedence(time,delivered,stranded,depot):
    _,plan,simulate=engine()
    s=tiny_fixture()
    r=simulate(s,plan(s,'velocity'),{'vehicle_id':'A','time':time})
    assert r['final_state']['delivered']['ambient']==delivered
    assert r['final_state']['stranded']['ambient']==stranded
    assert r['final_state']['depot_inventory']['ambient']==depot


def test_hard_window_and_cold_capacity_omit_infeasible_orders():
    _,plan,simulate=engine()
    s=tiny_fixture()
    s['nodes'][1]['window_end']=270
    r=simulate(s,plan(s,'velocity'))
    assert r['deliveries']==[]
    s['nodes'][1]['window_end']=1000
    s['nodes'][1]['commodity']='chilled'
    s['inventory']={'ambient':0,'chilled':10}
    assert simulate(s,plan(s,'velocity'))['deliveries']==[]


def test_recovery_binds_actual_snapshot_separately_from_future_locked_loads():
    create, plan, simulate = engine()
    s=create()
    r=simulate(s,plan(s,'resilience'),{'vehicle_id':'A','time':60})
    recovery=r['recovery_plan']
    assert 'input_snapshot' in recovery, 'Recovery must be bound to actual pre-projection custody'
    assert recovery['input_snapshot']['depot_inventory']=={'ambient':192,'chilled':48}
    assert all(sum(st['onboard'].values())==0 for st in recovery['input_snapshot']['vehicles'].values())
    assert len(recovery['input_state_hash'])==64
    assert {x['vehicle_id'] for x in recovery['locked_commitments']}=={'B','C'}
    assert all(x['end']==120 for x in recovery['locked_commitments'])
    assert all(e['time']==120 for e in r['events'] if e['kind']=='load' and e.get('revision')==0)


def test_healthy_service_is_locked_and_cannot_be_reassigned():
    create,plan,simulate=engine()
    s=create(); p=plan(s,'resilience'); base=simulate(s,p)
    service=next(e for e in base['events'] if e['kind']=='service_start' and e['vehicle_id']=='A')
    shock=service['time']+1
    r=simulate(s,p,{'vehicle_id':'B','time':shock})
    old=next(d for d in base['deliveries'] if d['destination_id']==service['node_id'])
    assert [d for d in r['deliveries'] if d['destination_id']==service['node_id']]==[old]
    assert all(service['node_id'] not in route['stops'] for route in r['recovery_plan']['routes'])
    completion=next(e for e in r['events'] if e['kind']=='delivery' and e['node_id']==service['node_id'])
    assert completion['time']>shock


def test_joint_reloads_never_double_spend_and_unused_cargo_occupies_capacity():
    create,plan,simulate=engine()
    s=create(); p=plan(s,'resilience')
    for time in [60,1800,2500]:
        r=simulate(s,p,{'vehicle_id':'A','time':time})
        stock=copy.deepcopy(s['inventory']); onboard={v['id']:{'ambient':0,'chilled':0} for v in s['vehicles']}
        for event in r['events']:
            vid=event.get('vehicle_id')
            if event['kind']=='load':
                for c,q in event['manifest'].items():
                    stock[c]-=q; onboard[vid][c]+=q
            elif event['kind']=='delivery':
                onboard[vid][event['commodity']]-=event['quantity']
            elif event['kind']=='breakdown':
                onboard[vid]={'ambient':0,'chilled':0}
            assert all(q>=0 for q in stock.values())
            for vehicle in s['vehicles']:
                cargo=onboard[vehicle['id']]
                assert all(q>=0 for q in cargo.values())
                assert sum(cargo.values())<=vehicle['capacity']
                assert not cargo['chilled'] or vehicle['chilled']
        recovery=r['recovery_plan']
        free=next(e['free_depot_inventory'] for e in r['events'] if e['kind']=='replan')
        for commodity in ['ambient','chilled']:
            assert sum(route['manifest'][commodity] for route in recovery['routes'])<=free[commodity]


def test_exact_time_old_completions_are_identical_and_failure_blocks_new_departure():
    _,plan,simulate=engine()
    s=tiny_fixture(); p=plan(s,'velocity'); base=simulate(s,p)
    r=simulate(s,p,{'vehicle_id':'A','time':280})
    before=[e for e in base['events'] if e['time']<280 or (e['time']==280 and e['kind']=='delivery')]
    assert r['events'][:len(before)]==before
    assert not any(e['kind']=='depart' and e['time']==280 for e in r['events'])


def test_late_priority_three_meals_do_not_count_on_time_priority_coverage():
    _,plan,simulate=engine()
    s=tiny_fixture(); s['nodes'][1]['due']=279
    r=simulate(s,plan(s,'velocity'))
    assert r['metrics']['coverage']==1
    assert r['metrics']['priority_coverage']==0
    assert r['metrics']['priority_weighted_coverage']==0


def test_diagnostic_baselines_route_real_stock_with_distinct_algorithms():
    import backend.fork_engine.planner as planner
    assert hasattr(planner,'plan_baseline'), 'Genuine conventional comparators are missing'
    create,_,simulate=engine()
    from backend.fork_engine.verifier import verify_world
    s=create()
    greedy=planner.plan_baseline(s,'greedy')
    neutral=planner.plan_baseline(s,'solver_only')
    for p in [greedy,neutral]:
        assert p['baseline_kind'] in ['greedy','solver_only']
        r=simulate(s,p)
        assert r['metrics']['meals_delivered']>0
        assert verify_world(s,r)['valid']
    assert 'greedy' in greedy['solver']['algorithm'].lower()
    assert 'OR-Tools' in neutral['solver']['algorithm']
    assert neutral['policy_config']['priority_power']==0
    assert neutral['policy_config']['lateness_per_second']==0


def test_greedy_selects_nearest_feasible_order_and_preserves_return_shift():
    import backend.fork_engine.planner as planner
    assert hasattr(planner,'plan_baseline'), 'Nearest-feasible comparator is missing'
    s=tiny_fixture()
    other=copy.deepcopy(s['nodes'][1]); other.update(id='near',name='Near',x=20,demand=3)
    s['nodes'].append(other)
    s['edges'] += [dict(id='near-out',source='depot',target='near',distance_m=200,seconds=20),dict(id='near-back',source='near',target='depot',distance_m=200,seconds=20)]
    s['inventory']['ambient']=13
    p=planner.plan_baseline(s,'greedy')
    assert p['routes'][0]['stops'][0]=='near'
    s['vehicles'][0]['shift_end']=200
    p=planner.plan_baseline(s,'greedy')
    assert p['routes'][0]['stops']==[]
