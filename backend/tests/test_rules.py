"""Golden tests for R1-R5: clean, conflict, cancelled, missing-value and uncertain-lineage cases."""

import time
from datetime import date
from decimal import Decimal

import pytest

from app.rules import Dataset, RuleParams, run_audit
from app.rules.common import ownership_summary
from app.rules.messages import BANNED_PHRASES

from .conftest import load_fixtures

FIXTURES = load_fixtures()


@pytest.mark.parametrize("fx", FIXTURES, ids=[f["scenario_id"] for f in FIXTURES])
def test_golden_fixture_matches_expected(fx):
    got = {f.match_key() for f in run_audit(Dataset.from_dict(fx))}
    expected = {(e["rule_id"], e["key"], e["outcome"]) for e in fx["expected_alerts"]}
    assert got == expected


def by_id(fixtures, sid):
    return next(f for f in fixtures if f["scenario_id"] == sid)


def test_clean_transfer_has_no_alert_and_balance_is_7(fixtures):
    fx = by_id(fixtures, "clean-transfer")
    ds = Dataset.from_dict(fx)
    assert run_audit(ds) == []
    owner_a = next(o for o in ownership_summary(ds, "P-S01-A") if o["owner"] == "OWNER-A")
    assert owner_a["balance"] == 7


def test_r2_shows_available_3_and_excess_2(fixtures):
    findings = run_audit(Dataset.from_dict(by_id(fixtures, "excess-transfer")))
    (f,) = [x for x in findings if x.rule_id == "R2"]
    assert f.key == "S02-T2"
    assert (f.calc["opening"], f.calc["prior_active_outgoing"]) == (12, 9)
    assert (f.calc["available"], f.calc["attempted"], f.calc["excess"]) == (3, 5, 2)
    assert {"S02-T1", "S02-T2", "S02-E1"} <= set(f.evidence_ids)


def test_r1_links_both_records(fixtures):
    (f,) = run_audit(Dataset.from_dict(by_id(fixtures, "duplicate-portion")))
    assert f.rule_id == "R1" and {"S03-T1", "S03-T2"} <= set(f.evidence_ids)


def test_same_dag_alone_is_not_an_r1_conflict(fixtures):
    fx = by_id(fixtures, "duplicate-portion")
    fx["transfers"][1]["portion_key"] = "PK-OTHER"
    assert [f for f in run_audit(Dataset.from_dict(fx)) if f.rule_id == "R1"] == []


def test_r3_wording_is_not_a_fraud_label(fixtures):
    (f,) = run_audit(Dataset.from_dict(by_id(fixtures, "missing-mutation")))
    assert "not found in supplied dataset" in f.message_en
    assert "fraud" not in f.message_en.lower()


def test_r3_flags_mismatching_mutation(fixtures):
    fx = by_id(fixtures, "clean-transfer")
    fx["mutations"][0]["recipient"] = "BUYER-Z"
    (f,) = run_audit(Dataset.from_dict(fx))
    assert f.rule_id == "R3" and "do not align" in f.message_en


def test_r4_ambiguous_lineage_needs_review_not_merge(fixtures):
    (f,) = run_audit(Dataset.from_dict(by_id(fixtures, "ambiguous-lineage")))
    assert f.rule_id == "R4" and f.calc["confidence"] == 0.4
    assert "Not merged automatically" in f.message_en


def test_r4_child_area_difference_is_2(fixtures):
    (f,) = run_audit(Dataset.from_dict(by_id(fixtures, "child-area-anomaly")))
    assert (f.calc["parent_area"], f.calc["children_total"], f.calc["difference"]) == (20, 22, 2)


def test_r4_tolerance_is_respected(fixtures):
    ds = Dataset.from_dict(by_id(fixtures, "child-area-anomaly"))
    assert run_audit(ds, RuleParams(area_tolerance=Decimal("2"))) == []


def test_missing_value_is_insufficient_data_never_zero(fixtures):
    findings = run_audit(Dataset.from_dict(by_id(fixtures, "missing-value")))
    assert findings and all(f.outcome == "insufficient_data" for f in findings)
    assert all("not treated as zero" in f.message_en for f in findings)


def test_missing_date_is_insufficient_data(fixtures):
    fx = by_id(fixtures, "clean-transfer")
    fx["transfers"][0]["event_date"] = None
    (f,) = [x for x in run_audit(Dataset.from_dict(fx)) if x.rule_id == "R2"]
    assert f.outcome == "insufficient_data"


