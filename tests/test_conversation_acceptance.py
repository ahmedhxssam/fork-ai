"""Independent user-like intake journeys with hand-derived scheduling checks."""
import pytest

from backend.studio.engine import simulate
from backend.studio.intake import intake
from backend.studio.referee import verify


def finish(brief, *, staff='two', duration='45 minutes each', horizon='two hours', work=None):
    """Answer the current question; never reuse a stale ID or inject model data."""
    history = []
    for _ in range(12):
        state = intake(brief, history)
        assert not state['issues'], state
        if state['ready']:
            assert not state['questions']
            return state, history
        assert state['model_hash'] is None and len(state['questions']) == 1, state
        question = state['questions'][0]
        field = question['id'].split(':')[-1]
        if field.startswith('staff'):
            answer = staff
        elif field.startswith('duration'):
            answer = duration
        elif field == 'horizon':
            answer = horizon
        elif field == 'work' and work:
            answer = work
        elif field == 'scope':
            answer = 'Use this simplified scope'
        else:
            pytest.fail(f'Unexpected unanswered question: {question}')
        history.append({'question_id': question['id'], 'answer': answer})
    pytest.fail('Ordinary answers did not reach a reviewable model')


def verified_result(state):
    result = simulate(state['model'], 'throughput')
    receipt = verify(state['model'], result)
    assert receipt['valid'], receipt
    return result


def test_staff_conflict_answers_change_actual_capacity_and_completed_work():
    brief = ('We have six bikes waiting for repair. Two volunteers can help; '
             'actually three people said they would be there. '
             'Each bike takes 45 minutes and we have two hours.')
    first = intake(brief)
    question = first['questions'][0]
    assert question['conflict']
    assert {choice['value'] for choice in question['choices']} == {'2', '3'}
    evidence = ' '.join(question['evidence'])
    assert 'Two volunteers' in evidence and 'three people' in evidence
    two, _ = finish(brief, staff='two')
    three, _ = finish(brief, staff='three')
    assert two['model_hash'] != three['model_hash']
    assert [two['model']['resources'][0]['capacity'], three['model']['resources'][0]['capacity']] == [2, 3]
    for state in (two, three):
        assert len(state['model']['tasks']) == 6
        assert {task['duration'] for task in state['model']['tasks']} == {45}
    assert verified_result(two)['metrics']['completed'] == 4
    assert verified_result(three)['metrics']['completed'] == 6


def test_unknown_job_time_answer_changes_real_schedule_not_only_summary():
    brief = 'Six bikes are waiting for repair. Two volunteers are available. We have two hours.'
    first = intake(brief)
    assert not first['ready'] and first['model_hash'] is None
    assert first['questions'][0]['unit'] == 'minutes'
    short, _ = finish(brief, duration='About fifteen minutes per bike')
    long, _ = finish(brief, duration='About 45 minutes per bike')
    assert short['model_hash'] != long['model_hash']
    assert {task['duration'] for task in short['model']['tasks']} == {15}
    assert {task['duration'] for task in long['model']['tasks']} == {45}
    short_result, long_result = verified_result(short), verified_result(long)
    assert (short_result['metrics']['completed'], short_result['metrics']['makespan']) == (6, 45)
    assert long_result['metrics']['completed'] == 4


def test_conflicting_work_and_room_windows_show_both_original_claims():
    brief = ('We have two people and six repairs, twenty minutes each. '
             'We can work for two hours, but the room is only available for ninety minutes.')
    question = intake(brief)['questions'][0]
    assert question['conflict']
    assert {choice['value'] for choice in question['choices']} == {'90', '120'}
    evidence = ' '.join(question['evidence'])
    assert 'work for two hours' in evidence and 'available for ninety minutes' in evidence
    short, _ = finish(brief, horizon='ninety minutes')
    long, _ = finish(brief, horizon='two hours')
    assert short['model']['horizon'] == 90
    assert long['model']['horizon'] == 120
    assert short['model_hash'] != long['model_hash']


@pytest.mark.parametrize('opening', [
    'We have two people and six repairs, twenty minutes each.',
    'Two volunteers can do six repairs, twenty minutes each.',
])
def test_combined_staffing_and_job_sentence_does_not_steal_staff_count(opening):
    state, _ = finish(opening + ' We have two hours.', duration='twenty minutes')
    assert len(state['model']['resources']) == 1
    assert state['model']['resources'][0]['capacity'] == 2
    assert len(state['model']['tasks']) == 6
    assert {task['duration'] for task in state['model']['tasks']} == {20}
    assert verified_result(state)['metrics']['completed'] == 6


