"""Sample data for the judge demo: five more plots (Bangla and English names) and seven past requests.

Everything goes through the same checker as a real request, so the results shown on the dashboard, alert list and
plot history are genuine outputs of the rules, not painted-on numbers. All names are made up.
Calling `load` twice does nothing the second time.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from . import khatian, service

LONG_AGO = 400  # days: the opening record is older than any sample sale

# (mouza, dag, owner, shatak)
PLOTS = [
    ("নমুনা মৌজা-৩", "301", "আব্দুল হামিদ", "8"),
    ("নমুনা মৌজা-৩", "302", "রোকেয়া খাতুন", "12"),
    ("Sample Mouza 4", "401", "Karim Hossain", "10"),
    ("Sample Mouza 4", "402", "Nasrin Akter", "14"),
    ("Sample Mouza 4", "403", "Sultana Razia", "6"),
]

# (days ago, mouza, dag, seller, buyer, shatak): what each one should produce is noted at the end of the line
DEALS = [
    (45, "নমুনা মৌজা-৩", "301", "আব্দুল হামিদ", "ফারুক আহমেদ", "3"),  # success, partial sale
    (40, "Sample Mouza 4", "401", "Karim Hossain", "Mizanur Rahman", "10"),  # success
    (25, "Sample Mouza 4", "402", "Nasrin Akter", "Tania Sultana", "14"),  # success
    (20, "নমুনা মৌজা-৩", "301", "আব্দুল হামিদ", "মিনা বেগম", "8"),  # blocked R2: only 5 shatak left
    (18, "Sample Mouza 4", "402", "Tania Sultana", "Rubel Hasan", "14"),  # warning R5: 7 days after the last sale
    (15, "নমুনা মৌজা-৩", "302", "অজানা ব্যক্তি", "মিনা বেগম", "12"),  # blocked R2: seller is not the owner
    (12, "Sample Mouza 4", "401", "Karim Hossain", "Another Buyer", "10"),  # blocked R1: already sold
]


def load(db: Session, officer: str, rapid_window_days: int) -> dict[str, object]:
    first = PLOTS[0]
    if service.find_parcel(db, first[0], first[1]) is not None:
        return {"loaded": False, "plots": len(PLOTS), "requests": len(DEALS)}
    today = date.today()
    for mouza, dag, owner, area in PLOTS:
        service.add_plot(
            db,
            officer=officer,
            mouza=mouza,
            dag_no=dag,
            owner=owner,
            area=Decimal(area),
            since=today - timedelta(days=LONG_AGO),
        )
    for days, mouza, dag, seller, buyer, area in sorted(DEALS, key=lambda d: -d[0]):
        service.register(
            db,
            officer=officer,
            mouza=mouza,
            dag_no=dag,
            seller=seller,
            buyer=buyer,
            area=Decimal(area),
            deed_date=today - timedelta(days=days),
            rapid_window_days=rapid_window_days,
        )
    # Mizanur Rahman's namjari is finished (green on the public page); the other new owners are still pending (amber).
    parcel = service.find_parcel(db, "Sample Mouza 4", "401")
    if parcel is not None:
        khatian.complete_mutation(db, parcel.id)
        db.commit()
    return {"loaded": True, "plots": len(PLOTS), "requests": len(DEALS)}
