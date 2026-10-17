"""Demo officer login: one synthetic sub-registrar account and short-lived signed session tokens.

The password comes from DAGSHIELD_OFFICER_PASSWORD (a demo default is used if unset, so change it for
anything beyond a local demo). Passwords are compared as scrypt hashes in constant time.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException, Request

SESSION_SECONDS = 8 * 3600
OFFICER_NAME_EN = "Demo Sub-Registrar"
OFFICER_NAME_BN = "ডেমো সাব-রেজিস্ট্রার"
JUDGE_USERNAME = "judge"
JUDGE_NAME_EN = "Judge (demo access)"
JUDGE_NAME_BN = "জুরি (ডেমো অ্যাক্সেস)"


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


class OfficerAuth:
    """Login check plus signed session tokens.

    A token is "<expiry>.<who>.<signature>". `who` is "o" for the officer account or "j" for the one-click judge
    demo access. The signature is an HMAC over who and expiry, keyed from a server secret. Nothing is kept in
    memory, so it keeps working when the host runs several worker processes (typical on shared hosting).
    Logging out forgets the token on this device; the token itself simply expires.
    """

    def __init__(self, username: str, password: str, secret: bytes):
        self._username = username
        self._secret = secret
        self._salt = secrets.token_bytes(16)
        self._hash = _derive(password, self._salt)

    def _sign(self, who: str, expiry: int) -> str:
        return hmac.new(self._secret, f"{who}|{expiry}".encode(), hashlib.sha256).hexdigest()

    def _token(self, who: str) -> str:
        expiry = int(time.time()) + SESSION_SECONDS
        return f"{expiry}.{who}.{self._sign(who, expiry)}"

    def login(self, username: str, password: str) -> str | None:
        user_ok = hmac.compare_digest(username.encode(), self._username.encode())
        pass_ok = hmac.compare_digest(_derive(password, self._salt), self._hash)
        return self._token("o") if user_ok and pass_ok else None

    def judge_token(self) -> str:
        """A session for the judge demo. Only handed out when DAGSHIELD_JUDGE_LOGIN is on."""
        return self._token("j")

    def logout(self, token: str) -> None:
        """Nothing to forget on the server: tokens are stateless and expire by themselves."""

    def officer_for(self, token: str) -> str | None:
        parts = token.split(".")
        if len(parts) != 3 or not parts[0].isdigit() or parts[1] not in ("o", "j"):
            return None
        expiry, who, signature = int(parts[0]), parts[1], parts[2]
        if expiry < time.time() or not hmac.compare_digest(signature, self._sign(who, expiry)):
            return None
        return self._username if who == "o" else JUDGE_USERNAME


def bearer(request: Request) -> str:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else ""


def current_officer(request: Request) -> str:
    """FastAPI dependency: returns the officer username or answers 401."""
    who = request.app.state.officer_auth.officer_for(bearer(request))
    if who is None:
        raise HTTPException(status_code=401, detail="Officer login required.")
    return who
