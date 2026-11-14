"""Hand-derived workflow receipts, independent of scheduler/schema fixtures."""
import copy
import hashlib
import json

import pytest

from backend.studio.referee import verify


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def fixture():
    model = {
        "schema_version": "fork-workflow/1", "title": "Hand derived", "horizon": 8,
        "resources": [{"id": "bench", "label": "Bench", "capacity": 2,
                       "skills": ["repair"], "cost_per_minute": 7}],
        "tasks": [
            {"id": "a", "label": "A", "duration": 3, "skill": "repair", "units": 2,
             "release": 0, "due": 4, "priority": 3, "value": 8, "depends_on": [], "materials": {"part": 1}},
            {"id": "b", "label": "B", "duration": 2, "skill": "repair", "units": 1,
             "release": 1, "due": 7, "priority": 1, "value": 3, "depends_on": ["a"], "materials": {"part": 1}},
        ], "stock": {"part": 2}, "budget_cents": 60,
        "events": [{"id": "off", "kind": "resource_outage", "resource_id": "bench", "at": 1,
                    "duration": 2, "capacity_lost": 1, "label": "Reduced bench"}],
    }
    # A works [0,1), pauses [1,3), then works [3,5); B follows [5,7).
    # Work=5 elapsed task minutes; cost=(3*2+2*1)*7=56; A is late.
    result = {
        "id": "throughput", "name": "Throughput", "policy": "throughput",
        "model_hash": digest(model), "adapt": True,
        "segments": [{"task_id": "a", "resource_id": "bench", "start": 0, "end": 1, "units": 2},
                     {"task_id": "a", "resource_id": "bench", "start": 3, "end": 5, "units": 2},
                     {"task_id": "b", "resource_id": "bench", "start": 5, "end": 7, "units": 1}],
        "completions": [{"task_id": "a", "time": 5}, {"task_id": "b", "time": 7}],
        "events": [],
        "metrics": {"completed": 2, "total": 2, "on_time": 1, "priority_on_time": 0,
                    "priority_total": 1, "value_completed": 11, "value_total": 11,
                    "cost_cents": 56, "work_minutes": 5, "unserved": 0, "makespan": 7},
    }
    return model, result


def test_hand_derived_checkpoint_work_and_metrics():
    model, result = fixture()
    receipt = verify(model, result)
    assert receipt["valid"], receipt["violations"]
    assert receipt["metrics"] == result["metrics"]
    assert all(check["passed"] for check in receipt["checks"])
    assert receipt["evidence_hash"] == verify(copy.deepcopy(model), copy.deepcopy(result))["evidence_hash"]


def test_receipt_digest_ignores_attached_api_metadata():
    model, result = fixture()
    receipt = verify(model, result)
    result.update(verification=receipt, compute_seconds=0.123)
    assert verify(model, result)["evidence_hash"] == receipt["evidence_hash"]


def test_noncanonical_required_evidence_cannot_receive_valid_digest():
    model, result = fixture()
    result["events"] = [{"time": 0, "kind": "task_started", "summary": "Started", "extra": float("nan")}]
    assert not verify(model, result)["valid"]


def test_partial_work_without_completion_is_counted_and_material_is_debited():
    model, result = fixture()
    result["segments"] = result["segments"][:1]
    result["completions"] = []
    result["metrics"].update(completed=0, on_time=0, value_completed=0, cost_cents=14,
                            work_minutes=1, unserved=2, makespan=1)
    assert verify(model, result)["valid"]
    model["stock"]["part"] = 0
    result["model_hash"] = digest(model)
    assert not verify(model, result)["valid"]


@pytest.mark.parametrize("mutation", [
    lambda m, r: r["segments"][0].update(task_id="phantom"),
    lambda m, r: r["segments"][0].update(resource_id="phantom"),
    lambda m, r: r["segments"][0].update(units=1),
    lambda m, r: r["segments"][0].update(start=1, end=2),
    lambda m, r: r["segments"][1].update(start=0, end=2),
    lambda m, r: r["segments"][2].update(start=4, end=6),
    lambda m, r: r["completions"][0].update(time=4),
    lambda m, r: r["completions"].pop(),
    lambda m, r: r["completions"].append({"task_id": "a", "time": 5}),
    lambda m, r: r["segments"][1].update(end=6),
    lambda m, r: r["metrics"].update(cost_cents=1),
    lambda m, r: r["metrics"].update(completed=1),
    lambda m, r: r.update(model_hash="0" * 64),
    lambda m, r: r.update(adapt=1),
    lambda m, r: r["segments"][0].update(start=False),
    lambda m, r: r["metrics"].update(completed=True),
    lambda m, r: r.update(events=[{"time": 99, "kind": "work", "summary": "bad"}]),
])
def test_tampered_evidence_fails(mutation):
    model, result = fixture()
    mutation(model, result)
    receipt = verify(model, result)
    assert not receipt["valid"]
    assert receipt["violations"]


