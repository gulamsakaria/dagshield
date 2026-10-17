"""Serve the built web UI (frontend/dist) from the same app, so one domain and one process host everything.

Used on hosts where only a Python app can run (e.g. cPanel). Enabled by setting DAGSHIELD_STATIC_DIR.
Anything under /api is never answered here, and files are only read from inside that folder.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

ONE_YEAR = {"Cache-Control": "public, max-age=31536000, immutable"}  # Vite file names carry a content hash


def mount_frontend(app: FastAPI, root: Path) -> None:
    root = root.resolve()
    index = root / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    def page(path: str):
        if path == "api" or path.startswith(("api/", "docs", "openapi.json")):
            raise HTTPException(404, "Not found")
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate, headers=ONE_YEAR if path.startswith("assets/") else None)
        # Not a real file: hand the address to the React router (/officer, /check, ...).
        return FileResponse(index)