def test_missing_entitlement_is_insufficient_data(fixtures):
    fx = by_id(fixtures, "clean-transfer")
    fx["entitlements"] = []
    (f,) = [x for x in run_audit(Dataset.from_dict(fx)) if x.rule_id == "R2"]
    assert f.outcome == "insufficient_data"


def test_cancellation_stops_counting_only_after_it_takes_effect(fixtures):
    fx = by_id(fixtures, "excess-transfer")
    t1 = fx["transfers"][0]
    t1["status"], t1["cancelled_on"] = "cancelled", "2024-03-01"  # effective BEFORE T2 on 03-15
    assert [f for f in run_audit(Dataset.from_dict(fx)) if f.rule_id == "R2"] == []
    t1["cancelled_on"] = "2024-04-01"  # effective AFTER T2: T1 still counted when T2 happened
    assert [f.key for f in run_audit(Dataset.from_dict(fx)) if f.rule_id == "R2"] == ["S02-T2"]


def test_same_day_events_are_tie_broken_by_event_id(fixtures):
    fx = by_id(fixtures, "excess-transfer")
    for t in fx["transfers"]:
        t["event_date"] = "2024-02-01"
    keys = [f.key for f in run_audit(Dataset.from_dict(fx)) if f.rule_id == "R2"]
    assert keys == ["S02-T2"]  # T1 is ordered first, so T2 is the one that overshoots


def test_r5_is_a_labelled_heuristic_and_configurable(fixtures):
    ds = Dataset.from_dict(by_id(fixtures, "rapid-transfers"))
    (f,) = run_audit(ds)
    assert f.heuristic and "Heuristic only" in f.message_en
    assert run_audit(ds, RuleParams(rapid_window_days=5)) == []
    assert run_audit(ds, RuleParams(enable_r5=False)) == []


def test_repeatability_same_input_same_output(fixtures):
    for fx in fixtures:
        a = [f.to_dict() for f in run_audit(Dataset.from_dict(fx))]
        b = [f.to_dict() for f in run_audit(Dataset.from_dict(fx))]
        assert a == b


def test_every_alert_is_complete_and_honestly_worded(fixtures):
    for fx in fixtures:
        for f in run_audit(Dataset.from_dict(fx)):
            assert f.rule_id and f.rule_version and f.severity and f.evidence_ids
            assert f.message_en and f.message_bn and f.next_check_en and f.next_check_bn
            text = (f.message_en + f.next_check_en).lower()
            assert not any(p in text for p in BANNED_PHRASES)


def test_rules_are_fast_on_1000_records():
    parcels, ents, deeds, transfers, muts = [], [], [], [], []
    for p in range(250):
        pid = f"P{p}"
        parcels.append({"id": pid, "area_decimal": 100, "dag_no": str(p)})
        ents.append(
            {"id": f"E{p}", "parcel_id": pid, "owner": "OWNER-A", "opening_area": 100, "effective_date": "2020-01-01"}
        )
        for i in range(4):
            tid = f"T{p}-{i}"
            d = date(2024, 1 + i * 2, 1).isoformat()
            deeds.append(
                {
                    "id": f"D{p}-{i}",
                    "parcel_id": pid,
                    "seller": "OWNER-A",
                    "buyer": f"BUYER-{i}",
                    "area_decimal": 5,
                    "registration_date": d,
                }
            )
            transfers.append(
                {
                    "id": tid,
                    "deed_id": f"D{p}-{i}",
                    "parcel_id": pid,
                    "portion_key": f"K{p}-{i}",
                    "seller": "OWNER-A",
                    "buyer": f"BUYER-{i}",
                    "area": 5,
                    "event_date": d,
                }
            )
            muts.append(
                {
                    "id": f"M{p}-{i}",
                    "transfer_id": tid,
                    "parcel_id": pid,
                    "date": d,
                    "area": 5,
                    "recipient": f"BUYER-{i}",
                }
            )
    ds = Dataset.from_dict(
        {"parcels": parcels, "entitlements": ents, "deeds": deeds, "transfers": transfers, "mutations": muts}
    )
    start = time.perf_counter()
    findings = run_audit(ds)
    elapsed = time.perf_counter() - start
    assert findings == []
    assert elapsed < 2.0, f"audit took {elapsed:.2f}s"
