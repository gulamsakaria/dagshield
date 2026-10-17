"""Runtime settings, read from environment variables (never from source code).

Secrets (the demo signing key, the database password, the admin token) only ever
come from the environment. See .env.example and scripts/gen_demo_key.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv_file(path: Path | None = None) -> None:
    """Tiny .env reader (no extra dependency). Real environment variables always win."""
    path = path or (REPO_ROOT / ".env")
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


# Demo-only login for the synthetic officer portal. Override both with environment variables.
DEMO_OFFICER_USER = "subregistrar"
DEMO_OFFICER_PASSWORD = "demo-officer-2026"  # noqa: S105


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _num(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return default if raw in (None, "") else float(raw)


@dataclass(frozen=True)
class Settings:
    database_url: str
    signing_key_b64: str | None
    allowed_origins: tuple[str, ...]
    public_base_url: str
    admin_token: str | None
    fixtures_dir: Path
    area_tolerance: float
    lineage_confidence_min: float
    rapid_window_days: int
    rapid_min_events: int
    enable_r5: bool
    rate_limit_per_min: int
    enable_docs: bool
    static_dir: Path | None
    judge_login: bool
    officer_username: str
    officer_password: str


def load_settings() -> Settings:
    origins = os.environ.get("DAGSHIELD_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080")
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./dagshield.db"),
        signing_key_b64=os.environ.get("DAGSHIELD_SIGNING_KEY") or None,
        allowed_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        public_base_url=os.environ.get("DAGSHIELD_PUBLIC_BASE_URL", "http://localhost:5173").rstrip("/"),
        admin_token=os.environ.get("DAGSHIELD_ADMIN_TOKEN") or None,
        fixtures_dir=Path(os.environ.get("DAGSHIELD_FIXTURES_DIR", str(REPO_ROOT / "fixtures" / "scenarios"))),
        area_tolerance=_num("DAGSHIELD_AREA_TOLERANCE", 0.0),
        lineage_confidence_min=_num("DAGSHIELD_LINEAGE_CONFIDENCE_MIN", 0.8),
        rapid_window_days=int(_num("DAGSHIELD_R5_WINDOW_DAYS", 30)),
        rapid_min_events=int(_num("DAGSHIELD_R5_MIN_EVENTS", 3)),
        enable_r5=_bool("DAGSHIELD_ENABLE_R5", True),
        rate_limit_per_min=int(_num("DAGSHIELD_RATE_LIMIT_PER_MIN", 120)),
        enable_docs=_bool("DAGSHIELD_ENABLE_DOCS", True),
        static_dir=Path(os.environ["DAGSHIELD_STATIC_DIR"]) if os.environ.get("DAGSHIELD_STATIC_DIR") else None,
        judge_login=_bool("DAGSHIELD_JUDGE_LOGIN", False),
        officer_username=os.environ.get("DAGSHIELD_OFFICER_USER") or DEMO_OFFICER_USER,
        officer_password=os.environ.get("DAGSHIELD_OFFICER_PASSWORD") or DEMO_OFFICER_PASSWORD,
    )
