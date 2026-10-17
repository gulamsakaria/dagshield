"""Evaluation: run the labeled synthetic fixtures and report ACTUAL counts.

Nothing here is a claim about real-world accuracy. The fixtures are small and synthetic,
so the results only show that the rules behave as designed.
"""

from __future__ import annotations

from typing import Any

from .auditlog.chain import GENESIS, make_entry, verify_chain
from .integrity.canonical import make_record, record_hash
from .integrity.signing import Signer
from .integrity.verify import verify_copy
from .rules import Dataset, RuleParams, run_audit

NOTE = (
    "These counts come from small, labeled, synthetic fixtures. They show the rules behave as "
    "designed; they say nothing about how the rules would perform on real land records."
)


def _rule_cases(fixtures: list[dict[str, Any]], params: RuleParams) -> list[dict[str, Any]]:
    cases = []
    for fx in fixtures:
        findings = run_audit(Dataset.from_dict(fx), params)
        again = run_audit(Dataset.from_dict(fx), params)
        actual = {f.match_key() for f in findings}
        expected = {(e["rule_id"], e["key"], e["outcome"]) for e in fx.get("expected_alerts", [])}
        cases.append(
            {
                "id": fx["scenario_id"],
                "name": fx["name"],
                "kind": "rule",
                "expected": sorted(expected),
                "actual": sorted(actual),
                "tp": len(actual & expected),
                "fp": len(actual - expected),
                "fn": len(expected - actual),
                "repeatable": [f.to_dict() for f in findings] == [f.to_dict() for f in again],
                "passed": actual == expected,
            }
        )
    return cases


def _integrity_cases(signer: Signer) -> list[dict[str, Any]]:
    rec = make_record("DEED-EVAL-1", "2024-03-10", "registered", "OWNER-A", "BUYER-B", "P-EVAL-1", 5, "SRC-EVAL")
    h = record_hash(rec)
    stored = {"record": rec, "hash": h, "signature": signer.sign(h)}
    genuine = verify_copy(signer, stored, dict(rec), h, stored["signature"])
    tampered_fields = dict(rec)
    tampered_fields["area_decimal"] = "6.0000"
    tampered = verify_copy(signer, stored, tampered_fields, h, stored["signature"])

    e1 = make_entry(GENESIS, "deed_signed", "D1", {"a": 1}, "2024-01-01T00:00:00+00:00")
    e2 = make_entry(e1["entry_hash"], "deed_verified", "D1", {"a": 2}, "2024-01-01T00:01:00+00:00")
    e3 = make_entry(e2["entry_hash"], "deed_verified", "D1", {"a": 3}, "2024-01-01T00:02:00+00:00")
    intact = verify_chain([e1, e2, e3])
    edited = verify_chain([e1, {**e2, "payload_hash": "f" * 64}, e3])

    def case(cid, name, expected, actual):
        return {
            "id": cid,
            "name": name,
            "kind": "integrity",
            "expected": expected,
            "actual": actual,
            "passed": expected == actual,
        }

    return [
        case("genuine-deed", "Genuine deed copy", "match", genuine["result"]),
        case("tampered-deed", "One field edited", "mismatch", tampered["result"]),
        case("intact-log", "Untouched audit log", "chain ok", "chain ok" if intact.ok else "chain broken"),
        case("broken-log", "One audit log entry edited", "chain broken", "chain ok" if edited.ok else "chain broken"),
    ]


def evaluate(fixtures: list[dict[str, Any]], params: RuleParams, signer: Signer) -> dict[str, Any]:
    rule_cases = _rule_cases(fixtures, params)
    integrity_cases = _integrity_cases(signer)
    per_rule: dict[str, dict[str, int]] = {}
    for c in rule_cases:
        expected = {tuple(x) for x in c["expected"]}
        actual = {tuple(x) for x in c["actual"]}
        for rule_id in {x[0] for x in expected | actual}:
            bucket = per_rule.setdefault(rule_id, {"tp": 0, "fp": 0, "fn": 0})
            bucket["tp"] += len({x for x in actual & expected if x[0] == rule_id})
            bucket["fp"] += len({x for x in actual - expected if x[0] == rule_id})
            bucket["fn"] += len({x for x in expected - actual if x[0] == rule_id})
    return {
        "synthetic_notice": "Synthetic data only. Not real land records.",
        "note": NOTE,
        "totals": {
            "tp": sum(c["tp"] for c in rule_cases),
            "fp": sum(c["fp"] for c in rule_cases),
            "fn": sum(c["fn"] for c in rule_cases),
            "cases": len(rule_cases) + len(integrity_cases),
            "passed": sum(1 for c in rule_cases + integrity_cases if c["passed"]),
        },
        "per_rule": dict(sorted(per_rule.items())),
        "repeatability_ok": all(c["repeatable"] for c in rule_cases),
        "cases": rule_cases + integrity_cases,
    }
