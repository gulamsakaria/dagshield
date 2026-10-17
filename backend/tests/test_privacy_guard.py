from app.privacy import scan_fixture

from .conftest import load_fixtures


def test_all_shipped_fixtures_are_clean():
    for fx in load_fixtures():
        assert scan_fixture(fx) == [], fx["scenario_id"]


def test_guard_rejects_real_looking_identity():
    assert scan_fixture({"owner": "Md Karim Uddin"})


def test_guard_rejects_nid_phone_and_email():
    assert scan_fixture({"notes": "NID 1990123456789"})
    assert scan_fixture({"notes": "call 01712345678"})
    assert scan_fixture({"notes": "someone@example.com"})


def test_guard_allows_synthetic_tokens_and_dates():
    assert scan_fixture({"owner": "OWNER-A", "buyer": "BUYER-B", "date": "2024-03-10"}) == []
