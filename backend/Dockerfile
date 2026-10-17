# Build context is the repository root:  docker compose build api
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Run as an unprivileged user
RUN useradd --system --uid 10001 --no-create-home app

WORKDIR /srv
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend backend
COPY fixtures fixtures
ENV DAGSHIELD_FIXTURES_DIR=/srv/fixtures/scenarios

USER app
WORKDIR /srv/backend
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=4s --retries=5 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

CMD ["uvicorn", "app.api.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
