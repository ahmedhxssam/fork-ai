"""Independent replay referee; intentionally imports no engine or solver helpers.

The receipt is derived from initial stock, physical loads, edge trajectories and
completed delivery records. Claimed result metrics and final state are ignored.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math

VERSION = "fork-referee-1.0"
COMMODITIES = ("ambient", "chilled")
CHECKS = {
    "provenance": ("Common initial scenario and evidence", {"INITIAL_HASH", "SCHEMA", "EVENT_ORDER", "EVENT_ID"}),
    "custody": ("Stock and cargo custody", {"INVENTORY", "CUSTODY", "QUANTITY", "LOAD_LIMIT", "LOAD_TIME", "STRANDED"}),
    "capacity": ("Vehicle capacity and cold compatibility", {"CAPACITY", "COMPATIBILITY"}),
    "delivery": ("Unique completed delivery ledger", {"DUPLICATE_DELIVERY", "DELIVERY_LEDGER", "DEMAND", "COMMODITY"}),
    "movement": ("Road travel and continuous locations", {"ROAD_TRAVEL", "LOCATION", "MOVEMENT_LEDGER", "OVERLAP", "RETURN"}),
    "timing": ("Service windows, duration and shifts", {"WINDOW", "SHIFT", "SERVICE_TIME", "HORIZON"}),
    "availability": ("Failed vehicles do no further work", {"UNAVAILABLE"}),
}


def verify_world(scenario: dict, result: dict) -> dict:
    """Return a JSON-compatible independent receipt, failing closed on bad input."""
    violations = []

    def fail(code, message, event=None):
        item = {"code": code, "message": message}
        if event and event.get("id") is not None:
            item["event_id"] = event["id"]
        if item not in violations:
            violations.append(item)

    metrics = {}
    try:
        metrics = _replay(scenario, result, fail)
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as exc:
        fail("SCHEMA", f"Malformed physical evidence: {exc}")
    try:
        payload = {key: result.get(key, []) for key in ("events", "trajectories", "deliveries")}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    except (ValueError, TypeError):
        fail("SCHEMA", "Physical evidence must be finite JSON-compatible data")
        digest = hashlib.sha256(b"invalid-evidence").hexdigest()
    metrics["violations"] = len(violations)
    failed = {v["code"] for v in violations}
    checks = []
    for key, (label, codes) in CHECKS.items():
        count = sum(v["code"] in codes for v in violations)
        passed = not bool(failed & codes) and "SCHEMA" not in failed
        detail = "Replay incomplete because evidence is malformed" if "SCHEMA" in failed else (f"{count} violation(s)" if count else "Independent replay passed")
        checks.append({"id": key, "label": label, "passed": passed, "detail": detail})
    return {"valid": not violations, "violations": violations, "metrics": metrics,
            "checks": checks, "scenario_hash": scenario.get("hash"),
            "event_hash": digest, "version": VERSION}


def _replay(scenario, result, fail):
    nodes = {n["id"]: n for n in scenario["nodes"]}
    vehicles = {v["id"]: v for v in scenario["vehicles"]}
    volunteers = {v["id"]: v for v in scenario.get("volunteers", [])}
    edges = scenario["edges"]
    depot = scenario["depot_id"]
    horizon = scenario["horizon"]
    events = result.get("events", [])
    deliveries = result.get("deliveries", [])
    trajectories = result.get("trajectories", [])
    if result.get("initial_hash") != scenario.get("hash"):
        fail("INITIAL_HASH", "World was not produced from the supplied initial scenario")

    def number(value):
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)

    def quantity(value, event=None):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            fail("QUANTITY", "Meal quantities must be nonnegative integers", event)
            return 0
        return value

    def timecheck(start, end, vid, event=None):
        if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 0 or end < start or end > horizon:
            fail("HORIZON", f"Invalid elapsed-time interval {start}..{end}", event)
        vehicle = vehicles[vid]
        driver = volunteers.get(vehicle.get("driver_id"), {})
        low = max(vehicle.get("shift_start", 0), driver.get("shift_start", 0))
        high = min(vehicle.get("shift_end", horizon), driver.get("shift_end", horizon))
        if start < low or end > high:
            fail("SHIFT", f"Vehicle {vid} work/required return exceeds vehicle or volunteer shift", event)

    ids = [e["id"] for e in events]
    if len(ids) != len(set(ids)):
        fail("EVENT_ID", "Physical event IDs are not unique")
    previous = (-1, -1)
    for e in events:
        t, seq = e["time"], e["seq"]
        if not number(t) or not number(seq) or (t, seq) < previous:
            fail("EVENT_ORDER", "Events must be chronological with stable sequence", e)
        previous = (t, seq)
        if not isinstance(t, int) or isinstance(t, bool) or t < 0 or t > horizon:
            fail("HORIZON", "Event falls outside scenario horizon", e)
        if "vehicle_id" in e and e["vehicle_id"] not in vehicles:
            fail("SCHEMA", "Event references unknown vehicle", e)

    shocks = {}
    shock_order = {}
    for e in events:
        if e["kind"] == "breakdown":
            vid = e["vehicle_id"]
            if vid in shocks:
                fail("UNAVAILABLE", f"Vehicle {vid} failed more than once", e)
            shocks[vid] = min(shocks.get(vid, math.inf), e["time"])
            shock_order[vid] = (e["time"], e["seq"])

    legs = defaultdict(list)
    distance = defaultdict(float)
    for tr in trajectories:
        vid = tr["vehicle_id"]
        vehicle = vehicles[vid]
        start, end = tr["depart"], tr["arrive"]
        timecheck(start, end, vid)
        origin, target = tr["from_id"], tr["to_id"]
        partial = tr.get("progress", 1) < 1 or target not in nodes
        candidates = [e for e in edges if (not tr.get("edge_id") or e["id"] == tr["edge_id"])
                      and origin == e["source"]
                      and (partial or target == e["target"])]
        if len(candidates) != 1:
            fail("ROAD_TRAVEL", f"Vehicle {vid} trajectory does not follow a unique road")
            edge = None
        else:
            edge = candidates[0]
            other = edge["target"] if origin == edge["source"] else edge["source"]
            progress = tr.get("progress", (end - start) / edge["seconds"] if partial else 1)
            if not number(progress) or not 0 < progress <= 1:
                fail("ROAD_TRAVEL", f"Vehicle {vid} has invalid edge progress")
                progress = 1
            expected_duration = edge["seconds"] * progress
            expected_distance = math.floor(edge["distance_m"] * progress) if partial else edge["distance_m"]
            if abs((end - start) - expected_duration) > 1e-6 or abs(tr["distance_m"] - expected_distance) > 1e-4:
                fail("ROAD_TRAVEL", f"Vehicle {vid} trajectory time/distance does not match road speed")
            expected_end = [nodes[origin][axis] + progress * (nodes[other][axis] - nodes[origin][axis]) for axis in ("x", "y")]
            path = tr["path"]
            expected_start = [nodes[origin]["x"], nodes[origin]["y"]]
            if len(path) < 2 or any(abs(path[0][i] - expected_start[i]) > 1e-4 or abs(path[-1][i] - expected_end[i]) > 1e-4 for i in (0, 1)):
                fail("LOCATION", f"Vehicle {vid} trajectory path has impossible endpoints")
            dx, dy = nodes[other]["x"] - nodes[origin]["x"], nodes[other]["y"] - nodes[origin]["y"]
            norm = dx * dx + dy * dy
            previous_progress = -1e-6
            for point in path:
                px, py = point[0] - expected_start[0], point[1] - expected_start[1]
                along = (px * dx + py * dy) / norm if norm else 0
                cross = px * dy - py * dx
                if not all(number(x) for x in point) or abs(cross) > 1e-4 or along < previous_progress or along > progress + 1e-6:
                    fail("LOCATION", f"Vehicle {vid} trajectory geometry leaves or reverses its road")
                previous_progress = along
        if partial and (vid not in shocks or end != shocks[vid]):
            fail("UNAVAILABLE", f"Vehicle {vid} partial road must end at actual breakdown")
        if vid in shocks and (start >= shocks[vid] or end > shocks[vid]):
            fail("UNAVAILABLE", f"Vehicle {vid} travels after breakdown")
        if not number(tr["distance_m"]) or tr["distance_m"] < 0:
            fail("ROAD_TRAVEL", "Distance must be finite and nonnegative")
        else:
            distance[vid] += tr["distance_m"]
        legs[vid].append(tr)

    for vid, route in legs.items():
        route.sort(key=lambda t: (t["depart"], t["arrive"]))
        last_node, ready = depot, 0
        for tr in route:
            if tr["depart"] < ready:
                fail("OVERLAP", f"Vehicle {vid} has overlapping movements")
            if tr["from_id"] != last_node:
                fail("LOCATION", f"Vehicle {vid} departs from {tr['from_id']} while at {last_node}")
            last_node, ready = tr["to_id"], tr["arrive"]
        if vid not in shocks and last_node != depot:
            fail("RETURN", f"Healthy vehicle {vid} never completed required depot return")

    def location_at(vid, t):
        location = depot
        for tr in legs.get(vid, []):
            if tr["depart"] < t < tr["arrive"]:
                return None
            if tr["arrive"] <= t:
                location = tr["to_id"]
            elif tr["depart"] >= t:
                break
        return location

    def stationary(vid, node, start, end, event=None):
        if location_at(vid, start) != node or location_at(vid, end) != node:
            fail("LOCATION", f"Vehicle {vid} is not at {node} for physical operation", event)
        if any(tr["depart"] < end and tr["arrive"] > start for tr in legs.get(vid, [])):
            fail("OVERLAP", f"Vehicle {vid} moves during loading or service", event)

    # Cross-check the claimed trajectories against departure/completion evidence.
    for vid, route in legs.items():
        for tr in route:
            starts = [e for e in events if e["kind"] == "depart" and e.get("vehicle_id") == vid and e["time"] == tr["depart"]
                      and e.get("from_id", e.get("node_id")) == tr["from_id"]
                      and (not e.get("edge_id") or e["edge_id"] == tr.get("edge_id"))]
            partial = tr["to_id"] not in nodes or tr.get("progress", 1) < 1
            ends = [e for e in events if e["kind"] in (("breakdown",) if partial else ("arrive", "return"))
                    and e.get("vehicle_id") == vid and e["time"] == tr["arrive"]
                    and (partial or e.get("node_id") == tr["to_id"])]
            if not partial:
                arrivals = [e for e in ends if e["kind"] == "arrive"]
                ends = arrivals if arrivals else ends
            if len(starts) != 1 or len(ends) != 1:
                fail("MOVEMENT_LEDGER", f"Vehicle {vid} trajectory lacks unique physical departure/completion evidence")
            elif not partial:
                departure, arrival = starts[0], ends[0]
                if any(key in arrival and arrival[key] != value for key, value in (("distance_m", tr["distance_m"]), ("depart", tr["depart"]), ("from_id", tr["from_id"]), ("edge_id", tr.get("edge_id")))):
                    fail("MOVEMENT_LEDGER", "Arrival road ledger differs from actual trajectory", arrival)
                if any(key in departure and departure[key] != value for key, value in (("distance_m", tr["distance_m"]), ("arrive", tr["arrive"]), ("to_id", tr["to_id"]))):
                    fail("MOVEMENT_LEDGER", "Departure road ledger differs from actual trajectory", departure)
    for e in events:
        if e["kind"] == "depart" and not any(tr["depart"] == e["time"] and tr["vehicle_id"] == e.get("vehicle_id") for tr in trajectories):
            fail("MOVEMENT_LEDGER", "Departure has no actual trajectory", e)
        if e["kind"] in ("arrive", "return") and not any(tr["arrive"] == e["time"] and tr["vehicle_id"] == e.get("vehicle_id") and tr["to_id"] == e.get("node_id") for tr in trajectories):
            fail("MOVEMENT_LEDGER", "Arrival/return has no actual trajectory", e)

    # Started operations remain locked until their actual completion or failure.
    busy = defaultdict(list)
    for e in events:
        kind, vid, start = e["kind"], e.get("vehicle_id"), e["time"]
        if kind not in ("load_start", "service_start") or vid not in vehicles:
            continue
        node_id = e.get("node_id")
        if node_id not in nodes:
            fail("LOCATION", "Operation starts at unknown node", e)
            continue
        if kind == "load_start":
            expected_end = start + 120
            node_id = depot
            done = [x for x in events if x["kind"] == "load" and x.get("vehicle_id") == vid and x["time"] == expected_end and x.get("started_at") == start]
            error_code = "LOAD_TIME"
        else:
            expected_end = start + nodes[node_id]["service_seconds"]
            done = [d for d in deliveries if d["vehicle_id"] == vid and d["destination_id"] == node_id and d["service_start"] == start and d["completed_at"] == expected_end]
            error_code = "SERVICE_TIME"
        if e.get("complete_at", expected_end) != expected_end:
            fail(error_code, "Started operation has incorrect scheduled completion", e)
        failed_at = shocks.get(vid, math.inf)
        interrupted = start <= failed_at < expected_end
        actual_end = min(expected_end, failed_at)
        if not interrupted and len(done) != 1:
            fail(error_code, "Healthy started operation was abandoned or completed more than once", e)
        if interrupted and done:
            fail("UNAVAILABLE", "Interrupted atomic operation cannot complete", e)
        stationary(vid, node_id, start, actual_end, e)
        timecheck(start, actual_end, vid, e)
        for previous_start, previous_end in busy[vid]:
            if start < previous_end and actual_end > previous_start:
                fail("OVERLAP", f"Vehicle {vid} starts overlapping load/service operations", e)
        busy[vid].append((start, actual_end))

    for e in events:
        if e["kind"] != "breakdown":
            continue
        vid, t = e["vehicle_id"], e["time"]
        ending = [tr for tr in legs.get(vid, []) if tr["arrive"] == t and (tr["to_id"] not in nodes or tr.get("progress", 1) < 1)]
        if ending:
            tr = ending[0]
            expected_position = tr["path"][-1]
            if e.get("edge_id") != tr.get("edge_id") or abs(e.get("edge_progress", -1) - tr.get("progress", 1)) > 1e-6 or e.get("distance_m") != tr["distance_m"]:
                fail("MOVEMENT_LEDGER", "Breakdown road evidence differs from truncated trajectory", e)
        else:
            node_id = location_at(vid, t)
            expected_position = [nodes[node_id]["x"], nodes[node_id]["y"]] if node_id in nodes else None
            if e.get("node_id", node_id) != node_id:
                fail("LOCATION", "Stationary breakdown node differs from actual location", e)
        if expected_position is None or e.get("position") is None or any(abs(e["position"][i] - expected_position[i]) > 1e-4 for i in (0, 1)):
            fail("LOCATION", "Breakdown position differs from actual vehicle position", e)

    delivery_ids, served = set(), set()
    delivered_records = []
    for d in deliveries:
        vid, destination = d["vehicle_id"], d["destination_id"]
        node = nodes[destination]
        q = quantity(d["quantity"])
        start, end = d["service_start"], d["completed_at"]
        timecheck(start, end, vid)
        if d["id"] in delivery_ids or destination in served:
            fail("DUPLICATE_DELIVERY", f"Order {destination} was completed more than once")
        delivery_ids.add(d["id"])
        served.add(destination)
        if node["kind"] != "destination" or q != node["demand"] or q <= 0:
            fail("DEMAND", f"Delivery {d['id']} exceeds or does not represent destination demand")
        if d["commodity"] != node["commodity"]:
            fail("COMMODITY", f"Delivery {d['id']} commodity differs from order")
        if d["commodity"] == "chilled" and not vehicles[vid]["chilled"]:
            fail("COMPATIBILITY", f"Vehicle {vid} cannot carry chilled meals")
        if start < node["window_start"] or end > node["window_end"]:
            fail("WINDOW", f"Order {destination} completed outside hard service window")
        if end - start != node["service_seconds"]:
            fail("SERVICE_TIME", f"Order {destination} service duration is incorrect")
        stationary(vid, destination, start, end)
        if vid in shocks and (end > shocks[vid] or start >= shocks[vid]):
            fail("UNAVAILABLE", f"Vehicle {vid} delivers after breakdown")
        matches = [e for e in events if e["kind"] == "delivery" and e.get("delivery_id", e.get("id")) == d["id"]]
        if len(matches) != 1:
            fail("DELIVERY_LEDGER", f"Delivery {d['id']} has no unique matching completion event")
        else:
            e = matches[0]
            if (e.get("vehicle_id"), e.get("node_id"), e.get("quantity"), e.get("commodity"), e["time"]) != (vid, destination, q, d["commodity"], end):
                fail("DELIVERY_LEDGER", f"Delivery {d['id']} differs from physical event", e)
        starts = [e for e in events if e["kind"] == "service_start" and e.get("vehicle_id") == vid and e.get("node_id") == destination and e["time"] == start]
        if len(starts) != 1:
            fail("SERVICE_TIME", f"Delivery {d['id']} has no unique service start")
        elif any(key in starts[0] and starts[0][key] != value for key, value in (("quantity", q), ("commodity", d["commodity"]))):
            fail("DELIVERY_LEDGER", f"Delivery {d['id']} differs from started service manifest", starts[0])
        delivered_records.append(d)

    stock = {c: quantity(scenario["inventory"].get(c, 0)) for c in COMMODITIES}
    cargo = {vid: {c: 0 for c in COMMODITIES} for vid in vehicles}
    stranded = {c: 0 for c in COMMODITIES}
    transferred = {c: 0 for c in COMMODITIES}
    load_counts = Counter()
    recovery_load_counts = Counter()
    for e in sorted(events, key=lambda e: (e["time"], e["seq"])):
        kind, vid, t = e["kind"], e.get("vehicle_id"), e["time"]
        if vid not in vehicles:
            continue
        if vid in shock_order and (t, e["seq"]) > shock_order[vid] and kind in ("load", "load_start", "depart", "arrive", "return", "service_start", "delivery"):
            fail("UNAVAILABLE", f"Vehicle {vid} performs {kind} after breakdown", e)
        if kind == "load":
            load_counts[vid] += 1
            if load_counts[vid] > 1 and (not shocks or e.get("started_at", t) < min(shocks.values())):
                fail("LOAD_LIMIT", f"Vehicle {vid} reloads before any actual recovery disruption", e)
            if shocks and e.get("started_at", t) >= min(shocks.values()):
                recovery_load_counts[vid] += 1
                if recovery_load_counts[vid] > 1:
                    fail("LOAD_LIMIT", f"Vehicle {vid} exceeds one recovery reload", e)
            if "started_at" not in e:
                fail("LOAD_TIME", "Completed load lacks its timed start", e)
            start = e.get("started_at", t)
            timecheck(start, t, vid, e)
            stationary(vid, depot, start, t, e)
            if "started_at" in e:
                duration = scenario.get("assumptions", {}).get("load_seconds", 120) if isinstance(scenario.get("assumptions", {}), dict) else 120
                if t - start != duration:
                    fail("LOAD_TIME", "Load must consume its explicit loading duration", e)
                matching = [x for x in events if x["kind"] == "load_start" and x.get("vehicle_id") == vid and x["time"] == start]
                if len(matching) != 1 or matching[0].get("manifest") != e.get("manifest"):
                    fail("LOAD_TIME", "Completed load has no matching start/manifest", e)
            manifest = e.get("manifest", {e.get("commodity"): e.get("quantity")})
            for c, amount in manifest.items():
                q = quantity(amount, e)
                if c not in COMMODITIES:
                    fail("COMMODITY", "Load contains unknown commodity", e)
                    continue
                stock[c] -= q
                cargo[vid][c] += q
                if stock[c] < 0:
                    fail("INVENTORY", f"Depot {c} stock became negative", e)
            if cargo[vid]["chilled"] and not vehicles[vid]["chilled"]:
                fail("COMPATIBILITY", f"Vehicle {vid} loaded chilled meals without refrigeration", e)
            if sum(cargo[vid].values()) > vehicles[vid]["capacity"]:
                fail("CAPACITY", f"Vehicle {vid} exceeds capacity including unused cargo", e)
        elif kind == "delivery":
            c = e.get("commodity")
            q = quantity(e.get("quantity"), e)
            if c not in COMMODITIES:
                fail("COMMODITY", "Delivery event has unknown commodity", e)
                continue
            cargo[vid][c] -= q
            transferred[c] += q
            if cargo[vid][c] < 0:
                fail("CUSTODY", f"Vehicle {vid} delivers meals it never possessed", e)
            if not any(d["id"] == e.get("delivery_id", e.get("id")) for d in deliveries):
                fail("DELIVERY_LEDGER", "Completion event has no delivery record", e)
        elif kind == "breakdown":
            expected = dict(cargo[vid])
            if "stranded" in e and any(e["stranded"].get(c, 0) != expected[c] for c in COMMODITIES):
                fail("STRANDED", f"Vehicle {vid} stranded cargo differs from reconstructed custody", e)
            for c in COMMODITIES:
                stranded[c] += cargo[vid][c]
                cargo[vid][c] = 0
        elif kind in ("unload", "transfer", "rescue"):
            fail("CUSTODY", "Cross-vehicle transfer/rescue/unload is not permitted", e)

    for c in COMMODITIES:
        total = stock[c] + sum(cargo[v][c] for v in vehicles) + stranded[c] + transferred[c]
        if total != scenario["inventory"].get(c, 0):
            fail("CUSTODY", f"Global {c} conservation failed")

    demand = sum(n.get("demand", 0) for n in nodes.values() if n["kind"] == "destination")
    priority_demand = sum(n.get("demand", 0) for n in nodes.values() if n.get("priority") == 3)
    weighted_demand = sum(n.get("demand", 0) * n.get("priority", 0) for n in nodes.values() if n["kind"] == "destination")
    meals = sum(d["quantity"] for d in delivered_records)
    on_time = sum(d["quantity"] for d in delivered_records if d["completed_at"] <= nodes[d["destination_id"]]["due"])
    priority_meals = sum(d["quantity"] for d in delivered_records if nodes[d["destination_id"]]["priority"] == 3 and d["completed_at"] <= nodes[d["destination_id"]]["due"])
    weighted_meals = sum(d["quantity"] * nodes[d["destination_id"]]["priority"] for d in delivered_records if d["completed_at"] <= nodes[d["destination_id"]]["due"])
    ratio = lambda a, b: min(1.0, max(0.0, a / b)) if b else 0.0
    return {"meals_delivered": meals, "demand": demand, "coverage": ratio(meals, demand),
            "on_time_meals": on_time, "on_time_coverage": ratio(on_time, demand),
            "priority_coverage": ratio(priority_meals, priority_demand),
            "priority_weighted_coverage": ratio(weighted_meals, weighted_demand),
            "destinations_served": len(served),
            "late_deliveries": sum(d["completed_at"] > nodes[d["destination_id"]]["due"] for d in delivered_records),
            "unserved_meals": max(0, demand - meals), "distance_m": round(sum(distance.values()), 4),
            "cost_cents": sum(round(distance[v] * vehicles[v]["cost_per_km"] / 1000) for v in vehicles),
            "emissions_g": sum(round(distance[v] * vehicles[v]["emissions_per_km"] / 1000) for v in vehicles)}
