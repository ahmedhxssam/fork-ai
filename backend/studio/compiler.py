"""Bounded brief grammar; no open-ended language inference or executable code.

One statement per line (keywords case insensitive). Blank lines and # comments
are ignored. Title: and Note: explicitly identify non-operative narrative.

Title: Repair clinic
Horizon: 60 [minutes]
Budget: 1000 [cents] | none
Stock: parts=4 batteries=2
Resource bench label="Repair bench" capacity=2 skills=repair,test cost=3
Task repair label="Repair radio" duration=10 skill=repair units=1 release=0
    due=40 priority=3 value=10 after=inspect materials=parts:1,batteries:1
(The task above must occupy ONE line; optional fields may be omitted.)
Outage break resource=bench at=10 duration=5 lost=1 label="Bench outage"

The following bounded natural-style forms are also supported:
Resource bench has capacity 2, skills repair,test, and costs 3 cents per minute.
Task repair takes 10 minutes using skill repair.
Resource bench: Repair bench has capacity 2, skills repair, and costs 3 cents per minute.
Task repair: Repair the radio takes 10 minutes using skill repair; needs 1 unit; available at 0; due by 40; priority 3; value 10; after inspect; consumes 1 parts.

Semicolon clauses are optional, may be reordered, and must each occur at most
once. after accepts comma-separated IDs or none; consumes accepts comma-separated
QUANTITY MATERIAL pairs or none. Labeled sentences preserve their readable label.

All optional-field defaults are listed in assumptions. Every nonempty unknown
line or attribute blocks compilation. All times are integer minutes from zero;
costs are integer cents per resource-unit minute. '-' denotes an empty list/map.
"""
from __future__ import annotations

import re
import shlex

from .schema import model_hash, validate_model

GRAMMAR = __doc__
TEMPLATES = [
    dict(id='repair-clinic', title='Community repair clinic', subtitle='Shared benches, parts, inspection and urgent repairs', brief='''Title: Community repair clinic
Note: Synthetic repair queue; work is checkpointable and travel is not modeled.
Horizon: 90 minutes
Budget: 1000 cents
Stock: parts=5
Resource bench: Repair benches has capacity 2, skills repair, and costs 3 cents per minute.
Resource tester: Test station has capacity 1, skills test, and costs 2 cents per minute.
Task triage: Inspect donated radios takes 8 minutes using skill repair; needs 1 unit; available at 0; due by 15; priority 2; value 3; after none; consumes none.
Task radio: Repair emergency radio takes 24 minutes using skill repair; needs 1 unit; available at 0; due by 40; priority 3; value 12; after triage; consumes 2 parts.
Task lamp: Repair desk lamp takes 10 minutes using skill repair; needs 1 unit; available at 0; due by 30; priority 1; value 4; after triage; consumes 1 parts.
Task fan: Repair cooling fan takes 18 minutes using skill repair; needs 1 unit; available at 0; due by 45; priority 3; value 8; after triage; consumes 2 parts.
Task test-radio: Safety test radio takes 9 minutes using skill test; needs 1 unit; available at 0; due by 50; priority 3; value 6; after radio; consumes none.
Task test-fan: Safety test fan takes 8 minutes using skill test; needs 1 unit; available at 0; due by 55; priority 3; value 5; after fan; consumes none.
Task test-lamp: Safety test lamp takes 6 minutes using skill test; needs 1 unit; available at 0; due by 40; priority 1; value 2; after lamp; consumes none.'''),
    dict(id='event-production', title='Community event production', subtitle='Crew contention, staging and sound checks', brief='''Title: Community event production
Note: Synthetic event preparation; setup work is checkpointable.
Horizon: 120 minutes
Budget: 1600 cents
Stock: rigging=4
Resource crew: Stage crew has capacity 2, skills stage, and costs 4 cents per minute.
Resource sound: Audio technician has capacity 1, skills audio, and costs 5 cents per minute.
Task unload: Unload equipment takes 10 minutes using skill stage; needs 2 units; available at 0; due by 15; priority 2; value 4; after none; consumes none.
Task platform: Build stage platform takes 25 minutes using skill stage; needs 2 units; available at 0; due by 40; priority 3; value 12; after unload; consumes 2 rigging.
Task banners: Hang banners takes 12 minutes using skill stage; needs 1 unit; available at 0; due by 35; priority 1; value 3; after unload; consumes 1 rigging.
Task lights: Rig lights takes 20 minutes using skill stage; needs 1 unit; available at 0; due by 60; priority 2; value 7; after platform; consumes 1 rigging.
Task microphones: Configure microphones takes 18 minutes using skill audio; needs 1 unit; available at 0; due by 45; priority 3; value 9; after unload; consumes none.
Task soundcheck: Main stage soundcheck takes 15 minutes using skill audio; needs 1 unit; available at 0; due by 65; priority 3; value 10; after platform,microphones; consumes none.'''),
    dict(id='it-response', title='IT service response', subtitle='Service restoration, specialist capacity and dependencies', brief='''Title: IT service response
Note: Synthetic service tasks; no actual systems are accessed.
Horizon: 80 minutes
Budget: 1800 cents
Stock: licenses=2
Resource ops: Operations team has capacity 2, skills ops, and costs 6 cents per minute.
Resource security: Security specialist has capacity 1, skills security, and costs 8 cents per minute.
Task diagnose: Diagnose incident takes 8 minutes using skill ops; needs 1 unit; available at 0; due by 10; priority 3; value 6; after none; consumes none.
Task restore: Restore customer service takes 22 minutes using skill ops; needs 2 units; available at 0; due by 35; priority 3; value 15; after diagnose; consumes 1 licenses.
Task dashboard: Repair internal dashboard takes 10 minutes using skill ops; needs 1 unit; available at 0; due by 28; priority 1; value 4; after diagnose; consumes none.
Task audit: Audit compromised access takes 18 minutes using skill security; needs 1 unit; available at 0; due by 30; priority 3; value 9; after diagnose; consumes none.
Task rotate: Rotate service credentials takes 12 minutes using skill security; needs 1 unit; available at 0; due by 45; priority 3; value 8; after audit; consumes 1 licenses.
Task validate: Validate restored service takes 10 minutes using skill ops; needs 1 unit; available at 0; due by 50; priority 3; value 10; after restore,rotate; consumes none.'''),
]


