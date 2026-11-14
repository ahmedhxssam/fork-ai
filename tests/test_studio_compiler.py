import copy

import pytest

from backend.studio.compiler import TEMPLATES, compile_brief
from backend.studio.schema import model_hash, model_schema, validate_model


def test_three_templates_compile_into_distinct_real_workflows():
    assert len(TEMPLATES) >= 3
    models = []
    for template in TEMPLATES:
        result = compile_brief(template['brief'])
        assert result['ready'], result['issues']
        assert result['compiler'] == 'deterministic-v1'
        assert result['model_hash'] == model_hash(result['model'])
        assert len(result['model']['tasks']) >= 5
        assert any(t['depends_on'] for t in result['model']['tasks'])
        assert result['facts']
        models.append(result['model'])
    assert len({m['title'] for m in models}) == len(models)
    assert len({tuple(r['skills'][0] for r in m['resources']) for m in models}) == len(models)


def test_documented_natural_sentences_and_visible_defaults():
    result = compile_brief('''Title: Help desk
Horizon: 40 minutes
Resource tech has capacity 1, skills support, and costs 3 cents per minute.
Task restore takes 8 minutes using skill support.
''')
    assert result['ready'], result['issues']
    task = result['model']['tasks'][0]
    assert (task['duration'], task['due'], task['release'], task['units']) == (8, 40, 0, 1)
    fields = {a['field'] for a in result['assumptions']}
    assert {'tasks.restore.due', 'tasks.restore.units', 'budget_cents'} <= fields


def test_explicit_grammar_preserves_constraints_and_traceability():
    result = compile_brief('''Title: Test
Horizon: 30
Budget: 90 cents
Stock: parts=2
Resource bench label="Repair bench" capacity=2 skills=repair cost=3
Task inspect duration=2 skill=repair units=1 release=0 due=10 priority=2 value=5 after=- materials=parts:1
Task fix duration=4 skill=repair units=2 release=1 due=20 priority=3 value=10 after=inspect materials=parts:1
Outage broken resource=bench at=3 duration=5 lost=1 label="Bench failure"
''')
    assert result['ready'], result['issues']
    model = result['model']
    assert model['tasks'][1]['depends_on'] == ['inspect']
    assert model['tasks'][1]['materials'] == {'parts': 1}
    assert model['resources'][0]['label'] == 'Repair bench'
    assert model['events'][0]['capacity_lost'] == 1
    assert all(f['line'] > 0 and f['targets'] for f in result['facts'])


@pytest.mark.parametrize('extra', [
    'Also every worker must take a lunch break.',
    'Task secret duration=1 skill=repair teleport=true',
    'Deadline: everything by noon',
    'Event rain at=3 duration=5',
    'Budget: unlimited but keep spending under 25',
])
def test_unknown_operative_lines_and_attributes_block(extra):
    result = compile_brief(TEMPLATES[0]['brief'] + '\n' + extra)
    assert not result['ready']
    assert result['model'] is None and result['model_hash'] is None
    assert any(i['severity'] == 'error' and i['line'] for i in result['issues'])


def test_empty_brief_blocks_and_comments_are_explicit():
    assert not compile_brief('')['ready']
    assert compile_brief(TEMPLATES[0]['brief'] + '\n# harmless comment')['ready']


@pytest.mark.parametrize('mutation', [
    lambda m: m['tasks'][0].update(duration=True),
    lambda m: m['tasks'][0].update(duration=0),
    lambda m: m['tasks'][0].update(release=-1),
    lambda m: m['tasks'][0].update(due=m['horizon'] + 1),
    lambda m: m['tasks'][0].update(depends_on=['missing']),
    lambda m: m['tasks'][0].update(depends_on=[m['tasks'][0]['id']]),
    lambda m: m['tasks'][0].update(skill='missing'),
    lambda m: m['tasks'][0].update(units=12),
    lambda m: m['tasks'][0].update(materials={'unknown': 1}),
    lambda m: m['tasks'][0].update(materials={'parts': 0}),
    lambda m: m['resources'].append(copy.deepcopy(m['resources'][0])),
    lambda m: m.update(surprise='ignored'),
    lambda m: m.update(horizon=721),
])
def test_schema_rejects_invalid_models(mutation):
    model = copy.deepcopy(compile_brief(TEMPLATES[0]['brief'])['model'])
    mutation(model)
    with pytest.raises(ValueError):
        validate_model(model)


def test_hash_is_canonical_schema_exposed_and_insufficient_constraints_valid():
    model = compile_brief(TEMPLATES[0]['brief'])['model']
    model['stock'] = {key: 0 for key in model['stock']}
    model['budget_cents'] = 0
    assert validate_model(model) == model
    assert model_hash(model) == model_hash(dict(reversed(list(model.items()))))
    assert 'properties' in model_schema()


def test_natural_labeled_tasks_keep_all_typed_clauses():
    result = compile_brief('''Title: Readable repair plan
Horizon: 30 minutes
Stock: parts=2
Resource bench: Repair bench has capacity 2, skills repair, and costs 3 cents per minute.
Task inspect: Inspect the radio takes 2 minutes using skill repair; needs 1 unit; available at 0; due by 10; priority 2; value 4; after none; consumes none.
Task fix: Fix the radio takes 4 minutes using skill repair; needs 2 units; available at 1; due by 20; priority 3; value 10; after inspect; consumes 2 parts.
''')
    assert result['ready'], result['issues']
    assert result['model']['resources'][0]['label'] == 'Repair bench'
    assert result['model']['tasks'][1] == dict(id='fix', label='Fix the radio', duration=4, skill='repair', units=2,
        release=1, due=20, priority=3, value=10, depends_on=['inspect'], materials={'parts': 2})
    invalid = compile_brief(result['facts'][3]['text'] + '\nTask fix takes 4 minutes using skill repair; no more than two people may work.')
    assert not invalid['ready']
    assert any(i['line'] == 2 for i in invalid['issues'])
