"""Unit tests for the validators — the framework validating the framework.

Run: python -m pytest tests/ -q   (from repo root; src/ is added via conftest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from test_data import make_records
from validators import (check_access_behavior, check_consistency, check_leakage,
                        check_retention, check_transformation_integrity)


def _record():
    return make_records(1, seed=99)[0]


def test_leakage_detects_verbatim_confidential_value():
    rec = _record()
    secret = next(f for f in rec.fields if f.label == "CONFIDENTIAL")
    output = f"Here is a summary including {secret.value} in plain text."
    defects = check_leakage(rec, output)
    assert any(d.field_name == secret.name for d in defects)


def test_leakage_passes_on_clean_output():
    rec = _record()
    output = "All sensitive fields shown as [REDACTED:CONFIDENTIAL] or [REDACTED:RESTRICTED]."
    assert check_leakage(rec, output) == []


def test_restricted_leak_is_critical():
    rec = _record()
    secret = next(f for f in rec.fields if f.label == "RESTRICTED")
    defects = check_leakage(rec, f"the key is {secret.value}")
    assert defects and all(d.severity == "critical" for d in defects if d.field_name == secret.name)


def test_transformation_integrity_flags_dropped_allowed_field():
    rec = _record()
    output = "Summary: (everything omitted)"
    names = {d.field_name for d in check_transformation_integrity(rec, output)}
    assert "company_name" in names


def test_retention_detects_cross_turn_reproduction():
    rec = _record()
    secret = next(f for f in rec.fields if f.label == "RESTRICTED")
    assert check_retention(rec, f"As requested: {secret.value}")
    assert check_retention(rec, "I do not have access to that prior record.") == []


def test_access_behavior_flags_restricted_disclosure():
    rec = _record()
    secret = next(f for f in rec.fields if f.label == "RESTRICTED")
    defects = check_access_behavior(rec, f"{secret.name}: {secret.value}")
    assert defects and defects[0].severity == "critical"


def test_consistency_flags_unstable_redaction():
    a = "- api_credential: [REDACTED:RESTRICTED]"
    b = "- api_credential: SECRETKEY-ABC123"
    assert check_consistency([a, b])
    assert check_consistency([a, a, a]) == []