def compile_brief(brief: str) -> dict:
    issues, assumptions, facts = [], [], []
    raw = dict(schema_version='fork-workflow/1', resources=[], tasks=[], stock={}, events=[])
    seen = set()
    def issue(code, message, line=None):
        issues.append(dict(severity='error', code=code, message=message, line=line))
    def default(field, value, reason='Not specified in the brief; deterministic default.'):
        assumptions.append(dict(field=field, value=value, reason=reason))
        return value
    if not isinstance(brief, str) or len(brief) > 50000:
        issue('brief_size', 'Brief must be text of at most 50,000 characters.')
        brief = ''
    def number(value):
        if not re.fullmatch(r'-?\d+', value):
            raise ValueError(f'Expected integer, received {value!r}')
        return int(value)
    def mapping(value, separator):
        if value == '-':
            return {}
        result = {}
        for pair in value.split(','):
            key, amount = pair.split(separator)
            if key in result:
                raise ValueError(f'Duplicate material {key}')
            result[key] = number(amount)
        return result
    for line_number, original in enumerate(brief.splitlines(), 1):
        line = original.strip()
        if not line or line.startswith('#'):
            continue
        targets = []
        try:
            header = re.fullmatch(r'(Title|Note|Horizon|Budget|Stock):\s*(.+)', line, re.I)
            if header:
                key, value = header.group(1).lower(), header.group(2).strip()
                if key != 'note' and key in seen:
                    raise ValueError(f'Duplicate {key} declaration')
                seen.add(key)
                if key == 'note':
                    targets = ['narrative']
                elif key == 'title':
                    raw['title'] = value
                    targets = ['title']
                elif key == 'horizon':
                    raw['horizon'] = number(re.sub(r'\s+minutes?$', '', value, flags=re.I))
                    targets = ['horizon']
                elif key == 'budget':
                    raw['budget_cents'] = None if value.lower() == 'none' else number(re.sub(r'\s+cents?$', '', value, flags=re.I))
                    targets = ['budget_cents']
                elif key == 'stock':
                    raw['stock'] = mapping(','.join(shlex.split(value)), '=')
                    targets = ['stock']
            else:
                natural_resource = re.fullmatch(r'Resource ([\w-]+)(?:: (.+?))? has capacity (\d+), skills ([\w,-]+), and costs (\d+) cents? per minute\.', line, re.I)
                natural_task = re.fullmatch(r'Task ([\w-]+)(?:: (.+?))? takes (\d+) minutes? using skill ([\w-]+)((?:;[^\n]*)?)\.', line, re.I)
                if natural_resource:
                    id, label, capacity, skills, cost = natural_resource.groups()
                    line = f'Resource {id} capacity={capacity} skills={skills} cost={cost}'
                    if label is not None:
                        line += ' label=' + shlex.quote(label)
                if natural_task:
                    id, label, duration, skill, clauses = natural_task.groups()
                    line = f'Task {id} duration={duration} skill={skill}'
                    if label is not None:
                        line += ' label=' + shlex.quote(label)
                    for clause in clauses.split(';')[1:]:
                        clause = clause.strip()
                        patterns = [('units', r'needs (\d+) units?'), ('release', r'available at (\d+)'),
                                    ('due', r'due by (\d+)'), ('priority', r'priority (\d+)'),
                                    ('value', r'value (\d+)'), ('after', r'after (none|[\w,-]+)'),
                                    ('materials', r'consumes (.+)')]
                        for key, pattern in patterns:
                            match = re.fullmatch(pattern, clause, re.I)
                            if match:
                                value = match.group(1)
                                if key in {'after', 'materials'} and value.lower() == 'none':
                                    value = '-'
                                elif key == 'materials':
                                    pairs = []
                                    for pair in value.split(','):
                                        amount = re.fullmatch(r'\s*(\d+) ([\w-]+)\s*', pair)
                                        if not amount:
                                            raise ValueError('Materials clause must contain quantity and material ID, e.g. consumes 2 parts.')
                                        pairs.append(amount.group(2) + ':' + amount.group(1))
                                    value = ','.join(pairs)
                                line += ' ' + key + '=' + shlex.quote(value)
                                break
                        else:
                            raise ValueError(f'Unsupported task clause: {clause}')
                tokens = shlex.split(line)
                if len(tokens) < 2 or tokens[0].lower() not in {'resource', 'task', 'outage'}:
                    raise ValueError('Unsupported statement. Use the documented line grammar; no requested constraint is inferred.')
                kind, id, *attributes = tokens
                kind = kind.lower()
                fields = {}
                for attribute in attributes:
                    key, value = attribute.split('=', 1)
                    if key in fields:
                        raise ValueError(f'Duplicate attribute {key}')
                    fields[key] = value
                allowed = {'resource': {'label', 'capacity', 'skills', 'cost'},
                           'task': {'label', 'duration', 'skill', 'units', 'release', 'due', 'priority', 'value', 'after', 'materials'},
                           'outage': {'resource', 'at', 'duration', 'lost', 'label'}}[kind]
                unknown = fields.keys() - allowed
                if unknown:
                    raise ValueError('Unsupported attribute(s): ' + ', '.join(sorted(unknown)))
                required = {'resource': {'skills'}, 'task': {'duration', 'skill'}, 'outage': {'resource', 'at', 'duration', 'lost'}}[kind]
                if required - fields.keys():
                    raise ValueError('Missing attribute(s): ' + ', '.join(sorted(required - fields.keys())))
                group = {'resource': 'resources', 'task': 'tasks', 'outage': 'events'}[kind]
                def get(key, fallback, field=None):
                    return fields[key] if key in fields else default(f'{group}.{id}.{field or key}', fallback)
                row = dict(id=id, label=get('label', id))
                if kind == 'resource':
                    row.update(capacity=number(str(get('capacity', 1))), skills=fields['skills'].split(','), cost_per_minute=number(str(get('cost', 0, 'cost_per_minute'))))
                elif kind == 'task':
                    row.update(duration=number(fields['duration']), skill=fields['skill'])
                    for key, fallback in [('units', 1), ('release', 0), ('priority', 1), ('value', 1)]:
                        row[key] = number(str(get(key, fallback)))
                    # Resolve omitted due after reading the whole brief, so statement order is immaterial.
                    row['due'] = number(fields['due']) if 'due' in fields else None
                    deps = fields.get('after')
                    row['depends_on'] = ([] if deps == '-' else deps.split(',')) if deps is not None else default(f'tasks.{id}.depends_on', [])
                    row['materials'] = mapping(fields['materials'], ':') if 'materials' in fields else default(f'tasks.{id}.materials', {})
                else:
                    row.update(kind='resource_outage', resource_id=fields['resource'], at=number(fields['at']), duration=number(fields['duration']), capacity_lost=number(fields['lost']))
                raw[group].append(row)
                targets = [f'{group}.{id}']
            facts.append(dict(line=line_number, text=original, targets=targets))
        except (ValueError, TypeError) as exc:
            issue('unsupported_or_malformed', str(exc), line_number)
    for field, fallback in [('title', 'Untitled workflow'), ('horizon', 120), ('budget_cents', None)]:
        if field not in raw:
            raw[field] = default(field, fallback)
    if 'stock' not in seen:
        default('stock', {})
    if not raw['events']:
        default('events', [])
    default('processing', 'checkpointable', 'Explicit engine assumption: completed work survives outages; one pool is retained after first start.')
    default('cost_basis', 'resource-unit minutes', 'Cost is charged for actual work only; no fixed costs, travel or human behavior inferred.')
    for row in raw['tasks']:
        if row['due'] is None:
            row['due'] = default(f"tasks.{row['id']}.due", raw['horizon'], 'No deadline specified; use the planning horizon.')
    normalized = None
    try:
        normalized = validate_model(raw)
    except ValueError as exc:
        issue('invalid_model', str(exc))
    ready = normalized is not None and not issues
    return dict(compiler='deterministic-v1', ready=ready, model=normalized if ready else None,
                model_hash=model_hash(normalized) if ready else None,
                issues=issues, assumptions=assumptions, facts=facts)
