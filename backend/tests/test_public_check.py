"""Public "Check Land" page: the four outcomes, live link to officer registrations, and no data leaks."""

from datetime import date

import pytest

from app.registry import public

MOUZA1 = "নমুনা মৌজা-১"
MOUZA2 = "নমুনা মৌজা-২"
RAHIM = "রহিম উদ্দিন"
KARIM = "করিম মিয়া"


@pytest.fixture()
def auth(client, settings):
    creds = {"username": settings.officer_username, "password": settings.officer_password}
    token = client.post("/api/auth/login", json=creds).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def check(client, dag, name, mouza=MOUZA1):
    r = client.post("/api/public/check", json={"mouza": mouza, "dag_no": dag, "owner_name": name})
    assert r.status_code == 200, r.text
    return r.json()


def sell(client, auth, seller, buyer):
    body = {
        "mouza": MOUZA1,
        "dag_no": "123",
        "seller": seller,
        "buyer": buyer,
        "area": "10",
        "deed_date": date.today().isoformat(),
    }
    assert client.post("/api/registry/registrations", json=body, headers=auth).json()["verdict"] == "success"


def test_registered_owner_with_finished_mutation_is_green(client):
    r = check(client, "১২৩", RAHIM)  # Bangla digits work too
    assert (r["result"], r["level"], r["mutation_done"]) == ("ok", "green", True)
    assert r["message_bn"] == "এই নামেই আছে, বিক্রির যোগ্য"


def test_officer_sale_shows_up_at_once_and_old_owner_is_red(client, auth):
    sell(client, auth, RAHIM, KARIM)
    old = check(client, "123", RAHIM)
    assert old["level"] == "red" and old["result"] == "not_owner"
    assert old["registered_owners"] == [KARIM]
    assert old["message_bn"] == f"এই নামে নেই। বর্তমান মালিক: {KARIM}"
    assert old["sold_on"] == date.today().isoformat()
    assert old["previous_owners"] == [{"name": RAHIM, "date": date.today().isoformat()}]


def test_new_owner_is_amber_until_mutation_is_completed(client, auth):
    sell(client, auth, RAHIM, KARIM)
    r = check(client, "123", KARIM)
    assert (r["result"], r["level"], r["mutation_done"]) == ("mutation_pending", "amber", False)
    done = client.post("/api/registry/mutations/complete", params={"mouza": MOUZA1, "dag_no": "123"}, headers=auth)
    assert done.status_code == 200
    assert check(client, "123", KARIM)["level"] == "green"


def test_demo_plot_with_pending_mutation_is_amber(client):
    r = check(client, "202", "নাজমা খাতুন", mouza=MOUZA2)
    assert r["level"] == "amber" and r["result"] == "mutation_pending"
    seller = check(client, "202", "আব্দুস সালাম", mouza=MOUZA2)
    assert seller["level"] == "red" and seller["sold_on"] is not None


def test_unknown_plot_is_amber_not_found(client):
    r = check(client, "999", RAHIM)
    assert (r["result"], r["level"]) == ("not_found", "amber")
    assert r["message_bn"] == "এই দাগ রেকর্ডে পাওয়া যায়নি"


def test_stranger_is_red_without_sale_date(client):
    r = check(client, "124", "অজানা ব্যক্তি")
    assert r["level"] == "red" and r["sold_on"] is None


def test_public_response_leaks_nothing_internal(client, auth):
    sell(client, auth, RAHIM, KARIM)
    client.post(  # a blocked attempt that must stay invisible to the public
        "/api/registry/registrations",
        json={
            "mouza": MOUZA1,
            "dag_no": "123",
            "seller": RAHIM,
            "buyer": "আনোয়ার হোসেন",
            "area": "10",
            "deed_date": date.today().isoformat(),
        },
        headers=auth,
    )
    r = check(client, "123", RAHIM)
    allowed = {
        "synthetic_notice",
        "result",
        "level",
        "message_bn",
        "message_en",
        "registered_owners",
        "mutation_done",
        "sold_on",
        "previous_owners",
    }
    assert set(r) == allowed
    text = str(r)
    for secret in ("আনোয়ার", "subregistrar", "R1", "alert", "risk", "blocked"):
        assert secret not in text


def test_public_check_is_audited_without_personal_data(client):
    check(client, "123", RAHIM)
    entries = client.get("/api/audit-log").json()["entries"]
    assert entries[0]["event_type"] == "public_check"
    assert entries[0]["subject_id"] == f"{MOUZA1}/123"
    assert client.get("/api/audit-log/verify").json()["ok"] is True


def test_validation_and_mouza_list(client):
    assert (
        client.post("/api/public/check", json={"mouza": MOUZA1, "dag_no": "123", "owner_name": "ক"}).status_code == 422
    )
    assert MOUZA1 in client.get("/api/public/mouzas").json()["mouzas"]


def test_pure_decision_handles_partial_owner():
    owners = [(RAHIM, "রহিম উদ্দিন"), (KARIM, "করিম মিয়া")]
    r = public.decide(found=True, owners=owners, mutation_complete=True, sales=[], name=" করিম  মিয়া ")
    assert r.level == "green"
