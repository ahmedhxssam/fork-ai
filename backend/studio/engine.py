"""Bounded deterministic list-scheduling heuristics, never optimality claims.

Throughput: shortest remaining processing time, then due time, then highest value.
Resilience: least deadline slack, then shortest remaining time; seeks time buffer,
not forecast robustness. Priority: highest declared priority, then earliest due.
All ties end with task ID. Resources prefer cheapest cost, then fewer skills,
then ID. No policy inspects future outages. Running healthy commitments precede
paused tasks; paused tasks precede new tasks. Capacity losses pause the latest
commitments first, preserving checkpointed work and the original pool.

The no-adaptation control computes a no-outage nominal schedule and fixes its
pool assignments, start-time lower bounds, per-pool start order and capacity-slot
predecessors. Each nominal unit slot stays committed through an outage delay. Outage pauses
and dependency delays may move starts later; blocked queue heads cannot be
bypassed. Jobs absent from the nominal schedule are not introduced by control.
"""
from __future__ import annotations

from .schema import model_hash, validate_model

POLICIES = {'throughput': 'Throughput', 'resilience': 'Resilience', 'priority': 'Priority'}
POLICY_DESCRIPTIONS = {
    'throughput': 'Shortest remaining work first; ties prefer earlier deadlines, then higher value.',
    'resilience': 'Least deadline slack first to protect time buffers; no outage forecast or robustness guarantee.',
    'priority': 'Highest declared priority first; ties prefer earlier deadlines, then shorter work.',
}


def simulate(model: dict, policy: str, adapt: bool = True, events: list | None = None) -> dict:
    if policy not in POLICIES:
        raise ValueError(f'Unknown policy {policy!r}; choose throughput, resilience or priority')
    if type(adapt) is not bool:
        raise ValueError('adapt must be boolean')
    model = validate_model(model)
    schedule = model['events'] if events is None else validate_model(model | {'events': events})['events']
    fixed = None
    if not adapt:
        nominal = _run(model, policy, [], None)
        fixed = {}
        slots = {r['id']: [(0, None)] * r['capacity'] for r in model['resources']}
        for segment in nominal['segments']:
            # Nominal uninterrupted work defines unit-slot predecessor commitments.
            # This prevents a delayed 2-unit job from being bypassed by a later
            # 1-unit job in the fixed control when an outage removes one unit.
            pool_slots = slots[segment['resource_id']]
            chosen = [i for i, (end, _) in enumerate(pool_slots) if end <= segment['start']][:segment['units']]
            predecessors = sorted({pool_slots[i][1] for i in chosen if pool_slots[i][1] is not None})
            fixed[segment['task_id']] = dict(resource_id=segment['resource_id'], start=segment['start'],
                order=len(fixed), predecessors=predecessors, work_limit=segment['end'] - segment['start'])
            for i in chosen:
                pool_slots[i] = (segment['end'], segment['task_id'])
    result = _run(model, policy, schedule, fixed)
    return dict(id=policy, name=POLICIES[policy], policy=policy,
                model_hash=model_hash(model), adapt=adapt, **result)


