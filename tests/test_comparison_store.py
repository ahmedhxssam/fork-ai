import copy

import pytest


def worlds():
    return [
        {"id": "velocity", "name": "Velocity", "verification": {"valid": True, "metrics": {
            "on_time_coverage": .9, "priority_coverage": .3, "cost_cents": 2000,
            "meals_delivered": 220, "priority_weighted_coverage": .6}}},
        {"id": "equity", "name": "Equity", "verification": {"valid": True, "metrics": {
            "on_time_coverage": .7, "priority_coverage": 1., "cost_cents": 5000,
            "meals_delivered": 190, "priority_weighted_coverage": .9}}},
    ]


def test_preferences_change_recommendation_without_changing_outcomes():
    from backend.comparison import compare_worlds
    data = worlds()
    before = copy.deepcopy(data)
    assert compare_worlds(data, {"coverage": 1, "equity": 0, "cost": 0})["recommended_id"] == "velocity"
    assert compare_worlds(data, {"coverage": 0, "equity": 1, "cost": 0})["recommended_id"] == "equity"
    assert data == before


def test_invalid_world_cannot_win_even_with_better_reported_metrics():
    from backend.comparison import compare_worlds
    data = worlds()
    data[0]["verification"]["valid"] = False
    data[0]["metrics"] = {"on_time_coverage": 1000000}
    result = compare_worlds(data, {"coverage": 1, "equity": 0, "cost": 0})
    assert result["recommended_id"] == "equity"
    assert result["eligible_ids"] == ["equity"]


def test_equal_verified_results_report_tie_and_no_arbitrary_winner():
    from backend.comparison import compare_worlds
    data = worlds()
    data[1]["verification"]["metrics"] = copy.deepcopy(data[0]["verification"]["metrics"])
    result = compare_worlds(data)
    assert result["recommended_id"] is None
    assert set(result["tied_ids"]) == {"velocity", "equity"}


def test_zero_weights_rejected_instead_of_dividing_by_zero():
    from backend.comparison import compare_worlds
    with pytest.raises(ValueError):
        compare_worlds(worlds(), {"coverage": 0, "equity": 0, "cost": 0})


def test_sqlite_reopen_recovers_experiment_and_command_receipt(tmp_path):
    from backend.store import ExperimentStore
    path = tmp_path / "fork.sqlite"
    store = ExperimentStore(path)
    store.save({"id": "exp-1", "revision": 1, "worlds": []})
    store.record_command("new", "key-1", "body-hash", {"id": "exp-1"})
    reopened = ExperimentStore(path)
    assert reopened.get("exp-1")["revision"] == 1
    assert reopened.command("new", "key-1", "body-hash") == {"id": "exp-1"}
    with pytest.raises(ValueError):
        reopened.command("new", "key-1", "different-body")


def test_store_returns_detached_snapshots(tmp_path):
    from backend.store import ExperimentStore
    store = ExperimentStore(tmp_path / "fork.sqlite")
    store.save({"id": "exp-1", "revision": 1, "worlds": [{"id": "velocity"}]})
    value = store.get("exp-1")
    value["worlds"][0]["id"] = "changed"
    assert store.get("exp-1")["worlds"][0]["id"] == "velocity"
