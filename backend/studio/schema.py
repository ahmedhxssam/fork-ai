"""Strict data boundary for the generic minute-discrete workflow engine."""
from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Slug = Annotated[str, Field(pattern=r'^[a-zA-Z][a-zA-Z0-9_-]{0,47}$')]
Label = Annotated[str, Field(min_length=1, max_length=200)]
Positive = Annotated[int, Field(strict=True, ge=1)]
Nonnegative = Annotated[int, Field(strict=True, ge=0)]
Minute = Annotated[int, Field(strict=True, ge=0, le=720)]
Duration = Annotated[int, Field(strict=True, ge=1, le=720)]
Units = Annotated[int, Field(strict=True, ge=1, le=12)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Resource(StrictModel):
    id: Slug
    label: Label
    capacity: Units
    skills: Annotated[list[Slug], Field(min_length=1, max_length=80)]
    cost_per_minute: Annotated[int, Field(ge=0, le=10000)]


class Task(StrictModel):
    id: Slug
    label: Label
    duration: Duration
    skill: Slug
    units: Units
    release: Minute
    due: Minute
    priority: Annotated[int, Field(ge=1, le=3)]
    value: Annotated[int, Field(ge=1, le=1000)]
    depends_on: Annotated[list[Slug], Field(max_length=80)]
    materials: dict[Slug, Positive]


class Event(StrictModel):
    id: Slug
    kind: Literal['resource_outage']
    resource_id: Slug
    at: Minute
    duration: Duration
    capacity_lost: Units
    label: Label


class Model(StrictModel):
    schema_version: Literal['fork-workflow/1']
    title: Label
    horizon: Duration
    resources: Annotated[list[Resource], Field(min_length=1, max_length=12)]
    tasks: Annotated[list[Task], Field(min_length=1, max_length=80)]
    stock: dict[Slug, Nonnegative]
    budget_cents: Nonnegative | None
    events: Annotated[list[Event], Field(max_length=12)]

    @model_validator(mode='after')
    def cross_references(self):
        for label, rows in [('resources', self.resources), ('tasks', self.tasks), ('events', self.events)]:
            ids = [row.id for row in rows]
            if len(ids) != len(set(ids)):
                raise ValueError(f'{label}: IDs must be unique')
        if len(self.stock) > 12:
            raise ValueError('stock: at most 12 material types')
        resources = {r.id: r for r in self.resources}
        tasks = {t.id: t for t in self.tasks}
        for r in self.resources:
            if len(r.skills) != len(set(r.skills)):
                raise ValueError(f'resource {r.id}: duplicate skills')
        for t in self.tasks:
            if not 0 <= t.release <= t.due <= self.horizon:
                raise ValueError(f'task {t.id}: require 0 <= release <= due <= horizon')
            if t.duration > self.horizon:
                raise ValueError(f'task {t.id}: duration exceeds horizon')
            if not any(t.skill in r.skills and t.units <= r.capacity for r in self.resources):
                raise ValueError(f'task {t.id}: no compatible resource with sufficient capacity')
            if len(t.depends_on) != len(set(t.depends_on)):
                raise ValueError(f'task {t.id}: duplicate dependencies')
            if any(d not in tasks for d in t.depends_on):
                raise ValueError(f'task {t.id}: unknown dependency')
            if any(s not in self.stock for s in t.materials):
                raise ValueError(f'task {t.id}: unknown material')
        visiting, visited = set(), set()
        def visit(id):
            if id in visiting:
                raise ValueError(f'dependency cycle involving {id}')
            if id in visited:
                return
            visiting.add(id)
            for dependency in tasks[id].depends_on:
                visit(dependency)
            visiting.remove(id)
            visited.add(id)
        for id in tasks:
            visit(id)
        for e in self.events:
            if e.resource_id not in resources:
                raise ValueError(f'event {e.id}: unknown resource')
            if e.at >= self.horizon:
                raise ValueError(f'event {e.id}: start must be before horizon')
            if e.capacity_lost > resources[e.resource_id].capacity:
                raise ValueError(f'event {e.id}: lost capacity exceeds resource capacity')
        return self


def validate_model(raw: dict) -> dict:
    """Return a detached, normalized model; reject coercion and unknown fields."""
    try:
        return Model.model_validate(raw).model_dump(mode='json')
    except (ValueError, TypeError) as exc:
        raise ValueError(str(exc)) from exc


def model_hash(model: dict) -> str:
    return hashlib.sha256(json.dumps(model, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def model_schema() -> dict:
    return Model.model_json_schema()
