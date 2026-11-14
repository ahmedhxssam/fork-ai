"""Generate reproducible genuine demo receipts and paired recovery comparisons."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.main import compute_benchmark, compute_world
from backend.fork_engine.scenario import create_scenario


def main():
    started = time.perf_counter()
    scenario = create_scenario(26)
    baseline = [compute_world(scenario, policy) for policy in ("velocity", "resilience", "equity")]
    cases = []
    for vehicle in ("A", "B", "C"):
        for at in (0, 1500, 1800, 2700, 5400, 14400):
            shock = {"vehicle_id": vehicle, "time": at}
            worlds = []
            for original in baseline:
                recovered = compute_world(scenario, original["policy"], original["plan"], shock)
                fixed = compute_world(scenario, original["policy"], original["plan"], shock, False)
                assert recovered["verification"]["valid"], recovered["verification"]["violations"]
                assert fixed["verification"]["valid"], fixed["verification"]["violations"]
                worlds.append({"id": original["id"], "adaptive": recovered["metrics"],
                    "fixed": fixed["metrics"], "recovered_meals": recovered["metrics"]["meals_delivered"]
                        - fixed["metrics"]["meals_delivered"],
                    "event_hash": recovered["verification"]["event_hash"]})
            cases.append({"shock": shock, "worlds": worlds})
    artifact = {"scenario_hash": scenario["hash"], "seed": 26, "mode": "deterministic",
        "baseline": [{"id": w["id"], "metrics": w["metrics"],
                      "receipt": w["verification"]} for w in baseline],
        "benchmarks": [{"id": kind, "metrics": compute_benchmark(scenario, kind)["metrics"]}
                       for kind in ("greedy", "solver_only")], "cases": cases,
        "execution_seconds": round(time.perf_counter() - started, 4)}
    destination = ROOT / "artifacts/demo-evidence.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n")
    print(f"Verified {len(cases)} paired disruption cases / {len(cases)*6} executions.")
    print(f"Evidence saved: {destination}")


if __name__ == "__main__":
    main()
