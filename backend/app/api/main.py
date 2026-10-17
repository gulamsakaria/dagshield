"""FastAPI application factory."""

from __future__ import annotations

import hashlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import Settings, load_dotenv_file, load_settings
from ..db import repo
from ..db.models import Base
from ..db.session import make_engine, make_session_factory
from ..integrity.signing import Signer
from ..registry import service as registry_service
from ..registry.auth import OfficerAuth
from .public_routes import router as public_router
from .registry_routes import router as registry_router
from .routes import router
from .security import RateLimiter, SecurityHeadersMiddleware
from .static_site import mount_frontend

log = logging.getLogger("dagshield")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    if not settings.signing_key_b64:
        raise RuntimeError(
            "DAGSHIELD_SIGNING_KEY is not set. Run `python scripts/gen_demo_key.py` to create a .env "
            "with a demo key (the key must never be committed to Git)."
        )
    signer = Signer(settings.signing_key_b64)
    engine = make_engine(settings.database_url)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    fixtures = repo.load_fixture_files(settings.fixtures_dir)

    def startup() -> None:
        """Create demo data if missing. Normally run by the lifespan hook; WSGI hosts call it by hand."""
        with factory() as db:
            log.info("database: %s", repo.ensure_seeded(db, fixtures, signer))
            log.info("registry demo data seeded: %s", registry_service.seed_if_empty(db))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        startup()
        yield

    app = FastAPI(
        title="DagShield API",
        version="1.0.0",
        description="Synthetic-data prototype. A screening aid for human review, not a legal opinion.",
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.startup = startup
    app.state.signer = signer
    app.state.session_factory = factory
    app.state.fixtures = fixtures
    app.state.limiter = RateLimiter(settings.rate_limit_per_min)
    app.state.public_limiter = RateLimiter(30)  # public checks per minute per client
    app.state.login_limiter = RateLimiter(10)  # login attempts per minute per client
    session_secret = hashlib.sha256(b"officer-session|" + settings.signing_key_b64.encode()).digest()
    app.state.officer_auth = OfficerAuth(settings.officer_username, settings.officer_password, session_secret)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-Admin-Token", "Authorization"],
        allow_credentials=False,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(router)
    app.include_router(registry_router)
    app.include_router(public_router)

    if settings.static_dir and (settings.static_dir / "index.html").is_file():
        mount_frontend(app, settings.static_dir)  # last, so every /api route wins

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):  # never leak stack traces to the client
        log.exception("unhandled error", exc_info=exc)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)

    return app


def app_factory() -> FastAPI:
    """Entry point for uvicorn: `uvicorn app.api.main:app_factory --factory`."""
    load_dotenv_file()
    return create_app()
