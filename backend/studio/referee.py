"""Independent, standard-library replay of bounded workflow work evidence.

No planner, compiler, schema or simulation helpers are used here. The receipt
certifies this declared minute/capacity model, not schedule optimality or reality.
"""
from collections import defaultdict
import hashlib
import json
import re


_METRICS = ("completed", "total", "on_time", "priority_on_time", "priority_total",
            "value_completed", "value_total", "cost_cents", "work_minutes", "unserved", "makespan")
_SLUG = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,47}$")
_RESULT_FIELDS = {"id", "name", "policy", "model_hash", "adapt", "segments", "completions", "events", "metrics"}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def _integer(value, low, high=None):
    return type(value) is int and value >= low and (high is None or value <= high)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _label(value):
    return isinstance(value, str) and 1 <= len(value) <= 200


def _slug(value):
    return isinstance(value, str) and _SLUG.fullmatch(value) is not None


def _fields(value, keys, context):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError(f"{context}: expected fields {keys}")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _events(raw, resources, horizon):
    _require(isinstance(raw, list) and len(raw) <= 12, "events: expected at most 12 outages")
    identifiers = set()
    for event in raw:
        _fields(event, "id kind resource_id at duration capacity_lost label", "outage")
        _require(_slug(event["id"]) and event["id"] not in identifiers, "outage: invalid or duplicate id")
        identifiers.add(event["id"])
        _require(event["kind"] == "resource_outage", "outage: unsupported kind")
        rid = event["resource_id"]
        _require(isinstance(rid, str) and rid in resources, "outage: unknown resource")
        _require(_integer(event["at"], 0, horizon - 1), "outage: invalid start")
        _require(_integer(event["duration"], 1, 720), "outage: invalid duration")
        _require(_integer(event["capacity_lost"], 1, resources[rid]["capacity"]), "outage: invalid capacity loss")
        _require(_label(event["label"]), "outage: invalid label")
    return raw


def _model(raw):
    _fields(raw, "schema_version title horizon resources tasks stock budget_cents events", "model")
    _require(raw["schema_version"] == "fork-workflow/1", "model: unsupported schema version")
    _require(_label(raw["title"]), "model: invalid title")
    horizon = raw["horizon"]
    _require(_integer(horizon, 1, 720), "model: horizon must be integer 1..720")
    _require(isinstance(raw["resources"], list) and 1 <= len(raw["resources"]) <= 12, "model: expected 1..12 resources")
    resources = {}
    for resource in raw["resources"]:
        _fields(resource, "id label capacity skills cost_per_minute", "resource")
        rid = resource["id"]
        _require(_slug(rid) and rid not in resources, "resource: invalid or duplicate id")
        _require(_label(resource["label"]), "resource: invalid label")
        _require(_integer(resource["capacity"], 1, 12), "resource: invalid capacity")
        _require(_integer(resource["cost_per_minute"], 0, 10000), "resource: invalid cost")
        skills = resource["skills"]
        _require(isinstance(skills, list) and 1 <= len(skills) <= 80 and all(_slug(skill) for skill in skills), "resource: invalid skills")
        _require(len(skills) == len(set(skills)), "resource: duplicate skills")
        resources[rid] = resource
    stock = raw["stock"]
    _require(isinstance(stock, dict) and len(stock) <= 12, "model: invalid stock")
    _require(all(_slug(key) and _integer(value, 0) for key, value in stock.items()), "stock: invalid id or quantity")
    _require(raw["budget_cents"] is None or _integer(raw["budget_cents"], 0), "model: invalid budget")
    _require(isinstance(raw["tasks"], list) and 1 <= len(raw["tasks"]) <= 80, "model: expected 1..80 tasks")
    tasks = {}
    for task in raw["tasks"]:
        _fields(task, "id label duration skill units release due priority value depends_on materials", "task")
        tid = task["id"]
        _require(_slug(tid) and tid not in tasks, "task: invalid or duplicate id")
        _require(_label(task["label"]) and _slug(task["skill"]), "task: invalid label or skill")
        _require(_integer(task["duration"], 1, horizon) and _integer(task["units"], 1, 12), "task: invalid duration or units")
        _require(_integer(task["release"], 0, horizon), "task: invalid release")
        _require(_integer(task["due"], task["release"], horizon), "task: invalid due time")
        _require(_integer(task["priority"], 1, 3) and _integer(task["value"], 1, 1000), "task: invalid priority or value")
        dependencies = task["depends_on"]
        _require(isinstance(dependencies, list) and len(dependencies) <= 80 and all(_slug(dep) for dep in dependencies), "task: invalid dependencies")
        _require(len(dependencies) == len(set(dependencies)), "task: duplicate dependencies")
        materials = task["materials"]
        _require(isinstance(materials, dict) and all(key in stock and _integer(value, 1)
                                                  for key, value in materials.items()), "task: invalid material reference/quantity")
        _require(any(task["skill"] in resource["skills"] and task["units"] <= resource["capacity"]
                     for resource in resources.values()), "task: no compatible sufficient-capacity resource")
        tasks[tid] = task
    # Bounded independent DFS; planner graph utilities deliberately not imported.
    visited, active = set(), set()

    def visit(tid):
        _require(tid not in active, "task: dependency cycle")
        if tid in visited:
            return
        active.add(tid)
        for dependency in tasks[tid]["depends_on"]:
            _require(dependency in tasks, "task: unknown dependency")
            visit(dependency)
        active.remove(tid)
        visited.add(tid)

    for tid in tasks:
        visit(tid)
    _events(raw["events"], resources, horizon)
    return resources, tasks


