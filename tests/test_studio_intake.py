"""Natural intake tests exercise source facts, conflicts and replay boundaries."""
import pytest
from backend.studio.intake import PROMPTS, describe_model, intake
from backend.studio.schema import model_hash, validate_model


def answer(brief, history, value):
    state = intake(brief, history)
    assert len(state['questions']) == 1, state
    history = history + [{'question_id': state['questions'][0]['id'], 'answer': value}]
    return intake(brief, history), history


def finish(brief, values=()):
    history = []
    for value in values:
        state, history = answer(brief, history, value)
    state = intake(brief, history)
    assert state['questions'][0]['id'].split(':')[-1] == 'scope', state
    return answer(brief, history, 'accept')[0]


def test_incomplete_brief_never_invents_capacity_work_time():
    brief = 'Our community repair clinic has a queue of broken bikes. Help us plan the afternoon.'
    first = intake(brief)
    assert not first['ready'] and first['model_hash'] is None
    state, history = answer(brief, [], 'two volunteers')
    assert state['questions'][0]['kind'] == 'text'
    state, history = answer(brief, history, 'Six bike repairs, around twenty minutes each')
    assert 'time' in state['questions'][0]['prompt'].lower()
    state, history = answer(brief, history, 'two hours')
    state, history = answer(brief, history, 'accept')
    assert state['ready'], state
    assert len(state['model']['tasks']) == 6
    assert state['model']['horizon'] == 120
    assert state['model']['resources'][0]['capacity'] == 2
    assert {t['duration'] for t in state['model']['tasks']} == {20}


def test_generic_prose_number_words_and_changed_facts_change_model():
    brief = 'We have three archivists. Eight document scans take twelve minutes each. We have two hours to finish.'
    result = finish(brief)
    assert result['ready']
    assert len(result['model']['tasks']) == 8
    assert result['model']['resources'][0]['capacity'] == 3
    assert result['model_hash'] == model_hash(validate_model(result['model']))
    assert result['model_hash'] != finish(brief.replace('Eight', 'Six'))['model_hash']
    assert any('document scans' in f['text'] for f in result['facts'])
    assert '8' in describe_model(result['model'])


def test_conflicting_staff_and_time_are_both_resolved_explicitly():
    brief = 'We have two technicians. Actually we have four technicians. Six laptop repairs take ten minutes each. We have 60 minutes to finish. We have 90 minutes to finish.'
    first = intake(brief)
    q = first['questions'][0]
    assert q['conflict'] and len(q['evidence']) == 2
    assert {c['value'] for c in q['choices']} == {'2', '4'}
    state, history = answer(brief, [], '4')
    assert state['questions'][0]['conflict']
    state, history = answer(brief, history, '90')
    result = answer(brief, history, 'accept')[0]
    assert result['ready']
    assert result['model']['resources'][0]['capacity'] == 4
    assert result['model']['horizon'] == 90


def test_duration_and_count_conflicts_not_last_write_wins():
    brief = 'Two volunteers are available. Six bike repairs take twenty minutes each. Six bike repairs take thirty minutes each. We have two hours to finish.'
    q = intake(brief)['questions'][0]
    assert q['conflict'] and 'minutes' in q['prompt']
    result = finish(brief, ['30'])
    assert {t['duration'] for t in result['model']['tasks']} == {30}


def test_wrong_stale_invalid_answers_retain_accepted_prefix():
    brief = 'Help us handle repairs.'
    state, history = answer(brief, [], '2')
    wrong = intake(brief, history + [{'question_id': 'old:work', 'answer': 'six repairs'}])
    assert wrong['accepted_answers'] == history and not wrong['ready']
    assert wrong['issues'][0]['code'] == 'stale_answer'
    stale = intake(brief + ' Today.', history)
    assert not stale['accepted_answers'] and not stale['ready']
    bad = intake(brief, [{'question_id': intake(brief)['questions'][0]['id'], 'answer': 'zero'}])
    assert not bad['accepted_answers'] and bad['issues']


