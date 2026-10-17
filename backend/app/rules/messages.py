"""Human-readable alert text (English + Bangla), built from templates.

Wording rule (PRD section 6): say "potential conflict", "record mismatch",
"not found in supplied dataset", "human review needed". Never "fraud confirmed"
or "ownership verified". Templates only change the language, never the result.
"""

from __future__ import annotations

from typing import Any

TEMPLATES: dict[str, dict[str, str]] = {
    "insufficient": {
        "en": "Insufficient data: {reason}. The result cannot be calculated; "
        "missing values were not treated as zero.",
        "bn": "অপর্যাপ্ত তথ্য: {reason}। হিসাব করা যায়নি; অনুপস্থিত মান শূন্য ধরা হয়নি।",
        "next_en": "Supply the missing value in the dataset and re-run the audit.",
        "next_bn": "অনুপস্থিত মানটি ডেটাসেটে যোগ করে audit আবার চালান।",
    },
    "R1": {
        "en": "Potential conflict: portion {portion_key} appears in two active transfers to "
        "different recipients ({buyer_a} in {t_a}, {buyer_b} in {t_b}). Human review needed.",
        "bn": "সম্ভাব্য সংঘাত: {portion_key} অংশটি দুটি সক্রিয় হস্তান্তরে ভিন্ন গ্রহীতাকে দেওয়া "
        "দেখা যাচ্ছে ({buyer_a}: {t_a}, {buyer_b}: {t_b})। মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Compare the two deeds and their mutation entries; confirm which, if any, "
        "was cancelled or reversed.",
        "next_bn": "দুটি দলিল ও তাদের মিউটেশন এন্ট্রি মিলিয়ে দেখুন এবং কোনটি (যদি থাকে) " "বাতিল বা রদ হয়েছে তা নিশ্চিত করুন।",
    },
    "R2": {
        "en": "Potential conflict: transfer {t} of {attempted} by {seller} exceeds the {available} "
        "available just before the event (opening {opening} + incoming {incoming} - prior "
        "outgoing {outgoing}). Excess: {excess}. Human review needed.",
        "bn": "সম্ভাব্য সংঘাত: {seller}-এর {t} হস্তান্তরের পরিমাণ {attempted}, কিন্তু ঘটনার ঠিক আগে "
        "প্রাপ্য ছিল {available} (শুরুর {opening} + আগত {incoming} - আগের প্রদত্ত {outgoing})। "
        "অতিরিক্ত: {excess}। মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Check the seller's entitlement record and the earlier transfers on this parcel.",
        "next_bn": "বিক্রেতার প্রাপ্য অংশের রেকর্ড ও এই পার্সেলের আগের হস্তান্তরগুলো যাচাই করুন।",
    },
    "R3_gap": {
        "en": "Record gap: registered transfer {t} (deed {deed}) - linked mutation entry "
        "not found in supplied dataset. Human review needed.",
        "bn": "রেকর্ডে ফাঁক: নিবন্ধিত হস্তান্তর {t} (দলিল {deed})-এর কোনো সংযুক্ত মিউটেশন এন্ট্রি "
        "সরবরাহকৃত ডেটাসেটে পাওয়া যায়নি। মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Check the AC Land office mutation records for this transfer.",
        "next_bn": "এই হস্তান্তরের জন্য এসি ল্যান্ড অফিসের মিউটেশন রেকর্ড যাচাই করুন।",
    },
    "R3_mismatch": {
        "en": "Record mismatch: transfer {t} and mutation {m} do not align ({diffs}). " "Human review needed.",
        "bn": "রেকর্ড অমিল: হস্তান্তর {t} ও মিউটেশন {m} মিলছে না ({diffs})। " "মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Compare the registered deed with the mutation entry field by field.",
        "next_bn": "নিবন্ধিত দলিল ও মিউটেশন এন্ট্রি ঘর ধরে ধরে মিলিয়ে দেখুন।",
    },
    "R4_uncertain": {
        "en": "Uncertain link: parent {p} to child {c} has confidence {conf} (minimum {min}). "
        "Not merged automatically; human review needed.",
        "bn": "অনিশ্চিত সংযোগ: পিতা-পার্সেল {p} ও সন্তান-পার্সেল {c}-এর নির্ভরযোগ্যতা {conf} "
        "(সর্বনিম্ন {min})। স্বয়ংক্রিয়ভাবে যুক্ত করা হয়নি; মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Confirm the parent-child relationship from the survey or mutation record.",
        "next_bn": "জরিপ বা মিউটেশন রেকর্ড থেকে পিতা-সন্তান সম্পর্ক নিশ্চিত করুন।",
    },
    "R4_area": {
        "en": "Area anomaly: child parcels of {p} total {sum} but the parent area is {parent} "
        "(difference {diff}, tolerance {tol}). Human review needed.",
        "bn": "আয়তনে অসঙ্গতি: {p}-এর সন্তান-পার্সেলগুলোর মোট আয়তন {sum}, কিন্তু পিতা-পার্সেলের "
        "আয়তন {parent} (পার্থক্য {diff}, সহনসীমা {tol})। মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Re-check the split areas against the survey record.",
        "next_bn": "জরিপ রেকর্ডের সাথে ভাগ হওয়া আয়তন আবার মিলিয়ে দেখুন।",
    },
    "R5": {
        "en": "Heuristic only: {n} active transfers on parcel {p} between {first} and {last}; "
        "threshold is {min} within {days} days. Human review needed.",
        "bn": "শুধু অনুমানভিত্তিক সংকেত: {first} থেকে {last}-এর মধ্যে পার্সেল {p}-এ {n}টি সক্রিয় "
        "হস্তান্তর; সীমা {days} দিনে {min}টি। মানুষের পর্যালোচনা প্রয়োজন।",
        "next_en": "Review the sequence of transfers and the parties involved.",
        "next_bn": "হস্তান্তরের ক্রম ও সংশ্লিষ্ট পক্ষগুলো পর্যালোচনা করুন।",
    },
}

BANNED_PHRASES = ("fraud confirmed", "ownership verified", "proven fraud", "forgery confirmed")


def render(kind: str, **values: Any) -> tuple[str, str, str, str]:
    """Return (message_en, message_bn, next_check_en, next_check_bn)."""
    t = TEMPLATES[kind]
    return (
        t["en"].format(**values),
        t["bn"].format(**values),
        t["next_en"],
        t["next_bn"],
    )
