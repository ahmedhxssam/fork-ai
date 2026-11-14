"""Natural authoring provenance must be replayable before simulation launches."""
import copy
import hashlib
import json

import pytest
from fastapi.testclient import TestClient


BRIEF = ('We are running a repair clinic for 120 minutes. We have two mechanics. '
         'We need to finish six bike repairs, each taking 30 minutes. '
         'Either mechanic can do any repair, one repair at a time. '
         'All repairs are equally important and should finish before we close. '
         'For now, compare only work time and staffing.')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


@pytest.fixture
def client(tmp_path):
    from backend.main import create_app
    with TestClient(create_app(tmp_path/'conversation.sqlite')) as client:
        yield client


def resolve(client, brief=BRIEF):
    answers=[]
    for _ in range(25):
        response=client.post('/api/studio/intake',json={'brief':brief,'answers':answers})
        assert response.status_code==200,response.text
        result=response.json()
        assert not [issue for issue in result['issues'] if issue['severity']=='error'],result
        if result['ready']:
            return result,answers
        assert len(result['questions'])==1,result
        q=result['questions'][0]
        assert q['choices'], 'Fully specified fixture should only require choice-based review: '+str(q)
        choices=q['choices']
        approved=next((c for c in choices if c['value'] in ('confirm','accept','yes','time_capacity','simplify','agree')),choices[0])
        answers.append({'question_id':q['id'],'answer':approved['value']})
    pytest.fail('Conversation did not reach a reviewable model')


def test_natural_prompts_and_intake_are_available_without_provider(client):
    response=client.get('/api/studio/prompts')
    assert response.status_code==200
    body=response.json()
    assert body['provider_enabled'] is False and body['mode']=='deterministic'
    assert len(body['prompts'])>=3
    assert all('Resource ' not in p['brief'] and 'Task ' not in p['brief'] and 'Title:' not in p['brief'] for p in body['prompts'])
    result=client.post('/api/studio/intake',json={'brief':'I run a small repair clinic and need help planning.','answers':[]})
    assert result.status_code==200
    data=result.json()
    assert not data['ready'] and len(data['questions'])==1 and data['model_hash'] is None


def test_conversation_launch_replays_answers_and_persists_provenance(client):
    result,answers=resolve(client)
    model=result['model']
    assert len(model['tasks'])==6 and all(t['duration']==30 for t in model['tasks'])
    assert sum(r['capacity'] for r in model['resources'])==2
    body={'brief':BRIEF,'model':model,'model_hash':result['model_hash'],
          'authoring':{'method':'conversation','answers':answers,'brief_hash':result['brief_hash']}}
    response=client.post('/api/studio/experiments',json=body,headers={'Idempotency-Key':'natural-1'})
    assert response.status_code==200,response.text
    exp=response.json()
    assert exp['brief']==exp['display_brief']==BRIEF
    assert exp['authoring']['answers']==answers
    assert exp['authoring']['model_hash']==result['model_hash']
    assert all(w['verification']['valid'] for w in exp['worlds'])
    assert all(w['metrics']['completed']==6 for w in exp['worlds'])
    base='/api/studio/experiments/'+exp['id']
    assert client.get(base).json()==exp
    r=client.post(base+'/preferences',json={'revision':1,'weights':{'completion':1,'priority':0,'cost':0}})
    assert r.status_code==200 and r.json()['authoring']==exp['authoring']
    selected=r.json()['worlds'][0]['id']
    assert client.post(base+'/approve',json={'revision':2,'world_id':selected}).status_code==200
    exported=client.get(base+'/export').json()
    assert exported['authoring']['answers']==answers
    assert exported['approved']['model_hash']==result['model_hash']


def test_conversation_launch_rejects_unanswered_stale_and_tampered_model(client):
    result,answers=resolve(client)
    payload={'brief':BRIEF,'model':result['model'],'model_hash':result['model_hash'],
        'authoring':{'method':'conversation','answers':answers,'brief_hash':result['brief_hash']}}
    tampered=copy.deepcopy(payload)
    tampered['model']['resources'][0]['capacity']=3
    tampered['model_hash']=digest(tampered['model'])
    assert client.post('/api/studio/experiments',json=tampered).status_code==409
    stale=copy.deepcopy(payload);stale['brief']='We have only one mechanic now. '+BRIEF
    assert client.post('/api/studio/experiments',json=stale).status_code==409
    missing=copy.deepcopy(payload);missing['brief']='I need help with some repairs.'
    missing['authoring']['answers']=[]
    first=client.post('/api/studio/intake',json={'brief':missing['brief'],'answers':[]}).json()
    missing['authoring']['brief_hash']=first['brief_hash']
    assert client.post('/api/studio/experiments',json=missing).status_code==409


def test_intake_bounds_and_stale_question_ids_fail_without_model(client):
    assert client.post('/api/studio/intake',json={'brief':'   ','answers':[]}).status_code==422
    assert client.post('/api/studio/intake',json={'brief':BRIEF,'answers':[{'question_id':'fake','answer':'x'*2001}]}).status_code==422
    data=client.post('/api/studio/intake',json={'brief':BRIEF,'answers':[{'question_id':'wrong','answer':'yes'}]}).json()
    assert not data['ready'] and data['model_hash'] is None
    assert data['issues']


def test_applied_outages_preserve_conversation_and_export_replay(client):
    result,answers=resolve(client)
    payload={'brief':BRIEF,'model':result['model'],'model_hash':result['model_hash'],
             'authoring':{'method':'conversation','answers':answers,'brief_hash':result['brief_hash']}}
    exp=client.post('/api/studio/experiments',json=payload).json()
    base='/api/studio/experiments/'+exp['id']
    event={'id':'one-away','kind':'resource_outage','resource_id':exp['model']['resources'][0]['id'],
           'at':20,'duration':40,'capacity_lost':1,'label':'One person unavailable'}
    rerun=client.post(base+'/events',json={'revision':1,'events':[event]})
    assert rerun.status_code==200,rerun.text
    revised=rerun.json()
    assert revised['authoring']==exp['authoring']
    assert revised['model_hash']!=revised['authoring']['model_hash']
    approved=client.post(base+'/approve',json={'revision':2,'world_id':'throughput'})
    assert approved.status_code==200,approved.text
    assert client.get(base+'/export').status_code==200
    corrupted=approved.json()
    corrupted['authoring']['answers'][-1]['answer']='I did not agree to that scope'
    client.app.state.store.save(corrupted)
    assert client.get(base+'/export').status_code==409


def test_legacy_source_is_preserved_but_display_is_readable(client):
    from test_studio_api import model_fixture
    model=model_fixture();source='Resource bench capacity=2 skills=repair\nTask job duration=20 skill=repair'
    exp=client.post('/api/studio/experiments',json={'brief':source,'model':model,'model_hash':digest(model)}).json()
    assert exp['brief']==source
    assert '3 jobs' in exp['display_brief'] and 'Resource bench capacity' not in exp['display_brief']
    assert client.get('/api/studio/experiments/'+exp['id']).json()['brief']==source


def test_malformed_saved_authoring_is_rejected_without_server_error(client):
    result,answers=resolve(client)
    exp=client.post('/api/studio/experiments',json={'brief':BRIEF,'model':result['model'],'model_hash':result['model_hash'],
        'authoring':{'method':'conversation','answers':answers,'brief_hash':result['brief_hash']}}).json()
    exp['authoring'].pop('answers')
    client.app.state.store.save(exp)
    assert client.post('/api/studio/experiments/'+exp['id']+'/approve',json={'revision':1,'world_id':'throughput'}).status_code==409
