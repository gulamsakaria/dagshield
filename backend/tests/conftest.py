import base64
import glob
import json
import os
from pathlib import Path

import pytest

# A throwaway key that exists only inside the test process. Never reuse it anywhere.
TEST_KEY = base64.b64encode(b"dagshield-test-key-0123456789ab!").decode()
FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "scenarios"


def load_fixtures():
    return [json.loads(Path(f).read_text(encoding="utf-8")) for f in sorted(glob.glob(str(FIXTURE_DIR / "*.json")))]


@pytest.fixture(scope="session")
def fixtures():
    return load_fixtures()


@pytest.fixture()
def settings(tmp_path):
    from app.config import load_settings

    os.environ["DAGSHIELD_SIGNING_KEY"] = TEST_KEY
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    os.environ["DAGSHIELD_RATE_LIMIT_PER_MIN"] = "0"
    os.environ.pop("DAGSHIELD_ADMIN_TOKEN", None)
    return load_settings()


@pytest.fixture()
def client(settings):
    from fastapi.testclient import TestClient

    from app.api.main import create_app

    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture()
def signer():
    from app.integrity.signing import Signer

    return Signer(TEST_KEY)
