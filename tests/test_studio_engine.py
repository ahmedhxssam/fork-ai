import copy

import pytest

from backend.studio.compiler import TEMPLATES, compile_brief
from backend.studio.engine import simulate
from backend.studio.schema import model_hash


def task(id, duration=2, **kw):
    return dict(id=id, label=id, duration=duration, skill='work', units=1,
                release=0, due=12, priority=1, value=1, depends_on=[], materials={}, **{}) | kw


def resource(id='a', **kw):
    return dict(id=id, label=id, capacity=1, skills=['work'], cost_per_minute=2) | kw


def model(tasks=None, resources=None, **kw):
    return dict(schema_version='fork-workflow/1', title='Hand derived', horizon=12,
                resources=resources or [resource()], tasks=tasks or [task('one')],
                stock={}, budget_cents=None, events=[]) | kw


def outage(resource_id='a', at=0, duration=3, lost=1, id='failure'):
    return dict(id=id, kind='resource_outage', resource_id=resource_id, at=at,
                duration=duration, capacity_lost=lost, label=id)


def test_hand_derived_dependencies_units_and_metrics():
    m = model([task('one', units=2, materials={'p': 1}), task('two', duration=3, depends_on=['one'], priority=3, due=4)],
              [resource(capacity=2)], stock={'p': 1})
    r = simulate(m, 'throughput')
    assert r['segments'] == [dict(task_id='one', resource_id='a', start=0, end=2, units=2),
                             dict(task_id='two', resource_id='a', start=2, end=5, units=1)]
    assert r['completions'] == [{'task_id': 'one', 'time': 2}, {'task_id': 'two', 'time': 5}]
    assert r['metrics'] == dict(completed=2, total=2, on_time=1, priority_on_time=0,
                               priority_total=1, value_completed=2, value_total=2,
                               cost_cents=14, work_minutes=5, unserved=0, makespan=5)


def test_stock_consumed_once_across_checkpointed_outages():
    m = model([task('one', duration=5, materials={'p': 1})], stock={'p': 1}, events=[outage(at=2, duration=3)])
    r = simulate(m, 'throughput')
    assert [(s['start'], s['end']) for s in r['segments']] == [(0, 2), (5, 8)]
    assert r['completions'] == [{'task_id': 'one', 'time': 8}]
    assert r['metrics']['cost_cents'] == 10
    assert r['model_hash'] == model_hash(m)
    assert simulate(m, 'throughput', events=[])['completions'][0]['time'] == 5
    assert simulate(m, 'throughput', events=[])['model_hash'] == r['model_hash']


def test_adaptation_changes_unstarted_assignment_but_control_retains_original():
    m = model([task('one', duration=4)], [resource('a'), resource('b', cost_per_minute=3)], events=[outage(at=0, duration=10)])
    adapted = simulate(m, 'throughput')
    control = simulate(m, 'throughput', adapt=False)
    assert adapted['segments'][0]['resource_id'] == 'b'
    assert adapted['completions'] == [{'task_id': 'one', 'time': 4}]
    assert control['segments'][0]['resource_id'] == 'a'
    assert control['metrics']['completed'] == 0


def test_started_task_retains_pool_and_healthy_task_not_preempted():
    m = model([task('one', duration=5), task('urgent', duration=2, release=1, priority=3)],
              [resource('a'), resource('b')], events=[outage(at=2, duration=2)])
    r = simulate(m, 'priority')
    assert {s['resource_id'] for s in r['segments'] if s['task_id'] == 'one'} == {'a'}
    assert next(c['time'] for c in r['completions'] if c['task_id'] == 'urgent') == 3


def test_partial_overlapping_outages_capacity_and_horizon():
    m = model([task('one', duration=4, units=2), task('two', duration=4)],
              [resource(capacity=3)], events=[outage(at=1, duration=3), outage(at=2, duration=3, id='second')])
    r = simulate(m, 'throughput')
    for minute in range(m['horizon']):
        used = sum(s['units'] for s in r['segments'] if s['start'] <= minute < s['end'])
        available = 3 - min(3, sum(e['capacity_lost'] for e in m['events'] if e['at'] <= minute < e['at'] + e['duration']))
        assert used <= available
    assert all(s['end'] <= m['horizon'] for s in r['segments'])


