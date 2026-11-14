"""Independent finite Scenario Studio review sweep; no optimality claim.

Run: PYTHONPATH=. .venv/bin/python scripts/studio_backend_review_sweep.py
"""
import random, copy, json
from backend.studio.engine import simulate
from backend.studio.referee import verify
rng=random.Random(991827)
checks=0
for case in range(1000):
 h=rng.randint(8,40)
 resources=[dict(id=f'r{i}',label=f'R {i}',capacity=rng.randint(1,5),skills=rng.sample(['a','b','c'],rng.randint(1,3)),cost_per_minute=rng.randint(0,8)) for i in range(rng.randint(1,4))]
 tasks=[]
 for i in range(rng.randint(1,15)):
  pool=rng.choice(resources); release=rng.randrange(h+1)
  tasks.append(dict(id=f't{i}',label=f'T {i}',duration=rng.randint(1,h),skill=rng.choice(pool['skills']),units=rng.randint(1,pool['capacity']),release=release,due=rng.randint(release,h),priority=rng.randint(1,3),value=rng.randint(1,50),depends_on=[f't{j}' for j in range(i) if rng.random()<.12],materials={s:rng.randint(1,4) for s in ['x','y'] if rng.random()<.3}))
 events=[]
 for i in range(rng.randint(0,7)):
  pool=rng.choice(resources)
  events.append(dict(id=f'e{i}',kind='resource_outage',resource_id=pool['id'],at=rng.randrange(h),duration=rng.randint(1,h+3),capacity_lost=rng.randint(1,pool['capacity']),label=f'E {i}'))
 model=dict(schema_version='fork-workflow/1',title='Review sweep',horizon=h,resources=resources,tasks=tasks,stock={'x':rng.randint(0,20),'y':rng.randint(0,20)},budget_cents=rng.choice([None,0,1,3,27,70,300]),events=events)
 for policy in ('throughput','resilience','priority'):
  nominal=simulate(model,policy,events=[])
  fixed=simulate(model,policy,adapt=False,events=[])
  for key in ('segments','completions','metrics'): assert nominal[key]==fixed[key], (case,policy,'nominal-control',key)
  actual=simulate(model,policy)
  cutoff=min([e['at'] for e in events],default=h)
  def prefix(result):
   return sorted((s['task_id'],s['resource_id'],s['start'],min(s['end'],cutoff),s['units']) for s in result['segments'] if s['start']<cutoff)
  assert prefix(nominal)==prefix(actual),(case,policy,'future peek')
  reverse=simulate(model,policy,events=list(reversed(events)))
  for key in ('segments','completions','metrics'): assert actual[key]==reverse[key],(case,policy,'event order')
  for adapt in (True,False):
   result=actual if adapt else simulate(model,policy,adapt=False)
   receipt=verify(model,result)
   assert receipt['valid'],(case,policy,adapt,receipt['violations'],model,result)
   cost=0; stock={s:0 for s in model['stock']}; taskmap={t['id']:t for t in tasks}; completions={c['task_id']:c['time'] for c in result['completions']}
   for pool in resources:
    for minute in range(h):
     usage=sum(s['units'] for s in result['segments'] if s['resource_id']==pool['id'] and s['start']<=minute<s['end'])
     loss=sum(e['capacity_lost'] for e in events if e['resource_id']==pool['id'] and e['at']<=minute<e['at']+e['duration'])
     assert usage<=max(0,pool['capacity']-loss)
     cost+=usage*pool['cost_per_minute']
   for tid,t in taskmap.items():
    segs=[s for s in result['segments'] if s['task_id']==tid]
    if segs:
     start=min(s['start'] for s in segs)
     assert start>=t['release']
     assert all(d in completions and completions[d]<=start for d in t['depends_on'])
     assert len({s['resource_id'] for s in segs})==1
     for material,q in t['materials'].items():stock[material]+=q
    work=sum(s['end']-s['start'] for s in segs)
    assert work<=t['duration']
    assert (tid in completions)==(work==t['duration'])
   assert cost==result['metrics']['cost_cents']
   assert model['budget_cents'] is None or cost<=model['budget_cents']
   assert all(q<=model['stock'][s] for s,q in stock.items())
   checks+=1
print(json.dumps({'cases':1000,'policies':3,'physical_runs':checks,'nominal_control_pairs':3000,'no_future_peek_pairs':3000,'outage_order_pairs':3000,'seed':991827,'passed':True}))
