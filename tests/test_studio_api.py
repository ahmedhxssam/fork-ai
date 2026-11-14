"""Workflow API tests exercise real compiler, scheduler, referee and durable snapshots."""
import copy
import csv
import hashlib
import io
import json

import pytest
from fastapi.testclient import TestClient


def hashed(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def model_fixture():
    return {'schema_version':'fork-workflow/1','title':'Repair bench','horizon':60,
        'resources':[{'id':'bench','label':'Repair team','capacity':2,'skills':['repair'],'cost_per_minute':10}],
        'tasks':[{'id':f'job-{i}','label':f'Repair {i}','duration':20,'skill':'repair','units':1,
            'release':0,'due':30 if i==3 else 60,'priority':3 if i==3 else 1,'value':10,
            'depends_on':[],'materials':{'parts':1}} for i in range(1,4)],
        'stock':{'parts':3},'budget_cents':1200,'events':[]}


@pytest.fixture
def client(tmp_path):
    from backend.main import create_app
    with TestClient(create_app(tmp_path / 'studio.sqlite')) as client:
        yield client


def launch(client, model=None, key=None):
    model = model or model_fixture()
    response = client.post('/api/studio/experiments', json={'brief':'Repair bench scenario','model':model,'model_hash':hashed(model)},
        headers={'Idempotency-Key':key} if key else {})
    assert response.status_code == 200, response.text
    return response.json()


def test_studio_templates_are_compilable_across_distinct_domains(client):
    response = client.get('/api/studio/templates')
    assert response.status_code == 200
    templates = response.json()['templates']
    assert len(templates) >= 3
    signatures = set()
    for template in templates:
        result = client.post('/api/studio/compile',json={'brief':template['brief']}).json()
        assert result['ready'], result
        assert result['compiler'] == 'deterministic-v1'
        assert result['model_hash'] == hashed(result['model'])
        signatures.add(tuple(sorted(r['skills'][0] for r in result['model']['resources'])))
    assert len(signatures) >= 3
    assert client.get('/api/studio/schema').json()['provider_enabled'] is False


def test_full_studio_revision_approval_and_export_lifecycle(client):
    exp = launch(client, key='studio-create')
    repeated = launch(client, key='studio-create')
    assert repeated['id'] == exp['id']
    assert exp['kind'] == 'workflow' and exp['mode'] == 'deterministic'
    assert len(exp['worlds']) == len(exp['baseline_worlds']) == len(exp['controls']) == 3
    assert {w['policy'] for w in exp['worlds']} == {'throughput','resilience','priority'}
    assert all(w['verification']['valid'] for w in exp['worlds'] + exp['baseline_worlds'] + exp['controls'])
    assert all(w['model_hash'] == exp['model_hash'] for w in exp['worlds'])
    base = '/api/studio/experiments/'+exp['id']
    assert client.get(base+'/export').status_code == 409
    selected = exp['comparison']['ranking'][0]['world_id']
    exp = client.post(base+'/approve',json={'revision':1,'world_id':selected}).json()
    assert exp['approved']['model_hash'] == exp['model_hash']
    exported = client.get(base+'/export?format=json')
    assert exported.status_code == 200 and exported.json()['approved']['revision'] == 1
    rows = list(csv.DictReader(io.StringIO(client.get(base+'/export?format=csv').text)))
    assert rows and set(rows[0]) == {'task_id','resource_id','start','end','units'}
    event = {'id':'outage-1','kind':'resource_outage','resource_id':'bench','at':10,'duration':30,'capacity_lost':2,'label':'Power loss'}
    exp = client.post(base+'/events',json={'revision':1,'events':[event]}).json()
    assert exp['revision'] == 2 and exp['approved'] is None
    assert exp['model_hash'] != repeated['model_hash']
    assert all(w['verification']['valid'] for w in exp['worlds'] + exp['controls'])
    assert any(w['metrics']['on_time'] < b['metrics']['on_time'] for w,b in zip(exp['worlds'],exp['baseline_worlds']))
    assert client.get(base+'/export').status_code == 409
    assert client.post(base+'/approve',json={'revision':1,'world_id':selected}).status_code == 409
    assert client.post(base+'/events',json={'revision':1,'events':[]}).status_code == 409
    response = client.post(base+'/preferences',json={'revision':2,'weights':{'completion':0,'priority':1,'cost':0}})
    assert response.status_code == 200
    exp = response.json()
    assert exp['revision'] == 3 and exp['comparison']['weights']['priority'] == 1
    assert client.get(base).json() == exp


def test_studio_rejects_bad_models_hashes_events_and_preferences(client):
    model = model_fixture()
    body = {'brief':'Repair','model':model,'model_hash':'0'*64}
    assert client.post('/api/studio/experiments',json=body).status_code == 409
    model['tasks'][0]['depends_on'] = ['missing']
    body['model_hash'] = hashed(model)
    assert client.post('/api/studio/experiments',json=body).status_code == 422
    exp = launch(client)
    base = '/api/studio/experiments/'+exp['id']
    assert client.post(base+'/preferences',json={'revision':1,'weights':{'completion':0,'priority':0,'cost':0}}).status_code == 422
    event = {'id':'oops','kind':'resource_outage','resource_id':'absent','at':10,'duration':5,'capacity_lost':1,'label':'missing'}
    assert client.post(base+'/events',json={'revision':1,'events':[event]}).status_code == 422
    assert client.get(base).json()['revision'] == 1
    assert client.post('/api/studio/compile',json={'brief':'x'*30001}).status_code == 422


def test_studio_preserves_ties_and_excludes_invalid_receipts(client):
    model = model_fixture()
    model['tasks'] = model['tasks'][:1]
    exp = launch(client, model)
    assert exp['comparison']['recommended_id'] is None
    assert set(exp['comparison']['tied_ids']) == {'throughput','resilience','priority'}
    invalid = copy.deepcopy(exp)
    invalid['worlds'][0]['segments'][0]['end'] += 1
    client.app.state.store.save(invalid)
    base = '/api/studio/experiments/'+exp['id']
    assert client.post(base+'/approve',json={'revision':1,'world_id':'throughput'}).status_code == 409


def test_studio_and_logistics_ids_are_not_interchangeable(client):
    exp = launch(client)
    assert client.get('/api/experiments/'+exp['id']).status_code == 404
    assert client.post('/api/experiments/'+exp['id']+'/disrupt',json={'vehicle_id':'A','time':60}).status_code == 404
    assert client.get('/api/studio/experiments/missing').status_code == 404


def test_studio_export_rechecks_approved_evidence(client):
    exp = launch(client)
    base = '/api/studio/experiments/'+exp['id']
    result = client.post(base+'/approve',json={'revision':1,'world_id':'throughput'})
    assert result.status_code == 200
    tampered = result.json()
    tampered['worlds'][0]['metrics']['completed'] += 1
    client.app.state.store.save(tampered)
    assert client.get(base+'/export').status_code == 409


def test_studio_idempotent_mutation_replays_lost_success(client):
    exp = launch(client)
    base = '/api/studio/experiments/'+exp['id']
    body = {'revision':1,'weights':{'completion':1,'priority':0,'cost':0}}
    response = client.post(base+'/preferences',json=body,headers={'Idempotency-Key':'preference-1'})
    assert response.status_code == 200
    repeat = client.post(base+'/preferences',json=body,headers={'Idempotency-Key':'preference-1'})
    assert repeat.status_code == 200 and repeat.json() == response.json()
    body['weights'] = {'completion':0,'priority':1,'cost':0}
    assert client.post(base+'/preferences',json=body,headers={'Idempotency-Key':'preference-1'}).status_code == 409


def test_studio_requires_a_meaningful_brief_even_for_manual_model(client):
    model = model_fixture()
    response = client.post('/api/studio/experiments',json={'brief':' \n\t ','model':model,'model_hash':hashed(model)})
    assert response.status_code == 422
    assert client.post('/api/studio/compile',json={'brief':'   '}).status_code == 422


@pytest.mark.parametrize('field', ['metrics','checks'])
def test_studio_approval_rejects_tampered_displayed_referee_receipt(client, field):
    exp = launch(client)
    receipt = exp['worlds'][0]['verification']
    if field == 'metrics':
        receipt['metrics']['completed'] = 999
    else:
        receipt['checks'][0]['detail'] = 'Unverified replacement claim'
    client.app.state.store.save(exp)
    base = '/api/studio/experiments/'+exp['id']
    assert client.post(base+'/approve',json={'revision':1,'world_id':'throughput'}).status_code == 409


def test_studio_export_rejects_tampered_displayed_referee_receipt(client):
    exp = launch(client)
    base = '/api/studio/experiments/'+exp['id']
    approved = client.post(base+'/approve',json={'revision':1,'world_id':'throughput'}).json()
    approved['worlds'][0]['verification']['metrics']['completed'] = 999
    client.app.state.store.save(approved)
    assert client.get(base+'/export').status_code == 409


@pytest.mark.parametrize('field',['metric_bool','passed_integer'])
def test_studio_receipt_integrity_is_type_sensitive(client, field):
    model = model_fixture()
    model['tasks'] = model['tasks'][:1]
    exp = launch(client, model)
    receipt = exp['worlds'][0]['verification']
    if field == 'metric_bool':
        assert receipt['metrics']['completed'] == 1
        receipt['metrics']['completed'] = True
    else:
        receipt['checks'][0]['passed'] = 1
    client.app.state.store.save(exp)
    assert client.post('/api/studio/experiments/'+exp['id']+'/approve',json={'revision':1,'world_id':'throughput'}).status_code == 409


def test_studio_cost_preference_uses_declared_budget_denominator(client):
    model = model_fixture()
    model.update(horizon=5,budget_cents=1000,stock={'parts':1})
    model['resources'][0].update(capacity=1,cost_per_minute=1)
    short = copy.deepcopy(model['tasks'][0])
    short.update(id='short',duration=2,due=5,priority=1)
    important = copy.deepcopy(short)
    important.update(id='important',duration=5,priority=3)
    model['tasks'] = [short,important]
    exp = launch(client,model)
    response = client.post('/api/studio/experiments/'+exp['id']+'/preferences',json={'revision':1,'weights':{'completion':0,'priority':.15,'cost':.85}})
    assert response.status_code == 200
    comparison = response.json()['comparison']
    scores = {row['world_id']:row['score'] for row in comparison['ranking']}
    assert scores['throughput'] == pytest.approx(-.0017)
    assert scores['priority'] == pytest.approx(.14575)
    assert set(comparison['tied_ids']) == {'resilience','priority'}
