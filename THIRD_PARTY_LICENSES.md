# Third-party software and licences

Listed from the pinned dependencies. **Check each entry against the package's own page before you submit**, because
this table was written from general knowledge, not generated from the installed packages.

| Package | Used for | Licence |
| --- | --- | --- |
| FastAPI | API framework | MIT |
| Starlette (via FastAPI) | ASGI toolkit | BSD-3-Clause |
| Pydantic | input validation | MIT |
| Uvicorn | ASGI server | BSD-3-Clause |
| SQLAlchemy | database layer | MIT |
| psycopg 3 | PostgreSQL driver | LGPL-3.0 (used as an unmodified library) |
| cryptography | Ed25519 signing | Apache-2.0 or BSD-3-Clause |
| qrcode and Pillow | QR image | BSD / HPND |
| pytest, httpx, ruff, pip-audit | development and checks | MIT / BSD-3-Clause / MIT / Apache-2.0 |
| React, React DOM, React Router | web UI | MIT |
| Vite, @vitejs/plugin-react, TypeScript, Prettier | build and checks | MIT / MIT / Apache-2.0 / MIT |
| IBM Plex Sans (@fontsource) | Latin font | SIL Open Font Licence 1.1 |
| Noto Sans Bengali (@fontsource) | Bangla font | SIL Open Font Licence 1.1 |
| a2wsgi (hosting package only) | runs the API under a WSGI host such as cPanel | Apache-2.0 |
| PostgreSQL, nginx (Docker images) | database, web server | PostgreSQL Licence, BSD-2-Clause |

To regenerate an exact list later: `pip-licenses` for Python and `npx license-checker --summary` for Node.

## Map outlines

- Bangladesh division outlines on the home page come from geoBoundaries (ADM1, CC0 1.0), simplified and projected in `frontend/src/bdMap.ts`. Source: https://www.geoboundaries.org/
