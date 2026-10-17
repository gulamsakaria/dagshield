import os
import time

from sqlalchemy import text

from app.db.session import make_engine


def deed_fields(client, ref):
    return client.get(f"/api/deeds/{ref}").json()["fields"]


def test_scenarios_listed_and_synthetic_banner_text(client):
    body = client.get("/api/scenarios").json()
    assert len(body["scenarios"]) == 10
    assert "Synthetic data only" in body["synthetic_notice"]


def test_search_exact_match_and_empty_state(client):
    hit = client.get("/api/parcels", params={"query": "P-S02-A"}).json()
    assert hit["count"] == 1 and hit["results"][0]["id"] == "P-S02-A"
    by_dag = client.get("/api/parcels", params={"query": "102"}).json()
    assert by_dag["count"] == 1
    assert client.get("/api/parcels", params={"query": "NOPE-999"}).json()["count"] == 0
    assert client.get("/api/parcels", params={"query": "P-S02"}).json()["count"] == 0  # no fuzzy match


def test_search_rejects_bad_input(client):
    assert client.get("/api/parcels", params={"query": "'; DROP TABLE parcels;--"}).status_code == 422
    assert client.get("/api/parcels", params={"query": "x" * 100}).status_code == 422
    assert client.get("/api/parcels", params={"query": ""}).status_code == 422


def test_history_has_lineage_timeline_and_balance(client):
    h = client.get("/api/parcels/P-S01-A/history").json()
    kinds = [e["kind"] for e in h["timeline"]]
    assert kinds == ["deed", "transfer", "mutation"]
    owner_a = next(o for o in h["ownership_summary"] if o["owner"] == "OWNER-A")
    assert owner_a["balance"] == 7
    lin = client.get("/api/parcels/P-S06-A/history").json()["lineage"]
    assert lin[0]["uncertain"] is True and lin[0]["confidence"] == 0.4
    assert client.get("/api/parcels/NOPE/history").status_code == 404


def test_audit_creates_alerts_and_status_persists_across_reruns(client):
    r = client.post("/api/audits", json={}).json()
    assert r["alert_count"] == 10
    alert = next(a for a in r["alerts"] if a["rule_id"] == "R2")
    assert alert["calc"]["excess"] == 2 and alert["status"] == "New"
    patched = client.patch(f"/api/alerts/{alert['id']}", json={"status": "Under Review"}).json()
    assert patched["status"] == "Under Review"
    client.post("/api/audits", json={})  # re-run
    assert client.get(f"/api/alerts/{alert['id']}").json()["status"] == "Under Review"
    assert client.patch(f"/api/alerts/{alert['id']}", json={"status": "Nonsense"}).status_code == 422


def test_clean_scenario_raises_no_alert(client):
    r = client.post("/api/audits", json={"scenario_id": "clean-transfer"}).json()
    assert r["alert_count"] == 0


def test_audit_by_parcel_and_unknown_inputs(client):
    r = client.post("/api/audits", json={"parcel_id": "P-S10-A"}).json()
    assert sorted(a["rule_id"] for a in r["alerts"]) == ["R1", "R3"]
    assert client.post("/api/audits", json={"parcel_id": "NOPE"}).status_code == 404
    assert client.post("/api/audits", json={"scenario_id": "nope"}).status_code == 404
    assert client.post("/api/audits", json={"unexpected": 1}).status_code == 422


def test_alert_filters(client):
    client.post("/api/audits", json={})
    only_r4 = client.get("/api/alerts", params={"rule_id": "R4"}).json()["alerts"]
    assert only_r4 and all(a["rule_id"] == "R4" for a in only_r4)


def test_genuine_deed_verifies_and_one_edit_fails(client):
    qr = client.get("/api/deeds/DEED-S01-1/qr").json()
    assert qr["png_base64"] and qr["verify_url"].startswith("http")
    fields = deed_fields(client, "DEED-S01-1")
    good = client.post(
        "/api/verify",
        json={"deed_ref": "DEED-S01-1", "fields": fields, "hash": qr["hash"], "signature": qr["signature"]},
    ).json()
    assert good["result"] == "match"
    fields["area_decimal"] = "6.0000"
    bad = client.post(
        "/api/verify",
        json={"deed_ref": "DEED-S01-1", "fields": fields, "hash": qr["hash"], "signature": qr["signature"]},
    ).json()
    assert bad["result"] == "mismatch" and "area_decimal" in bad["mismatched_fields"]
    assert bad["recomputed_hash"] != bad["signed_hash"]


def test_verify_unknown_deed_and_extra_fields(client):
    fields = deed_fields(client, "DEED-S01-1")
    r = client.post("/api/verify", json={"deed_ref": "DEED-NOPE", "fields": fields}).json()
    assert r["result"] == "not_found"
    fields["injected"] = "x"
    assert client.post("/api/verify", json={"deed_ref": "DEED-S01-1", "fields": fields}).status_code == 422


def test_audit_log_chain_is_ok_then_breaks_when_a_row_is_edited(client, settings):
    client.post("/api/audits", json={})
    assert client.get("/api/audit-log/verify").json()["ok"] is True
    engine = make_engine(settings.database_url)
    with engine.begin() as conn:
        conn.execute(text("UPDATE audit_log SET payload_hash = :h WHERE seq = 3"), {"h": "0" * 64})
    broken = client.get("/api/audit-log/verify").json()
    assert broken["ok"] is False and broken["broken_at"] == 2


