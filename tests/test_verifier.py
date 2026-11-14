"""Hand-derived referee examples: no planner/simulator helpers construct expected values."""
from copy import deepcopy
import pytest

from backend.fork_engine.verifier import verify_world


def small_world():
    scenario = {
        "id": "small", "hash": "small-hash", "horizon": 1000,
        "depot_id": "depot", "inventory": {"ambient": 10, "chilled": 0},
        "nodes": [
            {"id": "depot", "x": 0, "y": 0, "kind": "depot", "demand": 0},
            {"id": "food", "x": 100, "y": 0, "kind": "destination", "demand": 6,
             "commodity": "ambient", "priority": 3, "window_start": 0,
             "window_end": 500, "due": 240, "service_seconds": 20},
        ],
        "edges": [{"id": "road", "source": "depot", "target": "food", "distance_m": 1000, "seconds": 100},
                  {"id": "back", "source": "food", "target": "depot", "distance_m": 1000, "seconds": 100}],
        "vehicles": [{"id": "A", "capacity": 10, "chilled": False, "cost_per_km": 50,
                      "emissions_per_km": 200, "driver_id": "v", "shift_start": 0, "shift_end": 1000}],
        "volunteers": [{"id": "v", "vehicle_id": "A", "shift_start": 0, "shift_end": 1000}],
    }
    result = {
        "initial_hash": "small-hash", "metrics": {"meals_delivered": 9999}, "final_state": {},
        "trajectories": [
            {"vehicle_id": "A", "from_id": "depot", "to_id": "food", "depart": 0, "arrive": 100,
             "distance_m": 1000, "path": [[0, 0], [100, 0]], "revision": 0},
            {"vehicle_id": "A", "from_id": "food", "to_id": "depot", "depart": 120, "arrive": 220,
             "distance_m": 1000, "path": [[100, 0], [0, 0]], "revision": 0},
        ],
        "deliveries": [{"id": "d1", "destination_id": "food", "vehicle_id": "A", "quantity": 6,
                        "commodity": "ambient", "service_start": 100, "completed_at": 120,
                        "priority": 3, "on_time": True}],
        "events": [
            {"id": "load1", "seq": 0, "time": 0, "kind": "load", "vehicle_id": "A", "node_id": "depot", "commodity": "ambient", "quantity": 6},
            {"id": "depart1", "seq": 1, "time": 0, "kind": "depart", "vehicle_id": "A", "node_id": "depot"},
            {"id": "arrive1", "seq": 2, "time": 100, "kind": "arrive", "vehicle_id": "A", "node_id": "food"},
            {"id": "service1", "seq": 3, "time": 100, "kind": "service_start", "vehicle_id": "A", "node_id": "food"},
            {"id": "delivery1", "seq": 4, "time": 120, "kind": "delivery", "vehicle_id": "A", "node_id": "food", "delivery_id": "d1", "commodity": "ambient", "quantity": 6},
            {"id": "depart2", "seq": 5, "time": 120, "kind": "depart", "vehicle_id": "A", "node_id": "food"},
            {"id": "return1", "seq": 6, "time": 220, "kind": "return", "vehicle_id": "A", "node_id": "depot"},
        ],
    }
    for trajectory in result["trajectories"]:
        trajectory["depart"] += 120
        trajectory["arrive"] += 120
        trajectory["edge_id"] = "road" if trajectory["from_id"] == "depot" else "back"
    for delivery in result["deliveries"]:
        delivery["service_start"] += 120
        delivery["completed_at"] += 120
    for event in result["events"]:
        event["time"] += 120
        event["seq"] += 1
    result["events"][0].update(started_at=0, manifest={"ambient": 6, "chilled": 0})
    result["events"].insert(0, {"id": "loadstart", "seq": 0, "time": 0, "kind": "load_start", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 6, "chilled": 0}, "complete_at": 120})
    return scenario, result


def codes(receipt):
    return {v["code"] for v in receipt["violations"]}


