"""Versioned workflow experiments; compiled data never becomes executable code."""
import copy
import csv
import hashlib
import io
import json
import math
import time
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

POLICIES = ('throughput', 'resilience', 'priority')
DEFAULT_WEIGHTS = {'completion': .5, 'priority': .35, 'cost': .15}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class Body(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class CompileRequest(Body):
    brief: str = Field(min_length=1, max_length=30000)

    @field_validator('brief')
    @classmethod
    def meaningful_brief(cls, value):
        if not value.strip():
            raise ValueError('Describe a scenario or choose an example before compiling.')
        return value


class DialogueAnswer(Body):
    question_id: str = Field(min_length=1, max_length=512)
    answer: str = Field(min_length=1, max_length=2000)


class IntakeRequest(CompileRequest):
    answers: list[DialogueAnswer] = Field(default_factory=list, max_length=100)


class Authoring(Body):
    method: Literal['conversation']
    answers: list[DialogueAnswer] = Field(default_factory=list, max_length=100)
    brief_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


class SavedAuthoring(Authoring):
    model_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


class LaunchRequest(CompileRequest):
    model: dict
    model_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    authoring: Authoring | None = None


class RevisionRequest(Body):
    revision: StrictInt = Field(ge=1)


class EventsRequest(RevisionRequest):
    events: list[dict] = Field(max_length=12)


class Weights(Body):
    completion: float = Field(ge=0, le=1)
    priority: float = Field(ge=0, le=1)
    cost: float = Field(ge=0, le=1)

    @model_validator(mode='after')
    def nonzero(self):
        if self.completion + self.priority + self.cost <= 0:
            raise ValueError('Choose at least one positive preference.')
        return self


class PreferencesRequest(RevisionRequest):
    weights: Weights


class ApproveRequest(RevisionRequest):
    world_id: Literal['throughput', 'resilience', 'priority']


def comparison(worlds, model, weights=None):
    """Fixed model-derived normalization; only independently valid evidence competes."""
    values = dict(weights or DEFAULT_WEIGHTS)
    total = sum(values.values())
    normalized = {key: value / total for key, value in values.items()}
    cost_bound = sum(r['capacity'] * r['cost_per_minute'] * model['horizon'] for r in model['resources'])
    if model['budget_cents'] is not None:
        cost_bound = model['budget_cents']
    cost_bound = max(1, cost_bound)
    ranking = []
    for world in worlds:
        m = world['verification']['metrics']
        score = (normalized['completion'] * m['on_time'] / max(1, m['total'])
                 + normalized['priority'] * m['priority_on_time'] / max(1, m['priority_total'])
                 - normalized['cost'] * m['cost_cents'] / cost_bound)
        valid = bool(world['verification']['valid']) and math.isfinite(score)
        ranking.append({'world_id':world['id'], 'score':round(score, 9) if valid else None, 'eligible':valid})
    ranking.sort(key=lambda row:(not row['eligible'], -(row['score'] or 0), POLICIES.index(row['world_id'])))
    eligible = [row for row in ranking if row['eligible']]
    tied = [row['world_id'] for row in eligible if abs(row['score'] - eligible[0]['score']) <= 1e-9] if eligible else []
    return {'recommended_id':tied[0] if len(tied) == 1 else None,
            'tied_ids':tied if len(tied) > 1 else [], 'ranking':ranking, 'weights':normalized}


def compute(model, policy, adapt=True, events=None):
    from backend.studio.engine import simulate
    from backend.studio.referee import verify
    started = time.perf_counter()
    own = copy.deepcopy(model)
    result = simulate(own, policy, adapt=adapt, events=copy.deepcopy(events))
    receipt = verify(own, result, events=copy.deepcopy(events))
    result['verification'] = receipt
    result['metrics'] = copy.deepcopy(receipt['metrics'])
    result['compute_seconds'] = round(time.perf_counter() - started, 5)
    return result


def compute_experiment(model):
    baseline = [compute(model, policy, events=[]) for policy in POLICIES]
    if not model['events']:
        worlds = copy.deepcopy(baseline)
        controls = [compute(model, policy, adapt=False) for policy in POLICIES]
    else:
        worlds = [compute(model, policy) for policy in POLICIES]
        controls = [compute(model, policy, adapt=False) for policy in POLICIES]
    return worlds, baseline, controls


def install_studio_routes(application, store, mutation_lock):
    def present(exp):
        if 'display_brief' not in exp:
            if exp.get('authoring'):
                exp['display_brief'] = exp['brief']
            else:
                from backend.studio.intake import describe_model
                exp['display_brief'] = describe_model(exp['model'])
        return exp

    def validate(raw):
        from backend.studio.schema import validate_model
        try:
            return validate_model(raw)
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, 'Model needs correction: ' + str(exc)) from exc

    def get(experiment_id):
        exp = store.get(experiment_id)
        if exp is None or exp.get('kind') != 'workflow':
            raise HTTPException(404, 'Workflow experiment not found. Your draft can still be compiled again.')
        return present(exp)

    def cached(scope, key, payload):
        if not key:
            return None
        if len(key) > 160:
            raise HTTPException(422, 'Idempotency key is too long.')
        try:
            return store.command('studio:'+scope, key, digest(payload))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    def persist(exp, scope, key, payload):
        present(exp)
        command = ('studio:'+scope, key, digest(payload), exp) if key else None
        store.save(exp, command=command)
        return exp

    def require_revision(exp, revision):
        if exp['revision'] != revision:
            raise HTTPException(409, 'This experiment changed. Reload the latest revision before trying again.')

    def fresh_evidence(exp, world_id):
        from backend.studio.referee import verify
        if exp.get('authoring'):
            from backend.studio.intake import intake
            try:
                source = SavedAuthoring.model_validate(exp['authoring']).model_dump()
                parsed = intake(exp['brief'], source['answers'])
            except (ValueError, KeyError, TypeError) as exc:
                raise HTTPException(409, 'The saved conversation needs review before approval or export.') from exc
            if (not parsed['ready'] or parsed['brief_hash'] != source['brief_hash']
                    or parsed['model_hash'] != source['model_hash']
                    or digest(dict(parsed['model'], events=exp['model']['events'])) != exp['model_hash']):
                raise HTTPException(409, 'The conversation no longer matches this model. Review the scenario again.')
        selected = next((w for w in exp['worlds'] if w['id'] == world_id), None)
        if selected is None:
            raise HTTPException(409, 'This future is not part of the current experiment.')
        model = validate(exp['model'])
        if digest(model) != exp['model_hash'] or selected['model_hash'] != exp['model_hash']:
            raise HTTPException(409, 'The model changed. Run and review a fresh experiment.')
        receipt = verify(model, selected)
        previous = selected.get('verification', {})
        if not receipt['valid'] or digest(receipt) != digest(previous):
            raise HTTPException(409, 'The independent evidence check failed. Run a fresh experiment before approval or export.')
        return selected, receipt

    @application.get('/api/studio/templates')
    def templates():
        from backend.studio.compiler import GRAMMAR, TEMPLATES
        return {'templates':copy.deepcopy(TEMPLATES), 'grammar':GRAMMAR, 'capabilities':{
            'mode':'deterministic', 'compiler':'deterministic-v1', 'provider_enabled':False,
            'schema_version':'fork-workflow/1', 'time_unit':'minutes', 'max_horizon':720,
            'supported':['resource pools','skills','checkpointable jobs','dependencies','deadlines','stock','work budget','resource outages'],
            'unsupported':['travel and routing','stochastic arrivals','physical dynamics','unbounded natural language'],
            'assumption':'Jobs checkpoint on interruption; cost covers worked resource-unit minutes only.',
            'future_ai':'A future model may propose this same typed schema; the simulator and referee retain authority.'}}

    @application.get('/api/studio/schema')
    def schema():
        from backend.studio.schema import model_schema
        return {'schema':model_schema(), 'mode':'deterministic', 'provider_enabled':False}

    @application.get('/api/studio/prompts')
    def prompts():
        from backend.studio.intake import PROMPTS
        return {'prompts':copy.deepcopy(PROMPTS), 'mode':'deterministic', 'provider_enabled':False}

    @application.post('/api/studio/intake')
    def understand(body: IntakeRequest):
        from backend.studio.intake import intake
        return intake(body.brief, [answer.model_dump() for answer in body.answers])

    @application.post('/api/studio/compile')
    def compile_scenario(body: CompileRequest):
        from backend.studio.compiler import compile_brief
        return compile_brief(body.brief)

    @application.post('/api/studio/experiments')
    def launch(body: LaunchRequest, idempotency_key: str | None = Header(None)):
        payload = body.model_dump()
        if body.authoring is None:
            payload.pop('authoring')
        with mutation_lock:
            previous = cached('launch', idempotency_key, payload)
            if previous:
                return previous
            model = validate(body.model)
            if digest(model) != body.model_hash:
                raise HTTPException(409, 'The reviewed model does not match its fingerprint. Compile and review it again.')
            authoring = None
            if body.authoring is not None:
                from backend.studio.intake import intake
                authoring = body.authoring.model_dump()
                parsed = intake(body.brief, authoring['answers'])
                if (not parsed['ready'] or parsed['brief_hash'] != authoring['brief_hash']
                        or parsed['model_hash'] != body.model_hash or digest(parsed['model']) != digest(model)):
                    raise HTTPException(409, 'Answer the current follow-up questions and review the resulting model before running.')
                authoring['model_hash'] = parsed['model_hash']
            worlds, baseline, controls = compute_experiment(model)
            exp = {'id':'wf-'+uuid.uuid4().hex[:16], 'kind':'workflow', 'revision':1,
                   'mode':'deterministic', 'brief':body.brief, 'model':model, 'model_hash':digest(model),
                   'worlds':worlds, 'baseline_worlds':baseline, 'controls':controls,
                   'comparison':comparison(worlds, model), 'approved':None, 'created_at':now()}
            if authoring is not None:
                exp['authoring'] = authoring
            return persist(exp, 'launch', idempotency_key, payload)

    @application.get('/api/studio/experiments/{experiment_id}')
    def resume(experiment_id: str):
        return get(experiment_id)

    @application.post('/api/studio/experiments/{experiment_id}/events')
    def events(experiment_id: str, body: EventsRequest, idempotency_key: str | None = Header(None)):
        payload = body.model_dump()
        scope = experiment_id+':events'
        with mutation_lock:
            previous = cached(scope, idempotency_key, payload)
            if previous:
                return previous
            exp = get(experiment_id)
            require_revision(exp, body.revision)
            model = validate(dict(exp['model'], events=body.events))
            worlds, baseline, controls = compute_experiment(model)
            exp.update(model=model, model_hash=digest(model), worlds=worlds,
                       baseline_worlds=baseline, controls=controls,
                       comparison=comparison(worlds, model, exp['comparison']['weights']),
                       revision=exp['revision']+1, approved=None)
            return persist(exp, scope, idempotency_key, payload)

    @application.post('/api/studio/experiments/{experiment_id}/preferences')
    def preferences(experiment_id: str, body: PreferencesRequest, idempotency_key: str | None = Header(None)):
        payload = body.model_dump()
        scope = experiment_id+':preferences'
        with mutation_lock:
            previous = cached(scope, idempotency_key, payload)
            if previous:
                return previous
            exp = get(experiment_id)
            require_revision(exp, body.revision)
            exp.update(comparison=comparison(exp['worlds'], exp['model'], body.weights.model_dump()),
                       revision=exp['revision']+1, approved=None)
            return persist(exp, scope, idempotency_key, payload)

    @application.post('/api/studio/experiments/{experiment_id}/approve')
    def approve(experiment_id: str, body: ApproveRequest, idempotency_key: str | None = Header(None)):
        payload = body.model_dump()
        scope = experiment_id+':approve'
        with mutation_lock:
            previous = cached(scope, idempotency_key, payload)
            if previous:
                return previous
            exp = get(experiment_id)
            require_revision(exp, body.revision)
            _, receipt = fresh_evidence(exp, body.world_id)
            exp['approved'] = {'world_id':body.world_id, 'revision':exp['revision'],
                'evidence_hash':receipt['evidence_hash'], 'model_hash':exp['model_hash'],
                'weights_hash':digest(exp['comparison']['weights']), 'approved_at':now()}
            return persist(exp, scope, idempotency_key, payload)

    @application.get('/api/studio/experiments/{experiment_id}/export')
    def export(experiment_id: str, format: Literal['json','csv'] = Query('json')):
        with mutation_lock:
            exp = get(experiment_id)
            decision = exp.get('approved')
            if not decision or decision['revision'] != exp['revision'] or decision['model_hash'] != exp['model_hash']:
                raise HTTPException(409, 'Review and approve a future in this revision before exporting.')
            if decision.get('weights_hash') != digest(exp['comparison']['weights']):
                raise HTTPException(409, 'Preferences changed. Review and approve this revision again.')
            selected, receipt = fresh_evidence(exp, decision['world_id'])
            if receipt['evidence_hash'] != decision['evidence_hash']:
                raise HTTPException(409, 'Approved evidence no longer matches. Run and review a fresh experiment.')
            filename = f"fork-workflow-{exp['id']}-r{exp['revision']}.{format}"
            if format == 'json':
                content = json.dumps(exp, indent=2, allow_nan=False)
                media = 'application/json'
            else:
                output = io.StringIO(newline='')
                writer = csv.DictWriter(output, fieldnames=['task_id','resource_id','start','end','units'])
                writer.writeheader()
                for segment in selected['segments']:
                    writer.writerow({key:segment[key] for key in writer.fieldnames})
                content, media = output.getvalue(), 'text/csv'
            return Response(content, media_type=media, headers={'Content-Disposition':f'attachment; filename="{filename}"'})
