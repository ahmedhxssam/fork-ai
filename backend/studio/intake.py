"""Bounded, local natural-language interview; no model provider or executable prose.

Extraction records candidates rather than overwriting claims. A stateless replay
applies each answer only to its exact next question. Unrecognized statements are
shown at a mandatory simplified-scope decision, never silently treated as modeled.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field

from .schema import model_hash, validate_model

PROMPTS = [
    dict(id='repair-clinic', title='Incomplete details', subtitle='A community repair afternoon',
         brief='We are running a community repair clinic with two volunteers. There are bike repairs waiting, and I need help fitting them into the afternoon.'),
    dict(id='conflicting-details', title='Conflicting details', subtitle='Different staffing and timing claims',
         brief='We have two technicians available for laptop repairs. The coordinator says we have three technicians. Six laptop repairs take forty-five minutes each. We have one hour to finish. The room booking says we have 90 minutes to finish.'),
    dict(id='it-helpdesk', title='Another operation', subtitle='An IT support queue',
         brief='Our help desk has three technicians. Eight laptop setups take fifteen minutes each. Four account checks take ten minutes each. Account checks start after laptop setups finish. Account checks are due within 100 minutes. We have two hours to finish.'),
]

_WORDS = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty ninety'.split(), list(range(21)) + [30, 40, 50, 60, 90]))
_NUM = r'(?:\d+(?:\.\d+)?|(?:twenty|thirty|forty|fifty|sixty|ninety)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|an?|half)'
_TIME = rf'(?P<amount>{_NUM})\s*(?P<unit>minutes?|mins?|hours?|hrs?)\b'
_ROLES = r'(?:volunteers?|people|persons?|staff(?: members)?|workers?|technicians?|helpers?|crew(?: members)?|operators?|nurses?|doctors?|mechanics?|engineers?|designers?|archivists?|librarians?|reviewers?|editors?|cooks?|chefs?|machines?|printers?|benches?|stations?|jewelers?|carpenters?|electricians?|plumbers?|analysts?|agents?|assemblers?)'
_ROLE_RE = re.compile(rf'\b(?P<count>{_NUM})\s+(?P<label>(?:(?:audio|security|support|repair|senior|junior|it|operations|stage)\s+)?{_ROLES})\b', re.I)
_GENERIC_ROLES = {'volunteer', 'people', 'person', 'staff', 'staff member', 'worker', 'helper', 'crew', 'crew member'}
_SCOPE_NOTE = ('Synthetic deterministic planning only. Work is checkpointable and uses one person or resource unit at a time. '
               'No travel, customer messages, physical safety decisions, or live execution are modeled.')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def _number(text):
    text = text.strip().lower().replace('-', ' ')
    if re.fullmatch(r'\d+(?:\.\d+)?', text):
        return float(text) if len(text) <= 12 else 1_000_000_000
    if text in {'a', 'an'}:
        return 1
    if text == 'half':
        return .5
    parts = text.split()
    return sum(_WORDS[p] for p in parts) if parts and all(p in _WORDS for p in parts) else None


def _minutes(match):
    value = _number(match['amount'])
    return value * (60 if match['unit'].lower().startswith(('hour', 'hr')) else 1)


def _clean(text):
    return re.sub(r'\s+', ' ', text.strip(' ,.:;!?')).lower()


def _key(text):
    words = _clean(text).split()
    return ' '.join(w[:-1] if w.endswith('s') and not w.endswith('ss') else w for w in words)


def _sentences(text):
    result = []
    for match in re.finditer(r'[^.!?;\n]+(?:[.!?;]|$)', text):
        for clause in re.split(rf',?\s+\b(?:and then|and(?!\s+{_NUM}\s+(?:minutes?|mins?)\b)|but|then)\s+|\s+(?=(?:unless|except|provided|if)\b)', match.group(), flags=re.I):
            if clause.strip():
                result.append((text[:match.start()].count('\n') + 1, clause.strip()))
    return result


@dataclass
class Slot:
    id: str
    label: str
    unit: str
    minimum: int
    maximum: int
    claims: list = field(default_factory=list)
    answer: int | str | None = None
    answer_source: str | None = None
    uncertain: bool = False

    def add(self, value, line, text):
        # Every time path uses this gate, including deadlines and later duration claims.
        if self.unit == 'minutes' and re.search(rf'\b(?:hours?|hrs?)\s+(?:and\s+)?{_NUM}\s+(?:minutes?|mins?)\b', text, re.I):
            self.uncertain = True
        self.claims.append(dict(value=value, line=line, text=text))

    @property
    def values(self):
        return list(dict.fromkeys(c['value'] for c in self.claims))

    @property
    def value(self):
        if self.answer is not None:
            return self.answer
        values = self.values
        if not self.uncertain and len(values) == 1 and self.minimum <= values[0] <= self.maximum and int(values[0]) == values[0]:
            return int(values[0])
        return None

    def question(self):
        conflict = len(self.values) > 1 or self.uncertain
        choices = [dict(value=str(int(v)), label=f'{int(v)} {self.unit}') for v in self.values
                   if self.minimum <= v <= self.maximum and v == int(v)] if len(self.values) > 1 else []
        return dict(key=self.id, prompt=(f'I found conflicting numbers. {self.label}' if len(self.values) > 1 else self.label),
                    why='This changes how much work fits and when it can finish.',
                    kind='choice' if choices else 'number', choices=choices,
                    min=self.minimum, max=self.maximum, unit=self.unit, conflict=conflict,
                    evidence=[c['text'] for c in self.claims])


class Interview:
    def __init__(self, brief):
        self.brief = brief
        self.resources = []
        self.groups = []
        self.horizon = Slot('horizon', 'How much time do we have to do the work?', 'minutes', 1, 720)
        self.facts = []
        self.unmodeled = []
        self.dependencies = []
        self.scope = False
        self.work_answer = None
        self.extract(brief)

    def fact(self, line, text, targets):
        self.facts.append(dict(line=line, text=text, targets=targets))

    def resource(self, label):
        key = _key(label)
        if key in _GENERIC_ROLES:
            key = 'people'
        existing = next((r for r in self.resources if r['key'] == key), None)
        if existing:
            return existing
        index = len(self.resources) + 1
        row = dict(id=f'r{index}', label=label, key=key,
                   count=Slot(f'staff-{index}', f'How many {label} can work at the same time?', 'people', 1, 12))
        self.resources.append(row)
        return row

    def group(self, label):
        label = _clean(re.sub(r'^(?:the|our|some)\s+', '', label, flags=re.I))
        label = re.sub(r'\s+(?:are|is)$', '', label)
        key = _key(label)
        existing = next((g for g in self.groups if g['key'] == key), None)
        if existing:
            return existing
        index = len(self.groups) + 1
        row = dict(id=f'g{index}', label=label, key=key,
                   count=Slot(f'count-{index}', f'How many {label} need doing?', 'jobs', 1, 80),
                   duration=Slot(f'duration-{index}', f'About how many minutes does one {key} take?', 'minutes', 1, 720),
                   due=Slot(f'due-{index}', f'How many minutes from the start must {label} be finished by?', 'minutes', 0, 720),
                   resource=None, resource_source=None, after=[])
        self.groups.append(row)
        return row

    def extract(self, text, from_answer=False):
        sentences = _sentences(text)
        recognized = set()
        covered_ends, covered_starts = {}, {}
        def cover(sentence, end, start=0):
            covered_ends[sentence] = max(end, covered_ends.get(sentence, 0))
            covered_starts[sentence] = min(start, covered_starts.get(sentence, len(sentence)))
        for line, sentence in sentences:
            low = sentence.lower()
            if re.fullmatch(r'(?:i|we) (?:need|want) help (?:fitting (?:them|the work|these jobs) into (?:the )?(?:afternoon|morning|day)|planning (?:the work|these jobs|this))[.!?]?', low):
                self.fact(line, sentence, ['context'])
                recognized.add(sentence)
            # Every distinct staffing claim remains a candidate, including corrections.
            for match in _ROLE_RE.finditer(sentence):
                cover(sentence, match.end(), match.start())
                role = self.resource(match['label'].lower())
                role['count'].add(_number(match['count']), line, sentence)
                prefix, suffix = sentence[:match.start()].lower(), sentence[match.end():].lower().strip(' .')
                status = re.match(r'(?:are|is|were|will be|have been|can|cannot|can.t)\b', suffix)
                positive_status = re.match(r'(?:(?:are|is|were|will be|have been)\s+(?:available|here|working|ready)\b|can\s+(?:help|work|do|handle)\b|available\b)', suffix)
                affirmative = positive_status or re.search(r'\b(?:have|has|with|there are)\s*$', prefix)
                if (status and not positive_status) or not affirmative:
                    role['count'].uncertain = True
                alternative = re.search(rf'(?P<first>{_NUM})\s+(?:or|to)\s+$', sentence[:match.start()], re.I)
                if alternative:
                    role['count'].add(_number(alternative['first']), line, sentence)
                if re.search(r'\b(?:might|maybe|perhaps|up to|at most|at least|may have|not|never|don.t|unavailable|absent|need|require|needed|required|want)\b', sentence, re.I):
                    role['count'].uncertain = True
                self.fact(line, sentence, [f"resources.{role['id']}.capacity"])
                recognized.add(sentence)
            # Horizon wording must refer to the window, not a per-job duration/deadline.
            horizon_patterns = [
                rf'(?:we (?:only )?have|we(?:\x27ve| have) got|(?:workshop|clinic|session|shift|room|event) (?:is |runs |lasts |stays )?(?:only )?(?:open |available )?for|(?:plan|planning|finish|working) (?:over|for|within|in)|time (?:window|available) (?:is|of))\s+(?:about |around |the next )?{_TIME}',
                rf'(?P<amount>{_NUM})[ -](?P<unit>hours?|minutes?)\s+(?:window|shift|session|workshop)',
                rf'(?:clinic|workshop|session|shift|event)\s+for\s+{_TIME}',
                rf'(?:are|is)\s+(?:here|available|working)\s+for\s+{_TIME}',
                rf'we can work for\s+{_TIME}',
            ]
            for pattern in horizon_patterns:
                for match in re.finditer(pattern, sentence, re.I):
                    cover(sentence, match.end(), match.start())
                    self.horizon.add(_minutes(match), line, sentence)
                    alternative = re.match(rf'\s+or\s+{_TIME}', sentence[match.end():], re.I)
                    if alternative:
                        self.horizon.add(_minutes(alternative), line, sentence)
                    self.fact(line, sentence, ['horizon'])
                    recognized.add(sentence)
            # Generic quantified work, with or without a duration in the same phrase.
            label_word = rf'(?!{_NUM}\b)[a-z]+'
            work_pattern = rf'\b(?P<count>{_NUM})\s+(?P<label>{label_word}(?:[ -]+{label_word}){{0,9}}?)\s*(?:(?:,\s*)?(?:each\s+)?(?:take|takes|taking|need|needs|require|requires|last|lasts|lasting)\s+|,\s*(?:around|about|roughly)?\s*)(?:about |around |roughly )?{_TIME}(?:\s*(?:each|apiece|per (?:job|item|task)))?'
            for match in re.finditer(work_pattern, sentence, re.I):
                if _ROLE_RE.fullmatch(match['count'] + ' ' + match['label']) or re.search(r'\b(?:minutes?|hours?|have|available|cost|budget)\b', match['label'], re.I):
                    continue
                cover(sentence, match.end(), match.start())
                group = self.group(match['label'])
                group['count'].add(_number(match['count']), line, sentence)
                if not re.search(r'\b(?:total|altogether|combined|together)\b', sentence, re.I):
                    group['duration'].add(_minutes(match), line, sentence)
                self.fact(line, sentence, [f"tasks.{group['id']}.count", f"tasks.{group['id']}.duration"])
                recognized.add(sentence)
            # A queue can name the work without yet knowing count or duration.
            queue = re.search(rf'\b(?P<count>{_NUM})\s+(?P<label>[a-z][a-z -]{{0,50}}?)\s+(?:waiting|queued|pending|to (?:repair|process|check|complete|do)|need (?:repair|fix|check))', sentence, re.I)
            if queue and not _ROLE_RE.fullmatch(queue['count'] + ' ' + queue['label']) and not re.search(r'\b(?:brought|bring|have|has|that|who|which|can|will|said|with|said)\b', queue['label'], re.I):
                cover(sentence, queue.end(), queue.start())
                group = self.group(queue['label'])
                group['count'].add(_number(queue['count']), line, sentence)
                self.fact(line, sentence, [f"tasks.{group['id']}.count"])
                recognized.add(sentence)
            missing = re.search(r'(?:there are|we have|a queue of)\s+(?:(?:some|several)\s+)?([a-z][a-z -]{0,45}?)\s+(?:waiting|queued|pending)', sentence, re.I)
            if missing and not re.search(rf'\b{_NUM}\b', missing[1], re.I):
                cover(sentence, missing.end(), missing.start())
                group = self.group(missing[1])
                self.fact(line, sentence, [f"tasks.{group['id']}.label"])
                recognized.add(sentence)
        # Durations often arrive in a second sentence without repeating the quantity.
        for line, sentence in sentences:
            match = re.search(rf'\b(?:each|every)\s+(?P<label>[a-z][a-z -]{{0,50}}?)\s+(?:takes?|needs?|requires?)\s+(?:about |around )?{_TIME}', sentence, re.I)
            if match:
                group = self.match_group(match['label'])
                if group:
                    cover(sentence, match.end(), match.start())
                    group['duration'].add(_minutes(match), line, sentence)
                    self.fact(line, sentence, [f"tasks.{group['id']}.duration"])
                    recognized.add(sentence)
        # Deadlines and dependencies refer to actual extracted work names.
        for line, sentence in sentences:
            for group in self.groups:
                aliases = self.aliases(group)
                mentioned = next((a for a in aliases if re.search(r'\b' + re.escape(a) + r'\b', sentence, re.I)), None)
                if not mentioned:
                    continue
                for deadline in re.finditer(rf'(?:due|finished|done|completed)\s+(?:by|within|in|before)\s+(?:minute\s+)?{_TIME}', sentence, re.I):
                    subject = sentence[:deadline.start()].rsplit(',', 1)[-1]
                    if self.match_group(subject) == group:
                        cover(sentence, deadline.end())
                        group['due'].add(_minutes(deadline), line, sentence)
                        self.fact(line, sentence, [f"tasks.{group['id']}.due"])
                        recognized.add(sentence)
                # Role attribution only when named in this work statement.
                named = [r for r in self.resources if re.search(r'\b' + re.escape(r['label']) + r'\b', sentence, re.I)]
                if len(named) == 1 and (re.search(r'\b(?:handle|perform|do|by|using)\b', sentence, re.I)):
                    group['resource'] = named[0]['id']
                    group['resource_source'] = sentence
            dependency = re.search(r'(.+?)\s+(?:start(?:s)? |begin(?:s)? |can (?:start|begin) |must (?:start|begin) |happen(?:s)? )?after\s+(.+)', sentence, re.I)
            before = re.search(r'(.+?)\s+(?:has to happen |must happen |happen(?:s)? |finish(?:es)? )?before\s+(.+)', sentence, re.I)
            if dependency or before:
                match = dependency or before
                left, right = match[1], match[2]
                lhs, rhs = self.match_group(left), self.match_group(right)
                if lhs and rhs and lhs != rhs:
                    cover(sentence, len(sentence))
                    target, source = (lhs, rhs) if dependency else (rhs, lhs)
                    if source['id'] not in target['after']:
                        target['after'].append(source['id'])
                    self.fact(line, sentence, [f"tasks.{target['id']}.depends_on"])
                    recognized.add(sentence)
                else:
                    self.unmodeled.append(sentence)
            # Leading prose is not covered merely because a later numeric phrase parsed.
            if sentence in covered_starts:
                prefix = sentence[:covered_starts[sentence]].strip(' ,.;!?')
                framing = r'(?:we (?:have|need|need to (?:finish|inspect|do|complete))|there are|the|our [a-z ]+ has|(?:actually )?we have|the coordinator says we have)'
                running = r'we are running (?:a|an) [a-z ]+(?: with)?'
                if prefix and not re.fullmatch(framing, prefix, re.I):
                    if re.fullmatch(running, prefix, re.I):
                        self.fact(line, prefix, ['context'])
                    else:
                        self.unmodeled.append(prefix)
            # Preserve unconsumed trailing prose structurally, not by domain keywords.
            # Only complete grammatical endings carry no further constraint.
            if sentence in covered_ends:
                tail = sentence[covered_ends[sentence]:].strip(' ,.;!?')
                harmless = r'(?:(?:are|is) (?:available|here)|can help|to finish|each|apiece|per (?:job|item|task|inspection|repair)|(?:are |is )?(?:waiting|queued|pending))'
                if tail and not re.fullmatch(harmless, tail, re.I):
                    self.unmodeled.append(tail)
            # Even a partly understood sentence must not conceal operational limits.
            if re.search(r'\b(?:travel|drive|driving|send|message|text|email|medication|dosage|budget|cost|pay|paid|wage|stock|parts|batteries|licenses|urgent|priority|break|outage|simultaneously|together|cannot|can\x27t|only|available at|release|arrive|arriving)\b|\$', sentence, re.I):
                self.unmodeled.append(sentence)
            if sentence not in recognized:
                self.unmodeled.append(sentence)
        self.unmodeled = list(dict.fromkeys(self.unmodeled))

    @staticmethod
    def aliases(group):
        # Singular/plural variation is explicit, not semantic domain substitution.
        return list(dict.fromkeys([group['label'], group['key'], group['label'].split()[-1], group['key'].split()[-1]]))

    def match_group(self, text):
        matches = [g for g in self.groups if any(re.search(r'\b' + re.escape(a) + r'\b', text, re.I) for a in self.aliases(g))]
        return matches[0] if len(matches) == 1 else None

    def slots(self):
        result = [r['count'] for r in self.resources]
        for group in self.groups:
            result.extend([group['count'], group['duration']])
        result.append(self.horizon)
        result.extend(g['due'] for g in self.groups if g['due'].claims)
        return result

    def next(self):
        if not self.resources:
            return dict(key='staff', prompt='How many people or workstations can do this work at the same time?', why='We need a real capacity before scheduling.', kind='number', choices=[], min=1, max=12, unit='people', conflict=False, evidence=[])
        for role in self.resources:
            if role['count'].value is None:
                return role['count'].question()
        if not self.groups:
            return dict(key='work', prompt='What work is waiting, how many jobs are there, and about how long does each take?', why='For example: “Six bike repairs, around 20 minutes each.” You can describe one or more groups of work.', kind='text', choices=[], min=None, max=None, unit=None, conflict=False, evidence=[])
        for group in self.groups:
            for name in ('count', 'duration'):
                slot = group[name]
                if name == 'duration' and self.horizon.value:
                    slot.maximum = self.horizon.value
                if slot.value is None:
                    return slot.question()
        if self.horizon.value is None:
            return self.horizon.question()
        for group in self.groups:
            due = group['due']
            due.maximum = self.horizon.value
            if due.claims and due.value is None:
                return due.question()
            if len(self.resources) > 1 and not group['resource']:
                return dict(key=f"role-{group['id']}", prompt=f"Who can do the {group['label']}?", why='Choose the pool that performs these jobs. Different pools are not interchangeable without confirmation.', kind='choice', choices=[dict(value=r['id'], label=r['label']) for r in self.resources], min=None, max=None, unit=None, conflict=False, evidence=[])
        if not self.scope:
            return dict(key='scope', prompt='Use this simplified planning scope?',
                        why='Confirm these assumptions before model review. Quoted details below are outside the model; edit the description if they are essential.',
                        details=[
                            'Each job uses one person or resource unit and can pause and resume.',
                            'All work is available at the start; jobs have equal importance and equal completion value.',
                            'Unspecified deadlines mean the end of the session.',
                            'Only the work, staffing, times and ordering shown above are included.',
                            'Costs, budgets, stock, travel, messages and other unrecognized details are excluded.',
                            'For ordering between groups, all earlier jobs finish before later jobs start. No other dependencies are assumed.',
                        ],
                        kind='choice', choices=[dict(value='accept', label='Use this simplified scope'), dict(value='revise', label='I need to change the scope')], min=None, max=None, unit=None, conflict=False, evidence=self.unmodeled)
        return None

    def apply(self, question, text):
        key = question['key']
        if key == 'scope':
            if text.strip().lower() in {'accept', 'yes', 'use this simplified scope'}:
                self.scope = True
                return None
            return 'Edit the original description to change the scope, or choose “Use this simplified scope” to accept the listed exclusions.'
        if key.startswith('role-'):
            selected = next((r for r in self.resources if text.strip().lower() in {r['id'].lower(), r['label'].lower()}), None)
            if not selected:
                return 'Choose one of the listed people or resource pools.'
            group = next(g for g in self.groups if 'role-' + g['id'] == key)
            group['resource'], group['resource_source'] = selected['id'], text
            return None
        if key == 'work':
            self.extract(text, from_answer=True)
            if not self.groups:
                return 'Please name a group of work and its quantity, for example “Six bike repairs, around 20 minutes each”.'
            self.work_answer = text
            return None
        if re.search(r'(?<!\w)-\s*\d|\b(?:not|negative|maybe|perhaps|at most|at least|up to|might)\b', text, re.I):
            return 'Please give one confirmed, nonnegative number for this plan.'
        amounts = list(re.finditer(rf'\b{_NUM}\b', text, re.I))
        if len(amounts) != 1:
            return 'Please give one whole number, optionally with minutes or hours.'
        if amounts[0].group().lower() in {'a', 'an'}:
            tail = text[amounts[0].end():].strip()
            if not re.match(rf'(?:{_ROLES}|minutes?|mins?|hours?|hrs?)\b', tail, re.I):
                return 'Please use a number such as “one” or “1”, rather than an indefinite phrase.'
        if question['unit'] != 'minutes' and re.search(r'\b(?:seconds?|minutes?|mins?|hours?|hrs?|days?|weeks?)\b', text, re.I):
            return 'Please give a count of people, resources, or jobs, without a time unit.'
        tail = text[amounts[0].end():].strip(' .,!?')
        if question['unit'] == 'minutes' and tail and not re.match(r'(?:minutes?|mins?|hours?|hrs?|each|per|for)\b', tail, re.I):
            return 'Please give a total in minutes or hours, or a bare number of minutes.'
        value = _number(amounts[0].group())
        if question['unit'] == 'minutes' and re.search(r'\b(?:hours?|hrs?)\b', text, re.I):
            value *= 60
        if value != int(value) or not question['min'] <= value <= question['max']:
            return f"Please use a whole number from {question['min']} to {question['max']} {question['unit']}."
        if key == 'staff':
            label = _ROLE_RE.search(text)
            slot = self.resource(label['label'].lower() if label else 'people')['count']
        else:
            slot = next(s for s in self.slots() if s.id == key)
        slot.answer = int(value)
        slot.answer_source = text
        return None

    def known(self):
        result = []
        for slot in self.slots():
            if slot.value is not None:
                label = 'Time available' if slot.id == 'horizon' else slot.label
                for resource in self.resources:
                    if slot is resource['count']:
                        label = 'Available ' + resource['label']
                for group in self.groups:
                    if slot is group['count']:
                        label = group['label'].capitalize() + ' to do'
                    elif slot is group['duration']:
                        label = 'Time per ' + group['label'] + ' job'
                    elif slot is group['due']:
                        label = 'Deadline for ' + group['label']
                result.append(dict(id=slot.id, label=label, value=f'{slot.value} {slot.unit}', source=slot.answer_source or slot.claims[0]['text']))
        for group in self.groups:
            if group['after']:
                names = [g['label'] for g in self.groups if g['id'] in group['after']]
                result.append(dict(id=f"after-{group['id']}", label=f"Before {group['label']}", value='Finish all ' + ', '.join(names), source=next((f['text'] for f in self.facts if f"tasks.{group['id']}.depends_on" in f['targets']), 'Provided ordering')))
            if group['resource']:
                result.append(dict(id=f"role-{group['id']}", label=f"Who does {group['label']}", value=next(r['label'] for r in self.resources if r['id'] == group['resource']), source=group['resource_source']))
        return result

    def build(self):
        assumptions = [
            dict(field='scope', value='simplified workflow only', reason='Explicitly accepted in the conversation.'),
            dict(field='excluded_details', value=self.unmodeled, reason='Shown at scope confirmation; these statements are not modeled.'),
            dict(field='processing', value='checkpointable', reason='Accepted scope: completed work is retained when a job pauses.'),
            dict(field='tasks.units', value=1, reason='Accepted scope: one person or resource unit per job.'),
            dict(field='tasks.release', value=0, reason='Accepted scope: all work available from the start.'),
            dict(field='tasks.priority/value', value=1, reason='Accepted scope: jobs have equal importance and equal completion value.'),
            dict(field='tasks.unspecified_due', value=self.horizon.value, reason='Accepted scope: unspecified deadlines are the end of the session.'),
            dict(field='tasks.depends_on', value='only explicitly shown group ordering', reason='Accepted scope: groups without ordering can run independently; all jobs of a predecessor group must finish.'),
            dict(field='stock/tasks.materials', value={}, reason='Accepted scope: stock and material constraints are excluded.'),
            dict(field='resources.cost_per_minute/budget_cents', value='0 / no budget', reason='Accepted scope: costs and budgets are excluded; cost comparisons are consequently ties.'),
            dict(field='events', value=[], reason='Accepted scope: no disruptions before a user adds one in the simulation.'),
        ]
        resources = [dict(id=r['id'], label=r['label'], capacity=r['count'].value, skills=[], cost_per_minute=0) for r in self.resources]
        tasks = []
        for group in self.groups:
            selected = group['resource'] or self.resources[0]['id']
            for resource in resources:
                if resource['id'] == selected:
                    resource['skills'].append(group['id'])
            deps = [f"{g['id']}_{i + 1}" for g in self.groups if g['id'] in group['after'] for i in range(g['count'].value)]
            for i in range(group['count'].value):
                tasks.append(dict(id=f"{group['id']}_{i + 1}", label=f"{group['label']} {i + 1}", duration=group['duration'].value, skill=group['id'], units=1, release=0, due=group['due'].value if group['due'].value is not None else self.horizon.value, priority=1, value=1, depends_on=deps, materials={}))
        # Unassigned pools are retained and visibly idle, not silently discarded.
        for resource in resources:
            if not resource['skills']:
                resource['skills'] = ['unassigned']
        raw = dict(schema_version='fork-workflow/1', title=' and '.join(g['label'] for g in self.groups).capitalize()[:200], horizon=self.horizon.value, resources=resources, tasks=tasks, stock={}, budget_cents=None, events=[])
        return validate_model(raw), assumptions


def intake(brief: str, answers: list[dict] | None = None) -> dict:
    """Recompute the full interview; only the accepted prefix may affect a model."""
    issues = []
    valid_brief = isinstance(brief, str) and len(brief) <= 30000
    source = brief if valid_brief else ''
    brief_hash = _digest(source)
    result = dict(compiler='deterministic-dialogue-v1', ready=False, model=None, model_hash=None,
                  issues=issues, assumptions=[], facts=[], summary='', questions=[], known=[], accepted_answers=[],
                  brief_hash=brief_hash, scope_note=_SCOPE_NOTE)
    def error(code, message):
        issues.append(dict(severity='error', code=code, message=message, line=None))
    if not valid_brief:
        error('brief_size', 'Describe the issue in text, using at most 30,000 characters.')
        return result
    if answers is None:
        answers = []
    if not isinstance(answers, list) or len(answers) > 100:
        error('answers_size', 'Use at most 100 conversation answers.')
        return result
    interview = Interview(source)
    accepted = result['accepted_answers']
    def next_question():
        question = interview.next()
        if question:
            question['id'] = f"{brief_hash[:16]}:{_digest(accepted)[:12]}:{question['key']}"
        return question
    for entry in answers:
        question = next_question()
        if not isinstance(entry, dict) or set(entry) != {'question_id', 'answer'} or not isinstance(entry.get('question_id'), str) or not isinstance(entry.get('answer'), str) or not 1 <= len(entry['answer'].strip()) <= 2000:
            error('answer_format', 'Each answer needs its question ID and 1–2,000 characters of text.')
            break
        if not question or entry['question_id'] != question['id']:
            error('stale_answer', 'This answer belongs to an earlier question or description. Continue from the current question.')
            break
        candidate = copy.deepcopy(interview)
        failure = candidate.apply(question, entry['answer'])
        if failure:
            error('invalid_answer', failure)
            break
        interview = candidate
        accepted.append(dict(entry))
    question = next_question()
    result['facts'], result['known'] = interview.facts, interview.known()
    result['summary'] = (f"I have {len(interview.groups)} group{'s' if len(interview.groups) != 1 else ''} of work to plan. "
                         + ('One detail to clarify next.' if question else 'The agreed scope is ready for review.'))
    if question:
        result['questions'] = [{k: v for k, v in question.items() if k != 'key'}]
    elif not issues:
        try:
            model, assumptions = interview.build()
            result.update(ready=True, model=model, model_hash=model_hash(model), assumptions=assumptions, summary=describe_model(model))
        except (ValueError, TypeError) as exc:
            result['summary'] = 'These facts need a correction before this scenario can run. Edit the original description.'
            error('model_validation', 'The agreed facts cannot form a valid bounded workflow. Check job totals (maximum 80), people/resources (maximum 12 pools), time limits and circular ordering. ' + str(exc))
    return result


def describe_model(model: dict) -> str:
    """Readable legacy model summary without exposing line grammar as authoring."""
    resources = ', '.join(f"{r['capacity']} {r['label']}" for r in model.get('resources', []))
    tasks = model.get('tasks', [])
    durations = sorted({t['duration'] for t in tasks})
    duration = f"{durations[0]}" if len(durations) == 1 else (f'{durations[0]}–{durations[-1]}' if durations else 'unknown')
    return f"{model.get('title', 'Planning scenario')}: {len(tasks)} jobs, taking {duration} minutes each, with {resources}. The planning window is {model.get('horizon', '?')} minutes. This is a synthetic, checkpointable-work simulation."
