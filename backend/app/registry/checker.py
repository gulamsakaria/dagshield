"""Pre-registration check for one new deed (officer-portal demo).

Pure functions, no database. The same input always gives the same verdict.

Verdicts
    success  - the seller holds the land, the area fits, nothing odd.
    warning  - registration goes ahead but is flagged for a human (rule R5, a heuristic).
    blocked  - registration is refused (R0 not in dataset, R1 already sold, R2 seller not owner / too much area).

Wording stays careful: "potential", "not found in supplied dataset", never "fraud confirmed".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
ASCII_TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MAX_AREA = Decimal("100000")


def ascii_digits(text: str) -> str:
    return text.translate(BN_DIGITS)


def clean(text: str) -> str:
    """Trim and collapse whitespace; keep the person's spelling for display."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def key(text: str) -> str:
    """Comparison key: case, spacing and Bangla/ASCII digit differences do not matter."""
    return clean(ascii_digits(text)).casefold()


def parse_area(text: str) -> Decimal:
    try:
        value = Decimal(ascii_digits(text).strip().replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError("area must be a number") from exc
    if not value.is_finite() or value <= 0 or value > MAX_AREA:
        raise ValueError("area must be more than 0 and at most 100000")
    return value.quantize(Decimal("0.0001"))


def fmt(value: Decimal | float) -> str:
    d = Decimal(str(value)).quantize(Decimal("0.0001"))
    return format(d.normalize(), "f")


@dataclass(frozen=True)
class Holding:
    owner: str
    owner_key: str
    area: Decimal


@dataclass(frozen=True)
class PastTransfer:
    from_key: str | None
    to_owner: str
    event_date: date


@dataclass(frozen=True)
class Verdict:
    verdict: str  # success | warning | blocked
    rule_id: str
    reason_en: str
    reason_bn: str
    calc: dict[str, Any] = field(default_factory=dict)


def check(
    *,
    parcel_found: bool,
    holdings: list[Holding],
    transfers: list[PastTransfer],
    seller: str,
    buyer: str,
    area: Decimal,
    deed_date: date,
    rapid_window_days: int,
) -> Verdict:
    if not parcel_found:
        return Verdict(
            "blocked",
            "R0",
            "This plot was not found in the supplied dataset. Check the mouza and dag number.",
            "এই দাগটি সরবরাহ করা ডেটাসেটে পাওয়া যায়নি। মৌজা ও দাগ নম্বর আবার দেখুন।",
        )

    owners_en = ", ".join(h.owner for h in holdings) or "-"
    owners_bn = " ও ".join(h.owner for h in holdings) or "-"
    held = next((h.area for h in holdings if h.owner_key == key(seller)), None)

    if held is None:
        already_sold = any(t.from_key == key(seller) for t in transfers)
        if already_sold:
            return Verdict(
                "blocked",
                "R1",
                f"This plot was already sold. The current owner is {owners_en}.",
                f"এই দাগ আগেই বিক্রি হয়েছে, বর্তমান মালিক {owners_bn}।",
                {"current_owners": [h.owner for h in holdings]},
            )
        return Verdict(
            "blocked",
            "R2",
            "The seller is not the record owner of this plot.",
            "বিক্রেতা রেকর্ডের মালিক নন।",
            {"current_owners": [h.owner for h in holdings]},
        )

    if area > held:
        return Verdict(
            "blocked",
            "R2",
            f"The seller's record shows {fmt(held)} shatak, but {fmt(area)} shatak is being sold.",
            f"বিক্রেতার রেকর্ডে {fmt(held)} শতক আছে, কিন্তু {fmt(area)} শতক বিক্রির আবেদন করা হয়েছে।",
            {"held": fmt(held), "requested": fmt(area)},
        )

    transfer_dates = [t.event_date for t in transfers if t.from_key is not None]
    if transfer_dates:
        last = max(transfer_dates)
        days = (deed_date - last).days
        if days < 0:
            return Verdict(
                "warning",
                "R5",
                f"The deed date is {-days} day(s) before the last recorded transfer. A human should check it.",
                f"দলিলের তারিখ শেষ নথিভুক্ত হস্তান্তরের {-days} দিন আগের। মানুষের যাচাই দরকার।",
                {"last_transfer": last.isoformat(), "days_since": days, "heuristic": True},
            )
        if days <= rapid_window_days:
            when_en = "on the same day as" if days == 0 else f"only {days} day(s) after"
            when_bn = "একই দিনে" if days == 0 else f"মাত্র {days} দিন পরে"
            return Verdict(
                "warning",
                "R5",
                f"Another application {when_en} the last transfer of this plot "
                f"(window: {rapid_window_days} days). Potentially suspicious, human review needed.",
                f"এই দাগের আগের হস্তান্তরের {when_bn} আবার আবেদন "
                f"(সীমা {rapid_window_days} দিন)। সম্ভাব্য সন্দেহজনক, মানুষের যাচাই দরকার।",
                {"last_transfer": last.isoformat(), "days_since": days, "heuristic": True},
            )

    return Verdict(
        "success",
        "OK",
        f"The seller is the record owner and the area fits. Ownership moves to {buyer}.",
        f"বিক্রেতা রেকর্ডের মালিক এবং পরিমাণ মিলেছে। মালিকানা {buyer}-এ হস্তান্তর হবে।",
        {"held": fmt(held), "requested": fmt(area)},
    )