def test_hand_derived_metrics_ignore_claims_and_final_state():
    scenario, result = small_world()
    receipt = verify_world(scenario, result)
    assert receipt["valid"], receipt["violations"]
    assert receipt["metrics"] == {
        "meals_delivered": 6, "demand": 6, "coverage": 1.0, "on_time_meals": 6,
        "on_time_coverage": 1.0, "priority_coverage": 1.0, "priority_weighted_coverage": 1.0,
        "destinations_served": 1, "late_deliveries": 0, "unserved_meals": 0,
        "distance_m": 2000, "cost_cents": 100, "emissions_g": 400, "violations": 0,
    }
    assert receipt["scenario_hash"] == "small-hash"
    assert len(receipt["event_hash"]) == 64
    assert receipt["checks"] and all(c["passed"] for c in receipt["checks"])


def test_rejects_extra_food_without_depot_stock():
    scenario, result = small_world()
    result["events"][1]["manifest"]["ambient"] = 11
    result["events"][0]["manifest"]["ambient"] = 11
    assert "INVENTORY" in codes(verify_world(scenario, result))


def test_rejects_teleported_road_travel():
    scenario, result = small_world()
    result["trajectories"][0]["depart"] = 99
    assert "ROAD_TRAVEL" in codes(verify_world(scenario, result))


def test_rejects_duplicate_destination_delivery():
    scenario, result = small_world()
    duplicate = deepcopy(result["deliveries"][0])
    duplicate["id"] = "d2"
    result["deliveries"].append(duplicate)
    assert "DUPLICATE_DELIVERY" in codes(verify_world(scenario, result))


def test_rejects_delivery_after_breakdown():
    scenario, result = small_world()
    result["events"].insert(5, {"id": "break", "seq": 4.5, "time": 230, "kind": "breakdown", "vehicle_id": "A"})
    assert "UNAVAILABLE" in codes(verify_world(scenario, result))


def test_rejects_chilled_cargo_in_ambient_vehicle():
    scenario, result = small_world()
    scenario["inventory"] = {"ambient": 0, "chilled": 10}
    scenario["nodes"][1]["commodity"] = "chilled"
    result["deliveries"][0]["commodity"] = "chilled"
    for event in result["events"]:
        if "commodity" in event:
            event["commodity"] = "chilled"
        if "manifest" in event:
            event["manifest"] = {"ambient": 0, "chilled": 6}
    assert "COMPATIBILITY" in codes(verify_world(scenario, result))


@pytest.mark.parametrize("mutation,expected", [
    ("no_load", "CUSTODY"), ("capacity", "CAPACITY"), ("window", "WINDOW"),
    ("shift", "SHIFT"), ("wrong_location", "LOCATION"), ("service", "SERVICE_TIME"),
    ("missing_delivery_event", "DELIVERY_LEDGER"), ("overlap", "OVERLAP"),
])
def test_rejects_independent_constraint_tampering(mutation, expected):
    scenario, result = small_world()
    if mutation == "no_load":
        result["events"] = [e for e in result["events"] if e["kind"] not in ("load", "load_start")]
    elif mutation == "capacity":
        scenario["vehicles"][0]["capacity"] = 5
    elif mutation == "window":
        scenario["nodes"][1]["window_end"] = 239
    elif mutation == "shift":
        scenario["volunteers"][0]["shift_end"] = 339
    elif mutation == "wrong_location":
        result["trajectories"][0]["from_id"] = "food"
    elif mutation == "service":
        result["deliveries"][0]["service_start"] = 221
    elif mutation == "missing_delivery_event":
        result["events"] = [e for e in result["events"] if e["kind"] != "delivery"]
    elif mutation == "overlap":
        result["trajectories"][1]["depart"] = 239
    receipt = verify_world(scenario, result)
    assert not receipt["valid"]
    assert expected in codes(receipt)


def test_rejects_load_that_omits_timed_start():
    scenario, result = small_world()
    result["events"][1].pop("started_at")
    # All production loads are 120 seconds, never instantaneous grants.
    assert "LOAD_TIME" in codes(verify_world(scenario, result))


