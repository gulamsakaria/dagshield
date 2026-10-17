"""Single-domain hosting: the API also serves the built web UI, and officer tokens survive several workers."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app


@pytest.fixture()
def site(settings, tmp_path):
    root = tmp_path / "dist"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("<!doctype html><div id=root></div>", encoding="utf-8")
    (root / "assets" / "app-123.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("outside the folder", encoding="utf-8")
    with TestClient(create_app(replace(settings, static_dir=root))) as c:
        yield c


def test_pages_files_and_api_all_work_on_one_origin(site):
    assert "id=root" in site.get("/").text
    assert "id=root" in site.get("/officer/login").text  # React router address -> index.html
    js = site.get("/assets/app-123.js")
    assert js.status_code == 200 and "immutable" in js.headers["cache-control"]
    assert site.get("/api/health").json()["status"] == "ok"
    assert site.get("/api/nope").status_code == 404
    assert site.get("/api/nope").headers["content-type"].startswith("application/json")


def test_pages_get_a_page_policy_and_api_keeps_the_strict_one(site):
    assert "script-src 'self'" in site.get("/").headers["content-security-policy"]
    assert site.get("/api/health").headers["content-security-policy"].startswith("default-src 'none'")


def test_cannot_read_files_outside_the_folder(site):
    for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        r = site.get(path)
        assert "outside the folder" not in r.text


def test_officer_token_works_in_another_worker_process(settings):
    creds = {"username": settings.officer_username, "password": settings.officer_password}
    with TestClient(create_app(settings)) as worker_a, TestClient(create_app(settings)) as worker_b:
        token = worker_a.post("/api/auth/login", json=creds).json()["token"]
        assert worker_b.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
        forged = token[:-4] + "0000"
        assert worker_b.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
        assert worker_b.get("/api/auth/me", headers={"Authorization": "Bearer 1.abc"}).status_code == 401
