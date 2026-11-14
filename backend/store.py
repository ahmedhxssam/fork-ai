"""Transactional SQLite snapshots and idempotent command receipts."""

import json
import sqlite3
from pathlib import Path


class ExperimentStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS commands (
                    scope TEXT NOT NULL, key TEXT NOT NULL, body_hash TEXT NOT NULL,
                    response TEXT NOT NULL, PRIMARY KEY (scope, key)
                );
            """)

    def _connection(self):
        connection = sqlite3.connect(self.path, timeout=20)
        connection.execute("PRAGMA busy_timeout=20000")
        return connection

    def get(self, experiment_id: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute("SELECT payload FROM experiments WHERE id=?",
                                     (experiment_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, experiment: dict, command: tuple | None = None) -> None:
        payload = json.dumps(experiment, allow_nan=False, separators=(",", ":"))
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO experiments VALUES (?,?,?) ON CONFLICT(id) DO UPDATE "
                "SET revision=excluded.revision,payload=excluded.payload",
                (experiment["id"], experiment["revision"], payload))
            if command:
                scope, key, body_hash, response = command
                connection.execute("INSERT INTO commands VALUES (?,?,?,?)",
                    (scope, key, body_hash, json.dumps(response, allow_nan=False)))

    def command(self, scope: str, key: str, body_hash: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute("SELECT body_hash,response FROM commands WHERE scope=? AND key=?",
                                     (scope, key)).fetchone()
        if not row:
            return None
        if row[0] != body_hash:
            raise ValueError("Idempotency key was already used with different arguments.")
        return json.loads(row[1])

    def record_command(self, scope: str, key: str, body_hash: str, response: dict):
        with self._connection() as connection:
            connection.execute("INSERT INTO commands VALUES (?,?,?,?)",
                (scope, key, body_hash, json.dumps(response, allow_nan=False)))