def test_dependencies_and_deadlines_remain_real_constraints():
    brief = 'Two technicians are available. Two inspections take five minutes each. Two repairs take ten minutes each. Repairs start after inspections finish. Repairs are due within 45 minutes. We have one hour to finish.'
    result = finish(brief)
    assert result['ready'], result
    inspections = [t['id'] for t in result['model']['tasks'] if 'inspection' in t['label']]
    repairs = [t for t in result['model']['tasks'] if 'repair' in t['label']]
    assert all(t['depends_on'] == inspections and t['due'] == 45 for t in repairs)


def test_unrecognized_operational_requests_need_explicit_scope_agreement():
    brief = 'Two volunteers are available. Six bike repairs take twenty minutes each. We have two hours to finish. Send customers a text message and drive bikes across town.'
    result = intake(brief)
    q = result['questions'][0]
    assert not result['ready'] and 'scope' in q['id']
    assert any('text message' in e for e in q['evidence'])
    assert 'travel' in ' '.join(q['details']).lower()
    rejected, history = answer(brief, [], 'revise')
    assert not rejected['ready'] and rejected['questions']
    accepted = finish(brief)
    assert any('text message' in str(a) for a in accepted['assumptions'])


def test_bounds_and_unexpected_answer_shapes_are_safe():
    assert intake('x' * 30001)['issues']
    assert intake('hello', [{}])['issues']
    assert intake('hello', [{'question_id': 'x', 'answer': 'x' * 2001}])['issues']
    assert intake('hello', [{}] * 101)['issues']
    assert not intake('We have 100 technicians. 100 jobs take 20 minutes each. We have 900 minutes to finish.')['ready']


def test_examples_are_natural_and_all_reach_review():
    assert len(PROMPTS) >= 3
    for prompt in PROMPTS:
        assert 'Resource ' not in prompt['brief'] and 'Task ' not in prompt['brief']
        assert set(prompt) == {'id', 'title', 'subtitle', 'brief'}
    assert finish(PROMPTS[0]['brief'], ['6', '20', '90'])['ready']
    assert finish(PROMPTS[1]['brief'], ['3', '90'])['ready']
    assert finish(PROMPTS[2]['brief'])['ready']


def test_work_clause_does_not_absorb_preceding_staffing_quantity():
    for brief in [
        'We have two people and six repairs, twenty minutes each. We have two hours to finish.',
        'Three volunteers can do six repairs, forty minutes each. We have two hours to finish.',
        'We are running a repair clinic for 120 minutes. We have two mechanics. We need to finish six bike repairs, each taking 30 minutes.',
    ]:
        result = finish(brief)
        assert len(result['model']['tasks']) == 6
        assert all('people and' not in t['label'] and 'can do' not in t['label'] for t in result['model']['tasks'])


def test_job_names_are_not_resources_due_to_word_suffix():
    result = finish('Two workers are available. Six orders take ten minutes each. We have one hour to finish.')
    assert len(result['model']['resources']) == 1
    assert len(result['model']['tasks']) == 6
    result = intake('Six neighbors brought bikes that need repairing. Two volunteers can help. We have two hours to finish.')
    assert not any(k['value'] == '6 people' for k in result['known'])


def test_rejected_work_answer_does_not_mutate_interview():
    brief = 'We have two volunteers.'
    original = intake(brief)
    answer_entry = {'question_id': original['questions'][0]['id'], 'answer': 'We have three mechanics.'}
    rejected = intake(brief, [answer_entry])
    assert rejected['accepted_answers'] == []
    assert rejected['known'] == original['known']
    assert rejected['facts'] == original['facts']
    assert rejected['questions'] == original['questions']


def test_partly_understood_work_and_total_duration_are_not_silently_modeled():
    brief = 'Two volunteers are here for two hours. We need to inspect six bikes, taking ten minutes per inspection, and then repair each one for thirty minutes. Each bike must be inspected before it is repaired.'
    state = intake(brief)
    # Unsupported repair stage must remain quoted even though the inspection is parsed.
    assert state['questions'][0]['id'].endswith(':scope'), state
    assert any('repair each one for thirty minutes' in e for e in state['questions'][0]['evidence'])
    total = intake('Two volunteers are available. Six repairs take thirty minutes total. We have one hour to finish.')
    assert 'one repair' in total['questions'][0]['prompt']
    assert not total['ready']


