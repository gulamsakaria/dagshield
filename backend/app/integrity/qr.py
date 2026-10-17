"""QR payload for a signed deed copy (deed reference + hash + signature)."""

from __future__ import annotations

import base64
import io
from urllib.parse import urlencode

import qrcode


def verify_url(base_url: str, deed_ref: str, record_hash: str, signature: str) -> str:
    return f"{base_url}/verify?" + urlencode({"ref": deed_ref, "h": record_hash, "s": signature})


def qr_png_base64(text: str) -> str:
    img = qrcode.make(text, box_size=6, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