def test_rejects_reverse_use_of_a_one_way_road():
    scenario, result = small_world()
    scenario["edges"] = scenario["edges"][:1]
    # The same road cannot be silently reversed to get home.
    assert "ROAD_TRAVEL" in codes(verify_world(scenario, result))


def test_rejects_partial_order_not_atomic_transfer():
    scenario, result = small_world()
    result["deliveries"][0]["quantity"] = 5
    result["events"][5]["quantity"] = 5
    assert "DEMAND" in codes(verify_world(scenario, result))


def test_arrival_then_informational_return_are_one_physical_completion():
    scenario, result = small_world()
    result["events"].insert(-1, {"id": "arrived-home", "seq": 6.5, "time": 340, "kind": "arrive", "vehicle_id": "A", "node_id": "depot"})
    assert verify_world(scenario, result)["valid"]


def partial_world():
    scenario, result = small_world()
    scenario["edges"][0]["distance_m"] = 1003
    result["trajectories"] = [{"vehicle_id": "A", "from_id": "depot", "to_id": "breakdown:A", "depart": 120,
                               "arrive": 173, "path": [[0, 0], [53, 0]], "distance_m": 531,
                               "revision": 0, "edge_id": "road", "progress": 0.53}]
    result["deliveries"] = []
    result["events"] = result["events"][:3]
    result["events"].append({"id": "failed", "seq": 3, "time": 173, "kind": "breakdown", "vehicle_id": "A",
                             "position": [53, 0], "edge_id": "road", "edge_progress": 0.53,
                             "distance_m": 531, "stranded": {"ambient": 6, "chilled": 0}})
    return scenario, result


def test_partial_edge_uses_integer_actual_metres_and_strands_cargo():
    scenario, result = partial_world()
    receipt = verify_world(scenario, result)
    assert receipt["valid"], receipt["violations"]
    assert receipt["metrics"]["distance_m"] == 531
    assert receipt["metrics"]["meals_delivered"] == 0
    assert receipt["metrics"]["cost_cents"] == 27


def test_rejects_breakdown_position_that_disagrees_with_actual_edge():
    scenario, result = partial_world()
    result["events"][-1]["position"] = [99, 0]
    assert "LOCATION" in codes(verify_world(scenario, result))


def test_rejects_orphan_service_that_vehicle_abandons_without_failure():
    scenario, result = small_world()
    result["deliveries"] = []
    result["events"] = [e for e in result["events"] if e["kind"] != "delivery"]
    assert "SERVICE_TIME" in codes(verify_world(scenario, result))


def test_rejects_healthy_ongoing_loading_abandoned_without_completion():
    scenario, result = small_world()
    result["events"] = result["events"][:1]
    result["trajectories"] = []
    result["deliveries"] = []
    assert "LOAD_TIME" in codes(verify_world(scenario, result))


def test_rejects_tampered_arrival_metres_even_when_trajectory_looks_valid():
    scenario, result = small_world()
    arrival = next(e for e in result["events"] if e["kind"] == "arrive")
    arrival["distance_m"] = 99999
    assert "MOVEMENT_LEDGER" in codes(verify_world(scenario, result))


def test_rejects_tampered_service_start_manifest():
    scenario, result = small_world()
    event = next(e for e in result["events"] if e["kind"] == "service_start")
    event.update(quantity=100, commodity="chilled")
    assert "DELIVERY_LEDGER" in codes(verify_world(scenario, result))


def test_rejects_fractional_elapsed_seconds():
    scenario, result = small_world()
    result["events"][0]["time"] = 0.5
    assert "HORIZON" in codes(verify_world(scenario, result))