def test_uncertain_staffing_and_separate_duration_conflicts_are_questions():
    ambiguous = intake('We have two or three volunteers. Six repairs take twenty minutes each. We have two hours to finish.')
    assert ambiguous['questions'][0]['conflict']
    assert {c['value'] for c in ambiguous['questions'][0]['choices']} == {'2', '3'}
    uncertain = intake('We might have three volunteers. Six repairs take twenty minutes each. We have two hours to finish.')
    assert 'volunteers' in uncertain['questions'][0]['prompt']
    brief = 'Two volunteers are available. Six repairs take twenty minutes each. Each repair takes thirty minutes. We have two hours to finish.'
    state = intake(brief)
    assert state['questions'][0]['conflict']
    assert {c['value'] for c in state['questions'][0]['choices']} == {'20', '30'}


def test_compound_operational_clause_is_explicitly_outside_scope():
    brief = 'Two technicians are available and must determine whether the room layout is safe for wheelchair users. Six laptop setups take twenty minutes each. We have two hours.'
    state = intake(brief)
    assert any('wheelchair' in e for e in state['questions'][0]['evidence'])


def test_conflicting_paraphrased_windows_and_negation_need_resolution():
    brief = 'We have two people and six repairs, twenty minutes each. We can work for two hours, but the room is only available for ninety minutes.'
    state = intake(brief)
    q = state['questions'][0]
    assert q['conflict'] and {c['value'] for c in q['choices']} == {'120', '90'}
    negative = intake('We do not have two technicians. Six repairs take twenty minutes each. We have two hours.')
    assert 'technicians' in negative['questions'][0]['prompt']
    assert not any(k['id'].startswith('staff') for k in negative['known'])


def test_people_bringing_unknown_numbers_of_objects_is_not_a_work_count():
    state = intake('Six neighbors brought bikes that need repairing. Two volunteers are available. We have two hours.')
    assert not any(k['id'].startswith('count-') for k in state['known'])
    assert state['questions'][0]['id'].endswith(':work')


def test_oversized_numeric_answer_is_a_helpful_error_not_an_exception():
    brief = 'Help me plan repairs.'
    q = intake(brief)['questions'][0]
    state = intake(brief, [{'question_id': q['id'], 'answer': '9' * 500}])
    assert state['issues'][0]['code'] == 'invalid_answer'
    assert state['accepted_answers'] == []


@pytest.mark.parametrize('value', ['-2', 'not two', 'maybe three', 'at most four'])
def test_numeric_answers_do_not_turn_negative_or_uncertain_claims_into_facts(value):
    brief = 'Help us plan repairs.'
    q = intake(brief)['questions'][0]
    result = intake(brief, [{'question_id': q['id'], 'answer': value}])
    assert not result['accepted_answers']
    assert result['issues'][0]['code'] == 'invalid_answer'


def test_compound_time_not_silently_truncated_to_first_unit():
    state = intake('Two volunteers are available. Six repairs take twenty minutes each. We have one hour and thirty minutes to finish.')
    assert state['questions'][0]['id'].endswith(':horizon')
    assert not any(k['id'] == 'horizon' for k in state['known'])


@pytest.mark.parametrize('staff', ['Two technicians are unavailable.', 'We need two technicians.'])
def test_required_or_unavailable_staff_are_not_assumed_available(staff):
    result = intake(staff + ' Six repairs take twenty minutes each. We have two hours.')
    assert not any(k['id'].startswith('staff') for k in result['known'])
    assert 'technicians' in result['questions'][0]['prompt']


def test_alternative_time_windows_are_not_silently_first_match():
    state = intake('Two technicians are available. Six repairs take twenty minutes each. We have two hours or three hours to finish.')
    q = state['questions'][0]
    assert q['conflict'] and {c['value'] for c in q['choices']} == {'120', '180'}


def test_work_exception_remains_quoted_at_scope_review():
    state = intake('Two technicians are available. Six repairs take twenty minutes each unless they need inspection. We have two hours.')
    assert any('unless they need inspection' in e for e in state['questions'][0]['evidence'])


@pytest.mark.parametrize('text', ['not a number', 'a number', 'a few', 'an example'])
def test_articles_in_non_numeric_text_do_not_become_one(text):
    brief = 'We have two volunteers. There are bike repairs waiting.'
    first = intake(brief)
    result = intake(brief, [{'question_id': first['questions'][0]['id'], 'answer': text}])
    assert result['questions'] == first['questions']
    assert result['accepted_answers'] == []
    assert result['issues']


