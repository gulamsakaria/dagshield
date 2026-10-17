#!/usr/bin/env python3
"""Fail if the repository contains something that looks like a secret.

Run before every commit (see scripts/pre-commit) and in CI.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "__pycache__", ".pytest_cache", ".ruff_cache"}
SKIP_FILES = {".env.example", "check_secrets.py", "gen_demo_key.py"}
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".md", ".yml", ".yaml", ".toml", ".txt",
                 ".env", ".sh", ".html", ".css", ".conf", ".cfg", ".ini", ".sql", ""}

PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
    "signing key assigned a value": re.compile(r"DAGSHIELD_SIGNING_KEY\s*[=:]\s*['\"]?[A-Za-z0-9+/=_-]{32,}"),
    "hard-coded database password": re.compile(r"POSTGRES_PASSWORD\s*[=:]\s*['\"]?(?!\$)[^\s'\"$]{6,}"),
    "admin token assigned a value": re.compile(r"DAGSHIELD_ADMIN_TOKEN\s*[=:]\s*['\"]?[^\s'\"$]{6,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
}


def tracked_env_files() -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return [f for f in out.splitlines() if Path(f).name.startswith(".env") and Path(f).name != ".env.example"]


def main() -> int:
    problems = [f"{f}: .env file is tracked by Git" for f in tracked_env_files()]
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        if path.name in SKIP_FILES or path.name == ".env" or path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, rx in PATTERNS.items():
            if rx.search(text):
                problems.append(f"{path.relative_to(ROOT)}: {label}")
    if problems:
        print("Possible secrets found:")
        print("\n".join(f"  - {p}" for p in problems))
        return 1
    print("check_secrets: no secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