def test_budget_only_charged_for_actual_work_and_allows_free_work():
    m = model([task('paid', duration=4), task('free', duration=4, skill='free')],
              [resource(), resource('b', skills=['free'], cost_per_minute=0)], budget_cents=5)
    r = simulate(m, 'throughput')
    assert r['metrics']['cost_cents'] == 4
    assert r['metrics']['completed'] == 1
    assert r['completions'] == [{'task_id': 'free', 'time': 4}]
    assert r['metrics']['work_minutes'] == 6


def test_insufficient_stock_leaves_unserved_and_budget_zero_blocks_paid_start():
    m = model([task('one', materials={'p': 2})], stock={'p': 1})
    assert simulate(m, 'throughput')['segments'] == []
    m = model(budget_cents=0)
    assert simulate(m, 'throughput')['segments'] == []


def test_policy_choices_are_meaningful_and_deterministic():
    m = model([task('short', duration=2, due=12), task('urgent', duration=4, due=4), task('important', duration=3, priority=3)])
    assert simulate(m, 'throughput')['segments'][0]['task_id'] == 'short'
    assert simulate(m, 'resilience')['segments'][0]['task_id'] == 'urgent'
    assert simulate(m, 'priority')['segments'][0]['task_id'] == 'important'
    for policy in ['throughput', 'resilience', 'priority']:
        assert simulate(m, policy) == simulate(m, policy)
        assert simulate(m, policy) | {'adapt': False} == simulate(m, policy, adapt=False)


def test_templates_repeat_without_input_mutation():
    for template in TEMPLATES:
        m = compile_brief(template['brief'])['model']
        before = copy.deepcopy(m)
        for policy in ['throughput', 'resilience', 'priority']:
            assert simulate(m, policy) == simulate(m, policy)
        assert m == before


def test_invalid_policy_or_event_is_rejected():
    with pytest.raises(ValueError):
        simulate(model(), 'fake')
    with pytest.raises(ValueError):
        simulate(model(), 'throughput', events=[outage(lost=2)])


def test_control_delayed_plan_slots_do_not_select_later_work_during_pause():
    m = model([task('first', duration=3, units=2), task('later', duration=2, release=3)],
              [resource(capacity=2)], events=[outage(at=1, duration=4)])
    control = simulate(m, 'throughput', adapt=False)
    adapted = simulate(m, 'throughput')
    first_done = next(c['time'] for c in control['completions'] if c['task_id'] == 'first')
    later_start = next(s['start'] for s in control['segments'] if s['task_id'] == 'later')
    assert later_start >= first_done
    assert next(s['start'] for s in adapted['segments'] if s['task_id'] == 'later') == 3


def test_seeded_physical_sweep_and_nominal_control_parity():
    import random
    from backend.studio.referee import verify
    r=random.Random(2718)
    for seed in range(200):
        resources=[dict(id=f'r{i}',label=f'Pool {i}',capacity=r.randint(1,4),skills=['s'],cost_per_minute=r.randint(0,6)) for i in range(r.randint(1,4))]
        tasks=[]
        for i in range(r.randint(1,15)):
            tasks.append(dict(id=f't{i}',label=f'Task {i}',duration=r.randint(1,12),skill='s',units=r.randint(1,max(x['capacity'] for x in resources)),release=r.randint(0,8),due=r.randint(10,30),priority=r.randint(1,3),value=r.randint(1,10),depends_on=[f't{r.randrange(i)}'] if i and r.random()<.25 else [],materials={'part':r.randint(1,3)} if r.random()<.4 else {}))
        outages=[]
        for i in range(r.randint(0,4)):
            pool=r.choice(resources)
            outages.append(dict(id=f'e{i}',kind='resource_outage',resource_id=pool['id'],at=r.randint(0,28),duration=r.randint(1,12),capacity_lost=r.randint(1,pool['capacity']),label='Outage'))
        model=dict(schema_version='fork-workflow/1',title='Seeded physical sweep',horizon=30,resources=resources,tasks=tasks,stock={'part':r.randint(0,20)},budget_cents=r.choice([None,0,30,100,500]),events=outages)
        for policy in ['throughput','resilience','priority']:
            baseline=simulate(model,policy,events=[])
            control=simulate(model,policy,False,events=[])
            for key in ['segments','completions','metrics']:
                assert baseline[key]==control[key], (seed,policy,key,model,baseline,control)
            for adapt in [True,False]:
                result=simulate(model,policy,adapt)
                receipt=verify(model,result)
                assert receipt['valid'], (seed,policy,adapt,receipt['violations'])