def _run(model, policy, outages, fixed):
    horizon = model['horizon']
    tasks = {task['id']: task for task in model['tasks']}
    resources = {r['id']: r for r in model['resources']}
    progress = {id: 0 for id in tasks}
    assigned, started, completed = {}, {}, {}
    stock = model['stock'].copy()
    budget = model['budget_cents']
    spent = 0
    segments, completions, ledger = [], [], []
    last_segment = {}
    prior_work = set()
    def event(time, kind, summary, task_id=None, resource_id=None):
        item = dict(time=time, kind=kind, summary=summary)
        if task_id is not None:
            item['task_id'] = task_id
        if resource_id is not None:
            item['resource_id'] = resource_id
        ledger.append(item)
    def rank(id, minute):
        task = tasks[id]
        remaining = task['duration'] - progress[id]
        if policy == 'throughput':
            return (remaining, task['due'], -task['value'], id)
        if policy == 'resilience':
            return (task['due'] - minute - remaining, remaining, -task['priority'], id)
        return (-task['priority'], task['due'], remaining, id)
    ordered_outages = sorted(outages, key=lambda e: (e['at'], e['id']))
    for minute in range(horizon):
        for outage in ordered_outages:
            if outage['at'] == minute:
                event(minute, 'resource_outage', f"{outage['label']}: {outage['capacity_lost']} capacity unavailable until minute {min(horizon, minute + outage['duration'])}.", resource_id=outage['resource_id'])
            if min(horizon, outage['at'] + outage['duration']) == minute:
                event(minute, 'resource_restored', f"{outage['label']}: outage interval ended; other overlapping outages still apply.", resource_id=outage['resource_id'])
        available = {}
        for id, resource in resources.items():
            losses = sum(e['capacity_lost'] for e in outages if e['resource_id'] == id and e['at'] <= minute < e['at'] + e['duration'])
            available[id] = max(0, resource['capacity'] - losses)
        worked = set()
        # Healthy running tasks retain commitments; capacity loss pauses latest starts.
        active = sorted((id for id in started if id not in completed and (fixed is None or progress[id] < fixed[id]['work_limit'])),
                        key=lambda id: (id not in prior_work, started[id], id))
        def can_work(id, resource_id):
            task, resource = tasks[id], resources[resource_id]
            cost = task['units'] * resource['cost_per_minute']
            return task['units'] <= available[resource_id] and (budget is None or spent + cost <= budget)
        def work(id, resource_id):
            nonlocal spent
            task, resource = tasks[id], resources[resource_id]
            if id not in started:
                started[id] = (minute, len(started))
                assigned[id] = resource_id
                for material, amount in task['materials'].items():
                    stock[material] -= amount
                event(minute, 'task_started', f"Started {task['label']} on {resource['label']}; materials consumed once.", id, resource_id)
            elif id not in prior_work:
                event(minute, 'task_resumed', f"Resumed checkpointed work for {task['label']} on its original pool.", id, resource_id)
            available[resource_id] -= task['units']
            spent += task['units'] * resource['cost_per_minute']
            progress[id] += 1
            worked.add(id)
            previous = last_segment.get(id)
            if previous is not None and previous['end'] == minute:
                previous['end'] = minute + 1
            else:
                segment = dict(task_id=id, resource_id=resource_id, start=minute, end=minute + 1, units=task['units'])
                segments.append(segment)
                last_segment[id] = segment
        for id in active:
            resource_id = assigned[id]
            if can_work(id, resource_id):
                work(id, resource_id)
            elif id in prior_work:
                event(minute, 'task_paused', f"Paused {tasks[id]['label']}: insufficient available capacity or remaining budget; completed work retained.", id, resource_id)
        if fixed is None:
            pending = sorted((id for id in tasks if id not in started), key=lambda id: rank(id, minute))
        else:
            pending = sorted((id for id in fixed if id not in started), key=lambda id: fixed[id]['order'])
        blocked_pools = set()
        for id in pending:
            task = tasks[id]
            if fixed is not None:
                pool = fixed[id]['resource_id']
                if pool in blocked_pools:
                    continue
                # Retain planned starts and per-pool order even if a head cannot start.
                eligible_time = minute >= fixed[id]['start'] and all(progress[p] >= fixed[p]['work_limit'] for p in fixed[id]['predecessors'])
            else:
                eligible_time = True
            eligible = eligible_time and task['release'] <= minute and all(d in completed for d in task['depends_on'])
            eligible = eligible and all(stock[s] >= n for s, n in task['materials'].items())
            if not eligible:
                if fixed is not None:
                    blocked_pools.add(pool)
                continue
            candidates = [resources[fixed[id]['resource_id']]] if fixed is not None else sorted(resources.values(), key=lambda r: (r['cost_per_minute'], len(r['skills']), r['id']))
            chosen = next((r['id'] for r in candidates if task['skill'] in r['skills'] and can_work(id, r['id'])), None)
            if chosen is not None:
                work(id, chosen)
            elif fixed is not None:
                blocked_pools.add(pool)
        # A minute's completions cannot enable another task until the next minute.
        for id in sorted(worked):
            if progress[id] == tasks[id]['duration']:
                completed[id] = minute + 1
                completions.append(dict(task_id=id, time=minute + 1))
                event(minute + 1, 'task_completed', f"Completed {tasks[id]['label']}.", id, assigned[id])
        prior_work = worked - completed.keys()
    for outage in ordered_outages:
        if min(horizon, outage['at'] + outage['duration']) == horizon:
            event(horizon, 'resource_restored', f"{outage['label']}: modeled outage interval ended at the horizon.", resource_id=outage['resource_id'])
    event(horizon, 'horizon', 'Planning horizon reached; unfinished work remains unserved.')
    metrics = dict(completed=len(completed), total=len(tasks),
                   on_time=sum(time <= tasks[id]['due'] for id, time in completed.items()),
                   priority_on_time=sum(tasks[id]['priority'] == 3 and time <= tasks[id]['due'] for id, time in completed.items()),
                   priority_total=sum(t['priority'] == 3 for t in tasks.values()),
                   value_completed=sum(tasks[id]['value'] for id in completed),
                   value_total=sum(t['value'] for t in tasks.values()), cost_cents=spent,
                   work_minutes=sum(progress.values()), unserved=len(tasks) - len(completed),
                   makespan=max((s['end'] for s in segments), default=0))
    return dict(segments=segments, completions=completions, events=ledger, metrics=metrics)