@pytest.mark.parametrize('brief, forbidden', [
    ('Six neighbors brought bikes that need repairing. Two volunteers can work on them this afternoon, '
     'and the workshop is open for two hours. I do not know how long the repairs take.', 'neighbors'),
    ('There are six bicycles in the queue. A pair of volunteers can tackle them for the next couple of hours. '
     'Allow three quarters of an hour for each one.', 'quarters'),
])
def test_numeric_nouns_do_not_invent_resource_capacity_or_work_quantity(brief, forbidden):
    state = intake(brief)
    assert not any(item['id'].startswith(('staff', 'count')) and forbidden in item['label']
                   for item in state['known']), state
    if forbidden == 'neighbors':
        assert not any(item['id'].startswith('count') for item in state['known']), state


def test_noncanonical_laptop_operation_can_be_completed_in_ordinary_words():
    brief = ('Three technicians need to prepare eight laptops for an event. '
             'Each setup takes twenty minutes. We have ninety minutes before the doors open.')
    state, _ = finish(brief, staff='three', horizon='ninety minutes',
                      work='Eight laptop setups, around twenty minutes each')
    assert len(state['model']['tasks']) == 8
    assert state['model']['horizon'] == 90
    assert state['model']['resources'][0]['capacity'] == 3
    assert all('laptop' in task['label'] for task in state['model']['tasks'])
    result = verified_result(state)
    assert (result['metrics']['completed'], result['metrics']['makespan']) == (8, 60)


def test_editing_issue_cannot_reuse_previously_accepted_interview():
    brief = 'Six bikes are waiting for repair. Two volunteers are available. We have two hours.'
    original, history = finish(brief)
    assert history
    edited = intake(brief.replace('Six bikes', 'Eight bikes'), history)
    assert edited['brief_hash'] != original['brief_hash']
    assert not edited['ready'] and edited['model_hash'] is None
    assert not edited['accepted_answers']
    assert any(issue['code'] == 'stale_answer' for issue in edited['issues'])
    changed, _ = finish(brief.replace('Six bikes', 'Eight bikes'))
    assert len(changed['model']['tasks']) == 8
    assert changed['model_hash'] != original['model_hash']


def test_editing_an_earlier_answer_requires_new_dependent_question_ids():
    brief = ('We have six bikes waiting for repair. Two volunteers can help; '
             'actually three people said they would be there. '
             'Each bike takes 45 minutes and we have two hours.')
    ready, history = finish(brief, staff='two')
    assert ready['ready'] and len(history) >= 2
    edited_history = [dict(history[0], answer='three'), *history[1:]]
    edited = intake(brief, edited_history)
    assert not edited['ready'] and edited['model_hash'] is None
    assert edited['accepted_answers'] == edited_history[:1]
    assert any(issue['code'] == 'stale_answer' for issue in edited['issues'])


def test_partly_recognized_sentence_does_not_hide_a_second_work_stage():
    work = ('We need to inspect six bikes, taking ten minutes per inspection, '
            'and then repair each one for thirty minutes.')
    brief = ('Two volunteers are here for two hours. ' + work +
             ' Each bike must be inspected before it is repaired.')
    state = intake(brief)
    history = []
    for _ in range(8):
        assert not state['ready'], 'Unresolved repair work must reach explicit scope review'
        question = state['questions'][0]
        if question['id'].endswith(':scope'):
            durations = [item['value'] for item in state['known'] if item['id'].startswith('duration')]
            assert '30 minutes' in durations or any('repair each one for thirty minutes' in span
                                                   for span in question['evidence']), state
            return
        field = question['id'].split(':')[-1]
        answer = 'two hours' if field == 'horizon' else 'ten minutes'
        history.append({'question_id': question['id'], 'answer': answer})
        state = intake(brief, history)
    pytest.fail('Could not reach explicit work/scope clarification')


@pytest.mark.parametrize('extra_request', [
    'must drive between homes and account for traffic',
    'must choose the correct medication dose for patients',
    'must determine whether the room layout is safe for wheelchair users',
])
def test_consequential_extra_request_is_visible_even_in_a_staffing_sentence(extra_request):
    sentence = 'Two technicians are available and ' + extra_request + '.'
    brief = sentence + ' Six laptop setups take twenty minutes each. We have two hours.'
    state = intake(brief)
    question = state['questions'][0]
    assert not state['ready'] and question['id'].endswith(':scope'), state
    assert all(clause in ' '.join(question['evidence']) for clause in extra_request.split(' and ')), state
    reviewed, _ = finish(brief)
    exclusions = next(item for item in reviewed['assumptions'] if item['field'] == 'excluded_details')
    assert all(clause in ' '.join(exclusions['value']) for clause in extra_request.split(' and '))
