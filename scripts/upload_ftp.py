#!/usr/bin/env python3
"""Upload the cPanel package to the host over FTPS (FTP with TLS).

    python scripts/upload_ftp.py --creds ftp.local.txt --local ../cpanel-package/dagshield_app --remote dagshield_app

The credentials file has three or four lines (it stays on your computer, never commit it):
    host=ftp.example.com
    user=cpanel-ftp-user
    password=...
    port=21            (optional)

Plain FTP (no TLS) is refused unless you pass --allow-plain, because it sends the password in clear text.
"""

from __future__ import annotations

import argparse
import ftplib
import ssl
import sys
from pathlib import Path


def read_creds(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            out[k.strip().lower()] = v.strip()
    return out


def ensure_dir(ftp: ftplib.FTP, remote: str) -> None:
    for part in [p for p in remote.split("/") if p]:
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds", required=True)
    ap.add_argument("--local", required=True)
    ap.add_argument("--remote", required=True, help="folder on the server, relative to the FTP home")
    ap.add_argument("--allow-plain", action="store_true")
    ap.add_argument(
        "--insecure-tls",
        action="store_true",
        help="encrypt, but do not check the server certificate name (shared hosts often use another name)",
    )
    args = ap.parse_args()

    creds = read_creds(Path(args.creds))
    host, user, password = creds["host"], creds["user"], creds["password"]
    port = int(creds.get("port", "21"))
    local = Path(args.local).resolve()

    try:
        ctx = ssl.create_default_context()
        if args.insecure_tls:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        ftp: ftplib.FTP = ftplib.FTP_TLS(context=ctx)
        ftp.connect(host, port, timeout=30)
        ftp.auth()
        ftp.login(user, password)
        ftp.prot_p()
        print("connected with TLS")
    except (ssl.SSLError, ftplib.error_perm, OSError) as exc:
        if not args.allow_plain:
            print(f"TLS connection failed ({exc}). Not falling back to plain FTP. Use --allow-plain to override.")
            return 1
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=30)
        ftp.login(user, password)
        print("WARNING: connected WITHOUT encryption")

    home = ftp.pwd()
    count = 0
    for path in sorted(p for p in local.rglob("*") if p.is_file()):
        rel = path.relative_to(local).as_posix()
        ftp.cwd(home)
        ensure_dir(ftp, f"{args.remote}/{Path(rel).parent.as_posix()}".rstrip("/."))
        with path.open("rb") as fh:
            ftp.storbinary(f"STOR {path.name}", fh)
        count += 1
        if count % 10 == 0:
            print(f"  {count} files...")
    ftp.quit()
    print(f"uploaded {count} files to {args.remote}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
