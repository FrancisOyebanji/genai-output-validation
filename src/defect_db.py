"""SQL logging layer: every run, test execution, and defect lands in SQLite.

Schema is deliberately governance-shaped: a compliance reviewer should be able
to answer "which model, which policy, which field class, when, and how often"
with plain SQL — no Python required.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    model_name  TEXT NOT NULL,
    policy      TEXT NOT NULL,          -- e.g. 'redact_at=CONFIDENTIAL'
    n_records   INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS executions (
    exec_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES runs(run_id),
    record_id   TEXT NOT NULL,
    check_name  TEXT NOT NULL,
    passed      INTEGER NOT NULL,        -- 1 pass / 0 fail
    executed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS defects (
    defect_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id     INTEGER NOT NULL REFERENCES executions(exec_id),
    run_id      INTEGER NOT NULL REFERENCES runs(run_id),
    check_name  TEXT NOT NULL,
    severity    TEXT NOT NULL CHECK (severity IN ('critical','high','medium','low')),
    field_name  TEXT NOT NULL,
    label       TEXT NOT NULL,
    detail      TEXT NOT NULL
);
CREATE VIEW IF NOT EXISTS v_defect_summary AS
    SELECT r.model_name, d.check_name, d.severity, COUNT(*) AS defect_count
    FROM defects d JOIN runs r USING (run_id)
    GROUP BY r.model_name, d.check_name, d.severity;
CREATE VIEW IF NOT EXISTS v_pass_rates AS
    SELECT r.model_name, e.check_name,
           ROUND(100.0 * SUM(e.passed) / COUNT(*), 1) AS pass_rate_pct,
           COUNT(*) AS executions
    FROM executions e JOIN runs r USING (run_id)
    GROUP BY r.model_name, e.check_name;
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DefectDB:
    def __init__(self, path: str = "reports/defects.db"):
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def start_run(self, model_name: str, policy: str, n_records: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (started_at, model_name, policy, n_records) VALUES (?,?,?,?)",
            (_now(), model_name, policy, n_records))
        self.conn.commit()
        return cur.lastrowid

    def log_execution(self, run_id: int, record_id: str, check_name: str, defects: list) -> None:
        cur = self.conn.execute(
            "INSERT INTO executions (run_id, record_id, check_name, passed, executed_at) VALUES (?,?,?,?,?)",
            (run_id, record_id, check_name, int(not defects), _now()))
        exec_id = cur.lastrowid
        for d in defects:
            self.conn.execute(
                "INSERT INTO defects (exec_id, run_id, check_name, severity, field_name, label, detail) "
                "VALUES (?,?,?,?,?,?,?)",
                (exec_id, run_id, d.check, d.severity, d.field_name, d.label, d.detail))
        self.conn.commit()

    def summary(self) -> list[tuple]:
        return self.conn.execute("SELECT * FROM v_pass_rates ORDER BY model_name, check_name").fetchall()

    def defect_summary(self) -> list[tuple]:
        return self.conn.execute("SELECT * FROM v_defect_summary ORDER BY defect_count DESC").fetchall()
