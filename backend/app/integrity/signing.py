"""Ed25519 demo signing. The key comes from an environment variable, never from Git.

This stands in for a registrar's key. A real deployment needs key custody by the
registration authority and legal recognition of the signature (outside this MVP).
"""

from __future__ import annotations

import base64
import binascii

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def generate_seed_b64() -> str:
    import os

    return base64.b64encode(os.urandom(32)).decode("ascii")


class Signer:
    def __init__(self, seed_b64: str):
        try:
            seed = base64.b64decode(seed_b64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("DAGSHIELD_SIGNING_KEY is not valid base64") from exc
        if len(seed) != 32:
            raise ValueError("DAGSHIELD_SIGNING_KEY must decode to exactly 32 bytes")
        self._private = Ed25519PrivateKey.from_private_bytes(seed)
        self._public = self._private.public_key()

    @property
    def public_key_b64url(self) -> str:
        raw = self._public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return _b64url(raw)

    def sign(self, hash_hex: str) -> str:
        return _b64url(self._private.sign(hash_hex.encode("ascii")))

    def verify(self, hash_hex: str, signature: str | None) -> bool:
        if not signature:
            return False
        try:
            self._public.verify(_b64url_decode(signature), hash_hex.encode("ascii"))
            return True
        except (InvalidSignature, binascii.Error, ValueError):
            return False
