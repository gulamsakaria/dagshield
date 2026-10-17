#!/usr/bin/env python3
"""Create .env with a fresh Ed25519 demo signing key and a random database password.

The file is created with owner-only permissions and is ignored by Git.
Usage:  python scripts/gen_demo_key.py [--force]
"""
import base64
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / ".env.example"
TARGET = ROOT / ".env"


def main() -> int:
    if TARGET.exists() and "--force" not in sys.argv:
        print(".env already exists. Refusing to overwrite (re-run with --force to replace it).")
        print("Note: a new key means old deed signatures are re-signed automatically on next start.")
        return 1
    seed = base64.b64encode(os.urandom(32)).decode()
    text = EXAMPLE.read_text(encoding="utf-8")
    out = []
    for line in text.splitlines():
        if line.startswith("DAGSHIELD_SIGNING_KEY="):
            line = f"DAGSHIELD_SIGNING_KEY={seed}"
        elif line.startswith("POSTGRES_PASSWORD="):
            line = f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}"
        out.append(line)
    fd = os.open(TARGET, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Created {TARGET} (permissions 600). Keep it private; it is listed in .gitignore.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