def test_audit_log_breaks_when_a_row_is_deleted(client, settings):
    engine = make_engine(settings.database_url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE seq = 4"))
    assert client.get("/api/audit-log/verify").json()["ok"] is False


def test_reset_restores_a_scenario_and_keeps_the_log_append_only(client):
    before = client.get("/api/audit-log").json()["total"]
    assert client.post("/api/scenarios/excess-transfer/reset").json()["reset"] is True
    assert client.get("/api/audit-log").json()["total"] > before
    assert client.get("/api/audit-log/verify").json()["ok"] is True
    assert client.post("/api/scenarios/nope/reset").status_code == 404


def test_evaluation_reports_actual_counts(client):
    ev = client.get("/api/evaluation").json()
    t = ev["totals"]
    assert (t["tp"], t["fp"], t["fn"]) == (10, 0, 0)
    assert t["passed"] == t["cases"] and ev["repeatability_ok"] is True
    assert "synthetic" in ev["note"].lower()
    assert {"R1", "R2", "R3", "R4", "R5"} <= set(ev["per_rule"])


def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_cors_only_allows_configured_origins(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_oversized_body_is_refused(client):
    r = client.post("/api/audits", content=b"x" * 70_000, headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_errors_do_not_leak_internals(client):
    r = client.get("/api/parcels/%00/history")
    assert r.status_code in (404, 422) and "Traceback" not in r.text


def test_admin_token_protects_mutations_when_configured(settings):
    from fastapi.testclient import TestClient

    from app.api.main import create_app
    from app.config import load_settings

    os.environ["DAGSHIELD_ADMIN_TOKEN"] = "s3cret-demo-token"
    try:
        with TestClient(create_app(load_settings())) as c:
            assert c.post("/api/scenarios/excess-transfer/reset").status_code == 401
            ok = c.post("/api/scenarios/excess-transfer/reset", headers={"X-Admin-Token": "s3cret-demo-token"})
            assert ok.status_code == 200
            assert c.get("/api/scenarios").status_code == 200  # reads stay open
    finally:
        os.environ.pop("DAGSHIELD_ADMIN_TOKEN", None)


def test_rate_limit_returns_429(settings):
    from fastapi.testclient import TestClient

    from app.api.main import create_app
    from app.config import load_settings

    os.environ["DAGSHIELD_RATE_LIMIT_PER_MIN"] = "3"
    try:
        with TestClient(create_app(load_settings())) as c:
            fields = c.get("/api/deeds/DEED-S01-1").json()["fields"]
            codes = [
                c.post("/api/verify", json={"deed_ref": "DEED-S01-1", "fields": fields}).status_code for _ in range(5)
            ]
            assert codes[:3] == [200, 200, 200] and codes[-1] == 429
    finally:
        os.environ["DAGSHIELD_RATE_LIMIT_PER_MIN"] = "0"


def test_app_refuses_to_start_without_a_signing_key(settings):
    import dataclasses

    import pytest

    from app.api.main import create_app

    with pytest.raises(RuntimeError, match="DAGSHIELD_SIGNING_KEY"):
        create_app(dataclasses.replace(settings, signing_key_b64=None))


def test_stored_signatures_are_resigned_when_the_key_changes(settings):
    import dataclasses

    from fastapi.testclient import TestClient

    from app.api.main import create_app
    from app.integrity.signing import generate_seed_b64

    with TestClient(create_app(settings)):
        pass
    new_settings = dataclasses.replace(settings, signing_key_b64=generate_seed_b64())
    with TestClient(create_app(new_settings)) as c:
        qr = c.get("/api/deeds/DEED-S01-1/qr").json()
        fields = c.get("/api/deeds/DEED-S01-1").json()["fields"]
        r = c.post(
            "/api/verify",
            json={"deed_ref": "DEED-S01-1", "fields": fields, "hash": qr["hash"], "signature": qr["signature"]},
        ).json()
        assert r["result"] == "match"
        assert c.get("/api/audit-log/verify").json()["ok"] is True


def test_search_and_audit_stay_under_2_seconds_with_1000_parcels(client, settings):
    engine = make_engine(settings.database_url)
    rows = [{"id": f"P-BULK-{i}", "s": "bulk", "l": "bulk", "d": f"B{i}"} for i in range(1000)]
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO scenarios (id, name, name_bn, description, description_bn, case_type, position) "
                "VALUES ('bulk','bulk','','','','',99)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO parcels (id, scenario_id, label, survey_type, dag_no, area_decimal, status) "
                "VALUES (:id, :s, :l, 'RS', :d, 10, 'active')"
            ),
            rows,
        )
    t0 = time.perf_counter()
    assert client.get("/api/parcels", params={"query": "P-BULK-777"}).json()["count"] == 1
    assert time.perf_counter() - t0 < 2
    t0 = time.perf_counter()
    assert client.post("/api/audits", json={}).status_code == 200
    assert time.perf_counter() - t0 < 2