def verify(model, result, events=None):
    """Replay actual work, recompute all metrics and return a fail-closed receipt.

    `events=None` uses configured outages; an explicit list (including []) is a
    counterfactual. Both the configured model and effective schedule are hashed.
    Narrated playback records do not establish any physical facts.
    """
    failures = defaultdict(list)
    labels = {
        "model": "Independent model validation", "hash": "Canonical model identity",
        "schedule": "Effective outage schedule", "structure": "Typed evidence fields",
        "work": "Task work and pool commitments", "capacity": "Minute capacity and outages",
        "precedence": "Release and dependency precedence", "completion": "Exact work and completions",
        "stock": "Materials debited once on first start", "budget": "Worked-unit cost and budget",
        "metrics": "Recomputed metric integrity",
    }
    metrics = dict.fromkeys(_METRICS, 0)
    replay_complete = False

    def fail(category, detail):
        if detail not in failures[category]:
            failures[category].append(detail)

    def receipt():
        # A malformed non-JSON object still gets a stable rejection digest. Such
        # receipts cannot be approved; no repr containing arbitrary objects is used.
        physical_result = {key: value for key, value in result.items() if key in _RESULT_FIELDS} if isinstance(result, dict) else result
        evidence = {"version": "fork-workflow-referee/1", "model": model, "result": physical_result,
                    "effective_events": model.get("events") if events is None and isinstance(model, dict) else events,
                    "recomputed_metrics": metrics}
        try:
            evidence_hash = _digest(evidence)
        except (ValueError, TypeError, OverflowError, RecursionError):
            fail("structure", "physical evidence cannot be canonically serialized as finite JSON")
            violations = [f"{key}: {detail}" for key in labels for detail in failures[key]]
            evidence_hash = _digest({"invalid": True, "violations": violations, "metrics": metrics})
        checks = [{"id": key, "label": label, "passed": replay_complete and not failures[key],
                   "detail": "; ".join(failures[key]) if failures[key] else
                   ("Passed independent replay checks" if replay_complete else "Full replay not completed after invalid input")}
                  for key, label in labels.items()]
        violations = [f"{key}: {detail}" for key in labels for detail in failures[key]]
        return {"valid": not violations, "checks": checks, "violations": violations,
                "metrics": metrics, "evidence_hash": evidence_hash}

    try:
        resources, tasks = _model(model)
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        fail("model", str(error))
        return receipt()
    horizon = model["horizon"]
    metrics.update(total=len(tasks), priority_total=sum(task["priority"] == 3 for task in tasks.values()),
                   value_total=sum(task["value"] for task in tasks.values()), unserved=len(tasks))
    try:
        effective_events = _events(model["events"] if events is None else events, resources, horizon)
    except (ValueError, TypeError, KeyError) as error:
        fail("schedule", str(error))
        return receipt()
    if not isinstance(result, dict):
        fail("structure", "result must be an object")
        return receipt()
    if not _RESULT_FIELDS <= result.keys():
        fail("structure", "result missing required fields")
        return receipt()
    if result["policy"] not in ("throughput", "resilience", "priority") or result["id"] != result["policy"]:
        fail("structure", "invalid or inconsistent policy/id")
    if not _text(result["name"]) or type(result["adapt"]) is not bool:
        fail("structure", "invalid name or adaptation flag")
    try:
        if result["model_hash"] != _digest(model):
            fail("hash", "result model_hash differs from configured canonical model")
    except (ValueError, TypeError, OverflowError, RecursionError):
        fail("hash", "configured model cannot be canonically serialized")
        return receipt()
    if not all(isinstance(result[key], list) for key in ("segments", "completions", "events")):
        fail("structure", "segments, completions and events must be arrays")
        return receipt()
    # Replay is bounded by the declared physical horizon and task count, even for
    # malicious segment evidence. Larger evidence cannot be a merged valid trace.
    if len(result["segments"]) > 80 * 720 or len(result["completions"]) > 80 or len(result["events"]) > 80 * 720 * 4:
        fail("structure", "evidence exceeds bounded model trace limits")
        return receipt()
    for event in result["events"]:
        if not isinstance(event, dict) or not {"time", "kind", "summary"} <= event.keys():
            fail("structure", "playback event missing typed fields")
            continue
        if not _integer(event["time"], 0, horizon) or not _text(event["kind"]) or not _text(event["summary"]):
            fail("structure", "playback event has invalid time/kind/summary")
        if "task_id" in event and (not isinstance(event["task_id"], str) or event["task_id"] not in tasks):
            fail("structure", "playback event references unknown task")
        if "resource_id" in event and (not isinstance(event["resource_id"], str) or event["resource_id"] not in resources):
            fail("structure", "playback event references unknown resource")
    available = {rid: [resource["capacity"]] * horizon for rid, resource in resources.items()}
    for event in effective_events:
        for minute in range(event["at"], min(horizon, event["at"] + event["duration"])):
            rid = event["resource_id"]
            available[rid][minute] = max(0, available[rid][minute] - event["capacity_lost"])
    usage = {rid: [0] * horizon for rid in resources}
    work = {tid: set() for tid in tasks}
    segments = defaultdict(list)
    pools = defaultdict(set)
    for segment in result["segments"]:
        try:
            _fields(segment, "task_id resource_id start end units", "segment")
            tid, rid = segment["task_id"], segment["resource_id"]
            _require(isinstance(tid, str) and tid in tasks and isinstance(rid, str) and rid in resources,
                     "segment: unknown task/resource")
            start, end, units = segment["start"], segment["end"], segment["units"]
            _require(_integer(start, 0, horizon - 1) and _integer(end, start + 1, horizon), "segment: invalid interval/horizon")
            _require(_integer(units, 1, 12) and units == tasks[tid]["units"], "segment: incorrect units")
        except (ValueError, TypeError, KeyError) as error:
            fail("structure", str(error))
            continue
        if tasks[tid]["skill"] not in resources[rid]["skills"]:
            fail("work", f"{tid}: incompatible resource skill")
        pools[tid].add(rid)
        segments[tid].append((start, end))
        for minute in range(start, end):
            if minute in work[tid]:
                fail("work", f"{tid}: overlapping task work")
            work[tid].add(minute)
            usage[rid][minute] += units
        metrics["work_minutes"] += end - start
        metrics["cost_cents"] += (end - start) * units * resources[rid]["cost_per_minute"]
        metrics["makespan"] = max(metrics["makespan"], end)
    for tid, intervals in segments.items():
        if len(pools[tid]) > 1:
            fail("work", f"{tid}: changed resource pool after first start")
        ordered = sorted(intervals)
        if any(previous[1] == current[0] for previous, current in zip(ordered, ordered[1:])):
            fail("work", f"{tid}: contiguous work must be merged")
    for rid in resources:
        for minute in range(horizon):
            if usage[rid][minute] > available[rid][minute]:
                fail("capacity", f"{rid}: capacity exceeded at minute {minute}")
    supplied_completions = {}
    for completion in result["completions"]:
        try:
            _fields(completion, "task_id time", "completion")
            tid = completion["task_id"]
            _require(isinstance(tid, str) and tid in tasks, "completion: unknown task")
            _require(_integer(completion["time"], 1, horizon), "completion: invalid time")
            _require(tid not in supplied_completions, "completion: duplicate task")
            supplied_completions[tid] = completion["time"]
        except (ValueError, TypeError, KeyError) as error:
            fail("completion", str(error))
    # Completions come only from required physical work, never claimed markers.
    completed = {}
    consumed = defaultdict(int)
    for tid, task in tasks.items():
        minutes = work[tid]
        if len(minutes) > task["duration"]:
            fail("completion", f"{tid}: exceeds required work")
        if len(minutes) == task["duration"]:
            completed[tid] = max(minutes) + 1
        if minutes:
            for stock_id, quantity in task["materials"].items():
                consumed[stock_id] += quantity
            if min(minutes) < task["release"]:
                fail("precedence", f"{tid}: work before release")
        if supplied_completions.get(tid) != completed.get(tid):
            fail("completion", f"{tid}: completion disagrees with exact required work")
    for tid, task in tasks.items():
        if work[tid]:
            for dependency in task["depends_on"]:
                if dependency not in completed or completed[dependency] > min(work[tid]):
                    fail("precedence", f"{tid}: dependency {dependency} incomplete at first work")
    for stock_id, quantity in consumed.items():
        if quantity > model["stock"][stock_id]:
            fail("stock", f"{stock_id}: first-start consumption {quantity} exceeds stock")
    if model["budget_cents"] is not None and metrics["cost_cents"] > model["budget_cents"]:
        fail("budget", "actual resource-unit work cost exceeds budget")
    metrics.update(completed=len(completed), unserved=len(tasks) - len(completed),
                   on_time=sum(time <= tasks[tid]["due"] for tid, time in completed.items()),
                   priority_on_time=sum(tasks[tid]["priority"] == 3 and time <= tasks[tid]["due"]
                                        for tid, time in completed.items()),
                   value_completed=sum(tasks[tid]["value"] for tid in completed))
    supplied = result["metrics"]
    if not isinstance(supplied, dict) or set(supplied) != set(_METRICS):
        fail("metrics", "supplied metrics have missing or unexpected fields")
    else:
        for key in _METRICS:
            if type(supplied[key]) is not int or supplied[key] != metrics[key]:
                fail("metrics", f"{key}: supplied value differs from independently recomputed {metrics[key]}")
    replay_complete = True
    return receipt()
