"""One-click judge demo: access switch, sample data, and that it does not disturb the basic demo plots."""

from dataclasses import replace
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app


@pytest.fixture()
def judge_client(settings):
    with TestClient(create_app(replace(settings, judge_login=True))) as c:
        yield c


def bearer(client):
    token = client.post("/api/auth/judge").json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_judge_access_is_off_by_default(client):
    assert client.get("/api/public/config").json() == {"judge_login": False}
    assert client.post("/api/auth/judge").status_code == 404


def test_judge_token_works_and_is_named(judge_client):
    assert judge_client.get("/api/public/config").json() == {"judge_login": True}
    h = bearer(judge_client)
    me = judge_client.get("/api/auth/me", headers=h).json()
    assert me["username"] == "judge" and "Judge" in me["name_en"]
    assert judge_client.get("/api/registry/summary", headers=h).status_code == 200
    assert judge_client.get("/api/registry/summary").status_code == 401


def test_sample_data_gives_real_rule_outcomes_and_is_idempotent(judge_client):
    h = bearer(judge_client)
    first = judge_client.post("/api/registry/sample-data", headers=h).json()
    assert first["loaded"] is True
    assert judge_client.post("/api/registry/sample-data", headers=h).json()["loaded"] is False
    s = judge_client.get("/api/registry/summary", headers=h).json()
    assert (s["total"], s["success"], s["warning"], s["blocked"]) == (7, 3, 1, 3)
    assert s["parcels"] == 9  # four base plots plus five sample plots
    rules = {a["rule_id"] for a in judge_client.get("/api/registry/attempts", headers=h).json()["attempts"]}
    assert {"R1", "R2", "R5", "OK"} <= rules


def test_sample_names_work_in_english_on_the_public_page(judge_client):
    h = bearer(judge_client)
    judge_client.post("/api/registry/sample-data", headers=h)

    def check(mouza, dag, name):
        body = {"mouza": mouza, "dag_no": dag, "owner_name": name}
        return judge_client.post("/api/public/check", json=body).json()["level"]

    assert check("Sample Mouza 4", "401", "mizanur rahman") == "green"  # mutation finished
    assert check("Sample Mouza 4", "402", "Rubel Hasan") == "amber"  # mutation pending
    assert check("Sample Mouza 4", "401", "Karim Hossain") == "red"  # sold earlier
    assert check("Sample Mouza 4", "403", "Sultana Razia") == "green"  # untouched sample plot


def test_basic_demo_plots_still_start_clean_after_sample_data(judge_client):
    h = bearer(judge_client)
    judge_client.post("/api/registry/sample-data", headers=h)
    body = {
        "mouza": "নমুনা মৌজা-১",
        "dag_no": "123",
        "seller": "রহিম উদ্দিন",
        "buyer": "করিম মিয়া",
        "area": "10",
        "deed_date": date.today().isoformat(),
    }
    assert judge_client.post("/api/registry/registrations", json=body, headers=h).json()["verdict"] == "success"
    judge_client.post("/api/registry/reset", headers=h)
    assert judge_client.get("/api/registry/summary", headers=h).json()["total"] == 0
