"""Officer-portal demo: login, the four demo scenarios, history and counters."""

from datetime import date, timedelta

import pytest

MOUZA1 = "নমুনা মৌজা-১"
MOUZA2 = "নমুনা মৌজা-২"
RAHIM = "রহিম উদ্দিন"
KARIM = "করিম মিয়া"
SALMA = "সালমা বেগম"


@pytest.fixture()
def auth(client, settings):
    creds = {"username": settings.officer_username, "password": settings.officer_password}
    r = client.post("/api/auth/login", json=creds)
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def register(client, auth, seller, buyer, dag="১২৩", area="10", when=None, mouza=MOUZA1):
    body = {
        "mouza": mouza,
        "dag_no": dag,
        "seller": seller,
        "buyer": buyer,
        "area": area,
        "deed_date": (when or date.today()).isoformat(),
    }
    r = client.post("/api/registry/registrations", json=body, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def history(client, auth, mouza, dag):
    return client.get("/api/registry/history", params={"mouza": mouza, "dag_no": dag}, headers=auth).json()


def test_login_required_and_wrong_password(client):
    assert client.get("/api/registry/summary").status_code == 401
    assert client.post("/api/auth/login", json={"username": "subregistrar", "password": "wrong"}).status_code == 401


def test_success_then_double_sale_blocked(client, auth):
    ok = register(client, auth, RAHIM, KARIM)
    assert ok["verdict"] == "success"
    dup = register(client, auth, RAHIM, "আনোয়ার হোসেন")
    assert dup["verdict"] == "blocked" and dup["rule_id"] == "R1"
    assert KARIM in dup["reason_bn"]
    h = history(client, auth, MOUZA1, "123")
    assert [o["owner"] for o in h["owners"]] == [KARIM]
    assert [e["kind"] for e in h["timeline"]] == ["initial", "transfer", "blocked"]


def test_fake_seller_blocked(client, auth):
    r = register(client, auth, "অজানা ব্যক্তি", KARIM, dag="124", area="5")
    assert r["verdict"] == "blocked" and r["rule_id"] == "R2"
    assert r["reason_bn"] == "বিক্রেতা রেকর্ডের মালিক নন।"
    assert [o["owner"] for o in history(client, auth, MOUZA1, "124")["owners"]] == [SALMA]


def test_area_over_record_blocked(client, auth):
    r = register(client, auth, SALMA, KARIM, dag="124", area="16")
    assert r["verdict"] == "blocked" and r["rule_id"] == "R2"


def test_quick_resale_is_warning_and_still_registers(client, auth):
    assert register(client, auth, RAHIM, KARIM)["verdict"] == "success"
    w = register(client, auth, KARIM, "নাসির আহমেদ")
    assert w["verdict"] == "warning" and w["rule_id"] == "R5"
    s = client.get("/api/registry/summary", headers=auth).json()
    assert (s["total"], s["success"], s["warning"], s["blocked"]) == (2, 1, 1, 0)


def test_partial_sale_splits_holding(client, auth):
    r = register(client, auth, "জামাল হোসেন", "ফারুক আলী", dag="201", area="5", mouza=MOUZA2)
    assert r["verdict"] == "success"
    owners = {o["owner"]: o["area"] for o in history(client, auth, MOUZA2, "201")["owners"]}
    assert owners == {"জামাল হোসেন": 15.0, "ফারুক আলী": 5.0}


def test_unknown_plot_and_validation(client, auth):
    assert register(client, auth, RAHIM, KARIM, dag="999")["rule_id"] == "R0"
    bad = {"mouza": MOUZA1, "dag_no": "123", "seller": "ক খ", "buyer": "ক খ", "area": "1", "deed_date": "2020-01-01"}
    assert client.post("/api/registry/registrations", json=bad, headers=auth).status_code == 422
    bad.update(buyer="গ ঘ", deed_date=(date.today() + timedelta(days=3)).isoformat())
    assert client.post("/api/registry/registrations", json=bad, headers=auth).status_code == 422
    bad.update(deed_date="2020-01-01", area="-4")
    assert client.post("/api/registry/registrations", json=bad, headers=auth).status_code == 422


def test_alert_filter_and_reset(client, auth):
    register(client, auth, RAHIM, KARIM)
    register(client, auth, RAHIM, "আনোয়ার হোসেন")
    params = [("verdict", "blocked"), ("verdict", "warning")]
    assert len(client.get("/api/registry/attempts", params=params, headers=auth).json()["attempts"]) == 1
    assert client.post("/api/registry/reset", headers=auth).status_code == 200
    assert client.get("/api/registry/summary", headers=auth).json()["total"] == 0
    assert client.get("/api/audit-log/verify").json()["ok"] is True


def test_officer_can_add_a_plot_in_english_and_it_works_everywhere(client, auth):
    body = {
        "mouza": "Sample Mouza 3",
        "dag_no": "301",
        "owner": "Abdul Karim",
        "area": "7.5",
    }
    r = client.post("/api/registry/plots", json=body, headers=auth)
    assert r.status_code == 201, r.text
    # the same plot again (different case and spacing) is refused
    again = client.post(
        "/api/registry/plots", json={**body, "mouza": "  sample  MOUZA 3", "owner": "Someone Else"}, headers=auth
    )
    assert again.status_code == 409
    # public page: dropdown list and a name check, case and spacing ignored
    assert "Sample Mouza 3" in client.get("/api/public/mouzas").json()["mouzas"]
    check = {"mouza": "Sample Mouza 3", "dag_no": "301", "owner_name": "abdul   karim"}
    assert client.post("/api/public/check", json=check).json()["level"] == "green"
    # officer registers a sale with English names; the old owner is then red on the public page
    sale = {
        "mouza": "Sample Mouza 3",
        "dag_no": "301",
        "seller": "Abdul Karim",
        "buyer": "Rahim Uddin",
        "area": "7.5",
        "deed_date": date.today().isoformat(),
    }
    assert client.post("/api/registry/registrations", json=sale, headers=auth).json()["verdict"] == "success"
    assert client.post("/api/public/check", json=check).json()["level"] == "red"


def test_add_plot_needs_login_and_valid_input(client, auth):
    body = {"mouza": "M", "dag_no": "5", "owner": "Ab Cd", "area": "1"}
    assert client.post("/api/registry/plots", json=body).status_code == 401
    assert client.post("/api/registry/plots", json={**body, "area": "0"}, headers=auth).status_code == 422
    assert client.post("/api/registry/plots", json={**body, "dag_no": "a b"}, headers=auth).status_code == 422
