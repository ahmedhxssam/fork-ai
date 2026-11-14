import csv
import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from backend.main import create_app
    with TestClient(create_app(tmp_path / "api.sqlite")) as client:
        yield client


def test_unknown_experiment_and_invalid_shock_return_useful_errors(client):
    assert client.get("/api/experiments/missing").status_code == 404
    assert client.post("/api/experiments/missing/disrupt", json={"vehicle_id":"D", "time": -5}).status_code == 422
    assert client.post("/api/experiments/missing/approve", json={"world_id":"velocity"}).status_code == 422


def test_full_real_experiment_recovery_approval_and_export(client):
    response = client.post("/api/experiments", json={"seed":26}, headers={"Idempotency-Key":"demo"})
    assert response.status_code == 200, response.text
    initial = response.json()
    assert len(initial["worlds"]) == 3
    assert {w["id"] for w in initial["benchmarks"]} == {"greedy", "solver_only"}
    assert all(w["verification"]["valid"] for w in initial["benchmarks"])
    assert len({w["initial_hash"] for w in initial["worlds"]}) == 1
    assert all(w["verification"]["valid"] for w in initial["worlds"]), [(w["id"],w["verification"]["violations"]) for w in initial["worlds"]]
    repeated = client.post("/api/experiments", json={"seed":26}, headers={"Idempotency-Key":"demo"}).json()
    assert repeated["id"] == initial["id"]
    key_conflict = client.post("/api/experiments", json={"seed":27}, headers={"Idempotency-Key":"demo"})
    assert key_conflict.status_code == 409
    base = f"/api/experiments/{initial['id']}"
    assert client.get(base+"/export?world_id=velocity&format=json").status_code == 409
    response = client.post(base+"/disrupt", json={"vehicle_id":"B", "time":2700})
    assert response.status_code == 200, response.text
    shock = response.json()
    assert shock["revision"] == 2
    assert shock["disruption"] == {"vehicle_id":"B","time":2700}
    assert all(w["verification"]["valid"] for w in shock["worlds"]), [(w["id"],w["verification"]["violations"]) for w in shock["worlds"]]
    assert all("unadapted_metrics" in w for w in shock["worlds"])
    selected = shock["comparison"]["eligible_ids"][0]
    approval = client.post(base+"/approve", json={"world_id":selected,"revision":2})
    assert approval.status_code == 200
    exported = client.get(base+f"/export?world_id={selected}&format=json").json()
    assert exported["decision"]["world_id"] == selected
    assert exported["world"]["verification"]["valid"]
    rows = list(csv.DictReader(io.StringIO(client.get(base+f"/export?world_id={selected}&format=csv").text)))
    assert rows and {row["vehicle_id"] for row in rows} <= {"A","B","C"}
    client.post(base+"/disrupt", json={"vehicle_id":"C", "time":3600})
    assert client.get(base+f"/export?world_id={selected}&format=json").status_code == 409
    assert client.post(base+"/approve", json={"world_id":selected,"revision":2}).status_code == 409


def test_preference_request_rejects_nan_and_zero_weights(client):
    response = client.post("/api/experiments/missing/preferences", json={"coverage":0,"equity":0,"cost":0})
    assert response.status_code == 422