def test_recovery_reload_counts_unused_old_cargo_in_capacity():
    scenario, result = small_world()
    scenario["inventory"]["ambient"] = 20
    for e in result["events"]:
        if e["kind"] in ("load", "load_start"):
            e["manifest"]["ambient"] = 10
    result["events"].extend([
        {"id": "reload-start", "seq": 8, "time": 340, "kind": "load_start", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 7, "chilled": 0}, "complete_at": 460},
        {"id": "reload-end", "seq": 9, "time": 460, "kind": "load", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 7, "chilled": 0}, "started_at": 340},
    ])
    assert "CAPACITY" in codes(verify_world(scenario, result))


def test_cancelled_atomic_loading_keeps_stock_at_depot():
    scenario, result = small_world()
    result["events"] = result["events"][:1] + [{"id": "failure", "seq": 1, "time": 60, "kind": "breakdown", "vehicle_id": "A", "node_id": "depot", "position": [0, 0], "distance_m": 0, "stranded": {"ambient": 0, "chilled": 0}}]
    result["trajectories"] = []
    result["deliveries"] = []
    assert verify_world(scenario, result)["valid"]


def test_completion_exactly_at_breakdown_is_retained_before_failure():
    scenario, result = small_world()
    result["trajectories"] = result["trajectories"][:1]
    result["events"] = result["events"][:6] + [{"id": "failure", "seq": 6, "time": 240, "kind": "breakdown", "vehicle_id": "A", "node_id": "food", "position": [100, 0], "distance_m": 0, "stranded": {"ambient": 0, "chilled": 0}}]
    receipt = verify_world(scenario, result)
    assert receipt["valid"], receipt["violations"]
    assert receipt["metrics"]["meals_delivered"] == 6


def test_event_hash_covers_trajectory_and_delivery_evidence_and_is_stable():
    scenario, result = small_world()
    first = verify_world(scenario, result)
    assert first["event_hash"] == verify_world(scenario, deepcopy(result))["event_hash"]
    result["trajectories"][0]["distance_m"] = 998
    assert first["event_hash"] != verify_world(scenario, result)["event_hash"]


def test_late_high_priority_meals_count_coverage_but_not_on_time_equity():
    scenario, result = small_world()
    scenario["nodes"][1]["due"] = 239
    receipt = verify_world(scenario, result)
    assert receipt["valid"]
    assert receipt["metrics"]["coverage"] == 1
    assert receipt["metrics"]["on_time_coverage"] == 0
    assert receipt["metrics"]["priority_coverage"] == 0
    assert receipt["metrics"]["priority_weighted_coverage"] == 0
    assert receipt["metrics"]["late_deliveries"] == 1


def test_joint_recovery_loads_cannot_each_spend_the_same_depot_stock():
    scenario, result = small_world()
    scenario["vehicles"].append(dict(scenario["vehicles"][0], id="B", driver_id="w"))
    scenario["volunteers"].append(dict(scenario["volunteers"][0], id="w", vehicle_id="B"))
    result["events"].extend([
        {"id": "second-start", "seq": 8, "time": 340, "kind": "load_start", "vehicle_id": "B", "node_id": "depot", "manifest": {"ambient": 6, "chilled": 0}, "complete_at": 460},
        {"id": "second-end", "seq": 9, "time": 460, "kind": "load", "vehicle_id": "B", "node_id": "depot", "manifest": {"ambient": 6, "chilled": 0}, "started_at": 340},
    ])
    assert "INVENTORY" in codes(verify_world(scenario, result))


def test_rejects_unreturned_healthy_vehicle_even_with_valid_outbound_delivery():
    scenario, result = small_world()
    result["trajectories"] = result["trajectories"][:1]
    result["events"] = result["events"][:6]
    assert "RETURN" in codes(verify_world(scenario, result))


def test_rejects_trajectory_path_detour_unsupported_by_road_distance():
    scenario, result = small_world()
    result["trajectories"][0]["path"].insert(1, [999, 999])
    assert "LOCATION" in codes(verify_world(scenario, result))


