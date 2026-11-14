"""Local FORK API: real experiments, durable evidence, human-approved exports."""

import copy
import csv
import hashlib
import io
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.comparison import DEFAULT_WEIGHTS, compare_worlds
from backend.store import ExperimentStore

ROOT = Path(__file__).resolve().parent.parent
POLICIES = ("velocity", "resilience", "equity")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


class NewExperiment(BaseModel):
    seed: int = Field(default=26, ge=0, le=2**31 - 1)


class Shock(BaseModel):
    vehicle_id: Literal["A", "B", "C"]
    time: int = Field(ge=0, le=14400)


class Preferences(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    coverage: float = Field(ge=0, le=1)
    equity: float = Field(ge=0, le=1)
    cost: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def positive_total(self):
        if self.coverage + self.equity + self.cost <= 0:
            raise ValueError("At least one preference must be positive.")
        return self


class Approval(BaseModel):
    world_id: Literal["velocity", "resilience", "equity"]
    revision: int = Field(ge=1)


def compute_world(scenario, policy, plan=None, disruption=None, adapt=True):
    from backend.fork_engine.planner import plan_world
    from backend.fork_engine.simulation import simulate_world
    from backend.fork_engine.verifier import verify_world
    started = time.perf_counter()
    own_scenario = copy.deepcopy(scenario)
    selected_plan = copy.deepcopy(plan) if plan is not None else plan_world(own_scenario, policy)
    result = simulate_world(own_scenario, selected_plan, copy.deepcopy(disruption), adapt=adapt)
    receipt = verify_world(own_scenario, result)
    result["verification"] = receipt
    result["metrics"] = receipt["metrics"]
    result["compute_seconds"] = round(time.perf_counter() - started, 4)
    return result


def compute_benchmark(scenario, kind, disruption=None, plan=None):
    from backend.fork_engine.planner import plan_baseline
    result = compute_world(scenario, "velocity", plan or plan_baseline(scenario, kind), disruption)
    result["id"] = kind
    result["name"] = "Nearest-feasible greedy" if kind == "greedy" else "Neutral solver only"
    return result


def create_app(store_path: str | Path | None = None):
    application = FastAPI(title="FORK — Decision Laboratory", version="1.0.0",
                          description="Synthetic executable logistics experiments. No real dispatch.")
    store = ExperimentStore(store_path or os.environ.get("FORK_DB_PATH", ROOT / "data/fork.sqlite"))
    mutation_lock = threading.RLock()
    application.state.store = store

    def get_experiment(experiment_id):
        value = store.get(experiment_id)
        if value is None:
            raise HTTPException(404, "Experiment not found. Launch a new simulation.")
        return value

    def cached(scope, key, body):
        if not key:
            return None
        if len(key) > 160:
            raise HTTPException(422, "Idempotency key is too long.")
        try:
            return store.command(scope, key, digest(body))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    def persist(exp, scope, key, body, response=None):
        response = exp if response is None else response
        command = (scope, key, digest(body), response) if key else None
        store.save(exp, command=command)
        return response

    @application.get("/api/health")
    def health():
        return {"status": "ok", "mode": "deterministic", "version": "1.0.0",
                "synthetic": True, "external_dispatch": False}

    @application.get("/api/scenario")
    def scenario(seed: int = Query(26, ge=0, le=2**31-1)):
        from backend.fork_engine.scenario import create_scenario
        return create_scenario(seed)

    @application.post("/api/experiments")
    def launch(body: NewExperiment, idempotency_key: str | None = Header(None)):
        from backend.fork_engine.scenario import create_scenario
        payload = body.model_dump()
        with mutation_lock:
            previous = cached("launch", idempotency_key, payload)
            if previous:
                return previous
            initial = create_scenario(body.seed)
            with ThreadPoolExecutor(max_workers=3, thread_name_prefix="fork-world") as pool:
                futures = [pool.submit(compute_world, initial, policy) for policy in POLICIES]
                worlds = [future.result() for future in futures]
            benchmarks = [compute_benchmark(initial, kind) for kind in ("greedy", "solver_only")]
            exp = {"id": uuid.uuid4().hex[:16], "scenario": initial, "worlds": worlds,
                   "baseline_worlds": copy.deepcopy(worlds), "disruption": None,
                   "benchmarks": benchmarks, "baseline_benchmarks": copy.deepcopy(benchmarks),
                   "comparison": compare_worlds(worlds), "mode": "deterministic",
                   "created_at": now(), "revision": 1, "approved": None,
                   "activity": [{"id": f"plan-{w['id']}", "world_id": w["id"],
                                 "agent": w["name"] + " Strategist", "tool": "optimize_routes",
                                 "mode": "deterministic", "timestamp": now(),
                                 "summary": f"Computed {len(w['deliveries'])} delivery assignments; "
                                            f"independent verification {'passed' if w['verification']['valid'] else 'failed'}.",
                                 "duration_seconds": w["compute_seconds"]} for w in worlds]}
            return persist(exp, "launch", idempotency_key, payload)

    @application.get("/api/experiments/{experiment_id}")
    def get(experiment_id: str):
        return get_experiment(experiment_id)

    @application.post("/api/experiments/{experiment_id}/disrupt")
    def disrupt(experiment_id: str, body: Shock, idempotency_key: str | None = Header(None)):
        payload, scope = body.model_dump(), f"{experiment_id}/disrupt"
        with mutation_lock:
            previous = cached(scope, idempotency_key, payload)
            if previous:
                return previous
            exp = get_experiment(experiment_id)
            initial = exp["scenario"]
            originals = exp["baseline_worlds"]
            with ThreadPoolExecutor(max_workers=3, thread_name_prefix="fork-recover") as pool:
                adaptive = [pool.submit(compute_world, initial, w["policy"], w["plan"], payload, True)
                            for w in originals]
                worlds = [future.result() for future in adaptive]
                frozen = [pool.submit(compute_world, initial, w["policy"], w["plan"], payload, False)
                          for w in originals]
                unadapted = [future.result() for future in frozen]
            for index, world in enumerate(worlds):
                world["baseline_metrics"] = originals[index]["verification"]["metrics"]
                world["unadapted_metrics"] = unadapted[index]["verification"]["metrics"]
                world["unadapted_verification"] = unadapted[index]["verification"]
                world["recovery_gain"] = (world["metrics"]["meals_delivered"]
                                           - world["unadapted_metrics"]["meals_delivered"])
                world["adaptation_delta"] = {key: world["metrics"][key] - world["baseline_metrics"][key]
                                            for key in ("meals_delivered", "cost_cents", "distance_m", "emissions_g")}
            benchmarks = [compute_benchmark(initial, benchmark["id"], payload, benchmark["plan"])
                          for benchmark in exp.get("baseline_benchmarks", [])]
            exp.update(worlds=worlds, disruption=payload, approved=None, revision=exp["revision"] + 1,
                       benchmarks=benchmarks, comparison=compare_worlds(worlds, exp["comparison"]["weights"]))
            exp["activity"] += [{"id": f"replan-{exp['revision']}-{w['id']}", "world_id": w["id"],
                "agent": w["name"] + " Strategist", "tool": "replan_remaining_routes",
                "mode": "deterministic", "timestamp": now(), "duration_seconds": w["compute_seconds"],
                "summary": f"Vehicle {body.vehicle_id} unavailable. {w['recovery_gain']:+d} meals versus no adaptation; "
                           f"verification {'passed' if w['verification']['valid'] else 'failed'}."} for w in worlds]
            return persist(exp, scope, idempotency_key, payload)

    @application.post("/api/experiments/{experiment_id}/preferences")
    def preferences(experiment_id: str, body: Preferences):
        with mutation_lock:
            exp = get_experiment(experiment_id)
            exp["comparison"] = compare_worlds(exp["worlds"], body.model_dump())
            exp["approved"] = None
            exp["revision"] += 1
            store.save(exp)
            return dict(exp["comparison"], revision=exp["revision"])

    @application.post("/api/experiments/{experiment_id}/approve")
    def approve(experiment_id: str, body: Approval, idempotency_key: str | None = Header(None)):
        scope, payload = f"{experiment_id}/approve", body.model_dump()
        with mutation_lock:
            previous = cached(scope, idempotency_key, payload)
            if previous:
                return previous
            exp = get_experiment(experiment_id)
            if body.revision != exp["revision"]:
                raise HTTPException(409, "The experiment changed. Review the current revision before approving.")
            world = next((w for w in exp["worlds"] if w["id"] == body.world_id), None)
            if world is None or not world["verification"]["valid"]:
                raise HTTPException(409, "Only a currently verified plan may be approved.")
            decision = {"id": uuid.uuid4().hex[:12], "world_id": body.world_id,
                        "experiment_id": experiment_id, "revision": exp["revision"],
                        "approved_at": now(), "label": "Human-approved simulated plan",
                        "evidence_hash": digest(world), "preferences_hash": digest(exp["comparison"])}
            exp["approved"] = decision
            return persist(exp, scope, idempotency_key, payload, decision)

    @application.get("/api/experiments/{experiment_id}/export")
    def export(experiment_id: str, world_id: str, format: Literal["json", "csv"] = "json"):
        exp = get_experiment(experiment_id)
        decision = exp.get("approved")
        world = next((w for w in exp["worlds"] if w["id"] == world_id), None)
        if not decision or world is None or decision["world_id"] != world_id \
                or decision["revision"] != exp["revision"] or decision["evidence_hash"] != digest(world):
            raise HTTPException(409, "Approve this verified plan's current revision before exporting.")
        artifact = {"schema_version": 1, "synthetic": True, "external_dispatch": False,
                    "decision": decision, "scenario": exp["scenario"], "disruption": exp["disruption"],
                    "world": world, "comparison": exp["comparison"],
                    "limitations": exp["scenario"].get("assumptions", [])}
        filename = f"FORK-{experiment_id}-{world_id}-r{exp['revision']}.{format}"
        if format == "json":
            return Response(json.dumps(artifact, indent=2, allow_nan=False), media_type="application/json",
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})
        output = io.StringIO()
        fields = ["vehicle_id", "volunteer_id", "stop_order", "destination_id", "destination",
                  "commodity", "quantity", "service_start_seconds", "completed_at_seconds",
                  "on_time", "status", "plan_revision"]
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        nodes = {node["id"]: node for node in exp["scenario"]["nodes"]}
        vehicles = {vehicle["id"]: vehicle for vehicle in exp["scenario"]["vehicles"]}
        counts = {}
        for delivery in sorted(world["deliveries"], key=lambda d: (d["vehicle_id"], d["completed_at"])):
            vehicle_id = delivery["vehicle_id"]
            counts[vehicle_id] = counts.get(vehicle_id, 0) + 1
            destination = nodes[delivery["destination_id"]]["name"]
            if destination.startswith(("=", "+", "-", "@")):
                destination = "'" + destination
            writer.writerow({"vehicle_id": vehicle_id,
                "volunteer_id": vehicles[vehicle_id]["driver_id"], "stop_order": counts[vehicle_id],
                "destination_id": delivery["destination_id"], "destination": destination,
                "commodity": delivery["commodity"], "quantity": delivery["quantity"],
                "service_start_seconds": delivery["service_start"],
                "completed_at_seconds": delivery["completed_at"], "on_time": delivery["on_time"],
                "status": "simulated completion", "plan_revision": exp["revision"]})
        return Response(output.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    @application.get("/api/experiments/{experiment_id}/events")
    def events(experiment_id: str, last_event_id: str | None = Header(None)):
        exp = get_experiment(experiment_id)
        try:
            cursor = int(last_event_id or -1)
        except ValueError:
            raise HTTPException(422, "Last-Event-ID must be an integer cursor.")
        records = sorted([dict(event, world_id=w["id"]) for w in exp["worlds"]
                          for event in w["events"]], key=lambda e: (e["time"], e["world_id"], e["seq"]))
        def stream():
            for index, record in enumerate(records):
                if index > cursor:
                    yield f"id: {index}\nevent: simulation\ndata: {json.dumps(record)}\n\n"
            yield 'event: complete\ndata: {}\n\n'
        return StreamingResponse(stream(), media_type="text/event-stream")

    dist = ROOT / "frontend/dist"
    if (dist / "assets").exists():
        application.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @application.get("/")
    def index():
        if (dist / "index.html").exists():
            return FileResponse(dist / "index.html")
        return {"message": "FORK API ready. Start the frontend dev server or build frontend/dist.",
                "docs": "/docs", "health": "/api/health"}

    return application


app = create_app()
