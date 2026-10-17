#!/usr/bin/env python3
"""Build a ready-to-upload folder for cPanel "Setup Python App" hosting (one domain, one Python app).

    python scripts/build_cpanel_package.py --domain dagshield.stratifyxglobal.com

It writes, next to the repository (never inside it):
    cpanel-package/dagshield_app/        <- upload this whole folder (backend, built web UI, fixtures, .env)
    cpanel-package/PRIVATE-credentials.txt   <- the officer password and admin token. Do NOT upload this file.

Fresh secrets are generated on every run: signing key, officer password, admin token.
"""

from __future__ import annotations

import argparse
import base64
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIREMENTS = """\
# Runtime packages for the hosted app (SQLite, no PostgreSQL driver). Needs Python 3.11 or newer.
fastapi==0.115.6
pydantic==2.10.4
sqlalchemy==2.0.36
cryptography==44.0.0
qrcode[pil]==8.0
a2wsgi==1.10.7
"""

PASSENGER_WSGI = '''"""Entry file for cPanel "Setup Python App" (Passenger / LiteSpeed). Startup file: passenger_wsgi.py, entry point: application."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)  # relative paths in .env (database, web UI folder) start from here
sys.path.insert(0, os.path.join(HERE, "backend"))
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)

from a2wsgi import ASGIMiddleware  # noqa: E402  (turns the async FastAPI app into a WSGI app)

from app.api.main import app_factory  # noqa: E402

_app = app_factory()
_app.state.startup()  # a2wsgi does not run the ASGI start-up hook, so create the demo data here
_engine = _app.state.session_factory.kw["bind"]
_worker = {"pid": None, "wsgi": None}


def application(environ, start_response):
    """The host may fork worker processes after this file is loaded. a2wsgi runs a background thread and
    database connections do not survive a fork, so both are created inside the worker that serves requests."""
    if _worker["pid"] != os.getpid():
        _engine.dispose()
        _worker["wsgi"] = ASGIMiddleware(_app)
        _worker["pid"] = os.getpid()
    return _worker["wsgi"](environ, start_response)
'''


# The app folder may sit inside public_html (when the FTP account is locked to the web folder). This keeps the
# browser from downloading .env, the database or the source code by guessing their addresses.
DENY_HTACCESS = """<IfModule mod_authz_core.c>
  Require all denied
</IfModule>
<IfModule !mod_authz_core.c>
  Order deny,allow
  Deny from all
</IfModule>
"""


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    shell = os.name == "nt"  # npm is npm.cmd on Windows
    subprocess.run(cmd, cwd=cwd, check=True, shell=shell, env={**os.environ, **(env or {})})  # noqa: S603


def ignore_junk(_dir: str, names: list[str]) -> set[str]:
    return {n for n in names if n in {"__pycache__", ".pytest_cache", ".ruff_cache"} or n.endswith(".pyc")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="e.g. dagshield.stratifyxglobal.com")
    ap.add_argument("--out", default=str(ROOT.parent / "cpanel-package"))
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if ROOT in out.parents or out == ROOT:
        print("Refusing to write secrets inside the repository. Choose --out outside it.")
        return 1

    print("1/4 building the web UI (demo password hidden on the login page)")
    run(["npm", "run", "build"], ROOT / "frontend", {"VITE_SHOW_DEMO_LOGIN": "false"})

    print("2/4 copying files")
    app = out / "dagshield_app"
    if app.exists():
        shutil.rmtree(app)
    app.mkdir(parents=True)
    shutil.copytree(ROOT / "backend" / "app", app / "backend" / "app", ignore=ignore_junk)
    shutil.copytree(ROOT / "fixtures", app / "fixtures")
    shutil.copytree(ROOT / "frontend" / "dist", app / "frontend" / "dist")
    (app / "passenger_wsgi.py").write_text(PASSENGER_WSGI, encoding="utf-8")
    (app / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    (app / ".htaccess").write_text(DENY_HTACCESS, encoding="utf-8")

    print("3/4 generating fresh secrets")
    key = base64.b64encode(secrets.token_bytes(32)).decode()
    officer_password = secrets.token_urlsafe(12)
    admin_token = secrets.token_urlsafe(18)
    url = f"https://{args.domain}"
    settings = {
        "DAGSHIELD_SIGNING_KEY": key,
        "DATABASE_URL": "sqlite:///./data/dagshield.db",
        "DAGSHIELD_STATIC_DIR": "frontend/dist",
        "DAGSHIELD_PUBLIC_BASE_URL": url,
        "DAGSHIELD_ALLOWED_ORIGINS": url,
        "DAGSHIELD_OFFICER_USER": "subregistrar",
        "DAGSHIELD_OFFICER_PASSWORD": officer_password,
        "DAGSHIELD_ADMIN_TOKEN": admin_token,
        "DAGSHIELD_ENABLE_DOCS": "false",
        "DAGSHIELD_JUDGE_LOGIN": "true",  # one-click judge demo; set to false after judging
        "DAGSHIELD_RATE_LIMIT_PER_MIN": "240",
    }
    env = "".join(f"{k}={v}\n" for k, v in settings.items())
    (app / ".env").write_text(env, encoding="utf-8")
    (out / "PRIVATE-credentials.txt").write_text(
        f"DagShield hosted demo: {url}\n\n"
        f"Officer portal: {url}/officer\n  username: subregistrar\n  password: {officer_password}\n\n"
        f"Admin token (type it into the footer box of the site before pressing Reset scenario): {admin_token}\n\n"
        "Keep this file private. Do not upload it.\n",
        encoding="utf-8",
    )

    print(f"4/4 done: {app}")
    print(f"Credentials saved to: {out / 'PRIVATE-credentials.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