def test_malformed_evidence_fails_closed_without_claiming_unrun_checks_passed():
    scenario, result = small_world()
    result["trajectories"][0]["vehicle_id"] = "does-not-exist"
    receipt = verify_world(scenario, result)
    assert not receipt["valid"]
    assert "SCHEMA" in codes(receipt)
    assert all(not c["passed"] for c in receipt["checks"])


def test_non_json_evidence_cannot_receive_valid_receipt():
    scenario, result = small_world()
    result["events"][0]["summary"] = {object()}
    assert "SCHEMA" in codes(verify_world(scenario, result))


def test_coefficient_rounding_preserves_exact_half_unit_before_bankers_rounding():
    scenario, result = small_world()
    for edge in scenario["edges"]:
        edge["distance_m"] = 2050
    for leg in result["trajectories"]:
        leg["distance_m"] = 2050
    scenario["vehicles"][0]["emissions_per_km"] = 95
    receipt = verify_world(scenario, result)
    assert receipt["valid"]
    # 4100 metres *95 grams/km =389.5 grams; ties-to-even gives390.
    assert receipt["metrics"]["emissions_g"] == 390


def test_recovery_reload_requires_an_actual_prior_disruption():
    scenario, result = small_world()
    scenario["inventory"]["ambient"] = 20
    result["events"].extend([
        {"id": "reload-start", "seq": 8, "time": 340, "kind": "load_start", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 6, "chilled": 0}, "complete_at": 460},
        {"id": "reload-end", "seq": 9, "time": 460, "kind": "load", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 6, "chilled": 0}, "started_at": 340},
    ])
    assert "LOAD_LIMIT" in codes(verify_world(scenario, result))


def two_load_world_with_idle_vehicle_failure(shock):
    """A loads 6 at 10..130, delivers at 250, returns at 350, then loads 4 at 350..470."""
    scenario, result = small_world()
    scenario["vehicles"].append(dict(scenario["vehicles"][0], id="B", driver_id="w"))
    scenario["volunteers"].append(dict(scenario["volunteers"][0], id="w", vehicle_id="B"))
    for event in result["events"]:
        event["time"] += 10
        for key in ("started_at", "complete_at"):
            if key in event:
                event[key] += 10
    for trajectory in result["trajectories"]:
        trajectory["depart"] += 10
        trajectory["arrive"] += 10
    result["deliveries"][0]["service_start"] = 230
    result["deliveries"][0]["completed_at"] = 250
    result["events"].extend([
        {"id": "failure-B", "time": shock, "kind": "breakdown", "vehicle_id": "B", "node_id": "depot", "position": [0, 0], "distance_m": 0, "stranded": {"ambient": 0, "chilled": 0}},
        {"id": "recovery-start", "time": 350, "kind": "load_start", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 4, "chilled": 0}, "complete_at": 470},
        {"id": "recovery-end", "time": 470, "kind": "load", "vehicle_id": "A", "node_id": "depot", "manifest": {"ambient": 4, "chilled": 0}, "started_at": 350},
    ])
    # A shock at 10 precedes new operation starts at the same timestamp.
    result["events"].sort(key=lambda event: (event["time"], event["kind"] != "breakdown"))
    for seq, event in enumerate(result["events"]):
        event["seq"] = seq
    return scenario, result


@pytest.mark.parametrize("shock", [0, 10])
def test_initially_unloaded_vehicle_cannot_complete_two_post_shock_loads(shock):
    scenario, result = two_load_world_with_idle_vehicle_failure(shock)
    receipt = verify_world(scenario, result)
    assert not receipt["valid"]
    assert codes(receipt) == {"LOAD_LIMIT"}
    assert receipt["violations"][0]["event_id"] == "recovery-end"


def test_initial_load_started_before_shock_preserves_one_recovery_load_allowance():
    scenario, result = two_load_world_with_idle_vehicle_failure(60)
    receipt = verify_world(scenario, result)
    assert receipt["valid"], receipt["violations"]
    assert receipt["metrics"]["meals_delivered"] == 6
    assert receipt["metrics"]["distance_m"] == 2000