@pytest.mark.parametrize("mutation", [
    lambda m: m["stock"].update(part=1),
    lambda m: m.update(budget_cents=55),
    lambda m: m["tasks"][0].update(release=1),
    lambda m: m["resources"][0].update(skills=["other"]),
    lambda m: m["tasks"][0].update(duration=4),
    lambda m: m["tasks"][0].update(depends_on=["b"]),
    lambda m: m["tasks"][0].update(depends_on=["missing"]),
    lambda m: m["tasks"][0].update(materials={"missing": 1}),
    lambda m: m["events"][0].update(capacity_lost=3),
    lambda m: m["events"][0].update(kind="random_arrival"),
    lambda m: m["resources"].append(copy.deepcopy(m["resources"][0])),
    lambda m: m["tasks"][0].update(duration=True),
    lambda m: m.update(horizon=721),
])
def test_independent_model_and_constraints_validation(mutation):
    model, result = fixture()
    mutation(model)
    result["model_hash"] = digest(model)
    assert not verify(model, result)["valid"]


def test_counterfactual_schedule_binds_evidence_not_configured_model_hash():
    model, result = fixture()
    nominal = copy.deepcopy(result)
    nominal["segments"] = [{"task_id": "a", "resource_id": "bench", "start": 0, "end": 3, "units": 2},
                           {"task_id": "b", "resource_id": "bench", "start": 3, "end": 5, "units": 1}]
    nominal["completions"] = [{"task_id": "a", "time": 3}, {"task_id": "b", "time": 5}]
    nominal["metrics"].update(on_time=2, priority_on_time=1, makespan=5)
    assert verify(model, nominal, events=[])["valid"]
    assert not verify(model, nominal)["valid"]
    assert verify(model, result)["evidence_hash"] != verify(model, result, events=[])["evidence_hash"]


def test_partial_unserved_task_consumes_material_and_budget_only_once():
    model, result = fixture()
    model["stock"]["part"] = 1
    model["budget_cents"] = 42
    result["model_hash"] = digest(model)
    result["segments"] = result["segments"][:2]
    result["completions"] = result["completions"][:1]
    result["metrics"].update(completed=1, on_time=0, value_completed=8, cost_cents=42,
                            work_minutes=3, unserved=1, makespan=5)
    assert verify(model, result)["valid"]
    result["segments"].append({"task_id": "b", "resource_id": "bench", "start": 5, "end": 6, "units": 1})
    result["metrics"].update(cost_cents=49, work_minutes=4, makespan=6)
    assert not verify(model, result)["valid"]  # first start still debits stock and budget


def test_overlapping_outage_losses_capped_and_task_pool_retained():
    model, result = fixture()
    model["events"].append({"id": "off2", "kind": "resource_outage", "resource_id": "bench", "at": 1,
                            "duration": 1, "capacity_lost": 2, "label": "Other loss"})
    result["model_hash"] = digest(model)
    assert verify(model, result)["valid"]
    model["resources"].append(dict(model["resources"][0], id="other"))
    result["model_hash"] = digest(model)
    result["segments"][1]["resource_id"] = "other"
    assert not verify(model, result)["valid"]


def test_capacity_is_pool_wide_and_release_is_hard():
    model, result = fixture()
    model["tasks"][1]["depends_on"] = []
    model["tasks"][1]["release"] = 0
    result["model_hash"] = digest(model)
    result["segments"][2].update(start=3, end=5)
    result["completions"][1]["time"] = 5
    result["metrics"]["makespan"] = 5
    assert not verify(model, result)["valid"]


def test_release_at_horizon_is_valid_unserved_demand():
    model, result = fixture()
    model["tasks"][1].update(release=8, due=8)
    result["model_hash"] = digest(model)
    result["segments"] = result["segments"][:2]
    result["completions"] = result["completions"][:1]
    result["metrics"].update(completed=1, on_time=0, value_completed=8, cost_cents=42,
                            work_minutes=3, unserved=1, makespan=5)
    assert verify(model, result)["valid"]


@pytest.mark.parametrize("mutation", [
    lambda m: m["tasks"][0].update(duration=9),
    lambda m: m["tasks"][0].update(id="1numeric"),
    lambda m: m["resources"][0].update(skills=["not a slug"]),
    lambda m: m.update(title="x" * 201),
])
def test_malformed_schema_boundaries_rejected_even_without_work(mutation):
    model, result = fixture()
    mutation(model)
    result["model_hash"] = digest(model)
    result.update(segments=[], completions=[])
    result["metrics"].update(completed=0, on_time=0, value_completed=0, cost_cents=0,
                            work_minutes=0, unserved=2, makespan=0)
    assert not verify(model, result)["valid"]


@pytest.mark.parametrize("bad", [None, [], {}, {"horizon": float("nan")}])
def test_malformed_inputs_produce_invalid_receipt_without_throwing(bad):
    model, result = fixture()
    assert not verify(bad, result)["valid"]
    assert not verify(model, bad)["valid"]


def test_invalid_model_does_not_claim_unexecuted_replay_checks_passed():
    _, result = fixture()
    receipt = verify({}, result)
    assert not any(check["passed"] for check in receipt["checks"])