def test_compound_duration_requires_confirmed_total():
    state = intake('Two volunteers are available. Six repairs take one hour and thirty minutes each. We have two hours.')
    assert state['questions'][0]['id'].endswith(':duration-1')
    assert not any(k['id'] == 'duration-1' for k in state['known'])


def test_two_deadlines_in_one_sentence_bind_to_their_actual_work():
    brief = 'Two volunteers are available. Two inspections take ten minutes each. Six repairs take twenty minutes each. Repairs are due within 30 minutes, inspections are due within 60 minutes. We have two hours.'
    result = finish(brief)
    assert {t['due'] for t in result['model']['tasks'] if 'inspections' in t['label']} == {60}
    assert {t['due'] for t in result['model']['tasks'] if 'repairs' in t['label']} == {30}


@pytest.mark.parametrize('text', ['twenty seconds', '20 bikes', 'two days'])
def test_duration_answers_reject_other_units(text):
    brief = 'Two volunteers are available. Six repairs are waiting. We have two hours.'
    first = intake(brief)
    assert first['questions'][0]['id'].endswith(':duration-1')
    state = intake(brief, [{'question_id': first['questions'][0]['id'], 'answer': text}])
    assert state['questions'] == first['questions']
    assert not state['accepted_answers']


def test_provided_qualification_is_retained_for_explicit_scope_review():
    state = intake('Two volunteers are available. Six repairs take twenty minutes each, provided inspections finish first. We have two hours.')
    assert any('provided inspections finish first' in e for e in state['questions'][0]['evidence'])


@pytest.mark.parametrize('tail', ['depending on which tools work', 'when the station becomes available', 'subject to a manager agreeing'])
def test_unknown_trailing_constraints_are_retained_without_keyword_classification(tail):
    state = intake('Two volunteers are available. Six repairs take twenty minutes each ' + tail + '. We have two hours.')
    assert any(tail in e for e in state['questions'][0]['evidence'])


@pytest.mark.parametrize('time_claim', [
    'Repairs are due within one hour and thirty minutes.',
    'Each repair takes one hour and thirty minutes.',
])
def test_all_time_extraction_paths_require_confirmation_of_compound_values(time_claim):
    work = 'Six repairs are waiting.' if time_claim.startswith('Each') else 'Six repairs take twenty minutes each.'
    state = intake('Two volunteers are available. ' + work + ' ' + time_claim + ' We have two hours.')
    assert not state['questions'][0]['id'].endswith(':scope')
    assert not any(k['value'] == '60 minutes' for k in state['known'])


def test_unrecognized_staff_status_does_not_assert_availability():
    state = intake('Two technicians are sick. Six repairs take twenty minutes each. We have two hours.')
    assert not any(k['id'].startswith('staff') for k in state['known'])
    assert 'technicians' in state['questions'][0]['prompt']


def test_benign_planning_goal_is_context_not_an_excluded_requirement():
    brief = PROMPTS[0]['brief']
    state = intake(brief)
    history = []
    for value in ['6', '20', '90']:
        state, history = answer(brief, history, value)
    assert not any('help fitting them into the afternoon' in e for e in state['questions'][0]['evidence'])
    assert any('context' in f['targets'] and 'help fitting' in f['text'] for f in state['facts'])


@pytest.mark.parametrize('prefix', ['If the manager approves, ', 'Subject to inspections finishing, ', 'After safety approval, '])
def test_unknown_leading_constraints_are_preserved_at_scope_review(prefix):
    state = intake('Two volunteers are available. ' + prefix + 'six repairs take twenty minutes each. We have two hours.')
    assert any(prefix.strip(' ,') in e for e in state['questions'][0]['evidence'])


@pytest.mark.parametrize(('brief', 'response'), [
    ('Help us plan repairs.', 'two hours'),
    ('Two volunteers are available. There are bike repairs waiting. We have two hours.', 'six minutes'),
])
def test_count_answers_reject_time_units(brief, response):
    first = intake(brief)
    state = intake(brief, [{'question_id': first['questions'][0]['id'], 'answer': response}])
    assert state['questions'] == first['questions']
    assert not state['accepted_answers']
