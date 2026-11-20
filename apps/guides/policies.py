"""
Individual gid qoidalari (LAZURI taqdimoti, 11-slayd). Turlarga emas, faqat gid bronlariga tegishli.

Turist bekor qilsa (boshlanishigacha qolgan vaqt):  >=48s — 100%, 24–48s — 50%, 12–24s — 25%, <12s — 0%.
Gid bekor qilsa: turistga doim 100%. Gidga jarima: >=72s — yo'q, 48–72s — $5, 24–48s — $10 + 1 ogohlantirish,
<24s — $20 + 2 ogohlantirish. Gid kelmasa — $25, 3 marta = profil bloklanadi.
Turist kelmasa — qaytarilmaydi, gidga jami summaning 30% kompensatsiya. Gid 1 soat kutadi.
"""

from datetime import timedelta
from decimal import Decimal

TOURIST_NO_SHOW_WAIT = timedelta(hours=1)
TOURIST_NO_SHOW_GUIDE_SHARE = Decimal("0.30")
GUIDE_NO_SHOW_PENALTY_USD = Decimal("25")
GUIDE_NO_SHOW_LIMIT = 3
LOW_RATING_THRESHOLD = Decimal("4.00")
LOW_RATING_MIN_REVIEWS = 5  # bitta yomon sharh bilan bloklanmasin


def tourist_refund_ratio(time_left: timedelta) -> Decimal:
    hours = time_left.total_seconds() / 3600
    if hours >= 48:
        return Decimal("1")
    if hours >= 24:
        return Decimal("0.5")
    if hours >= 12:
        return Decimal("0.25")
    return Decimal("0")


def guide_cancel_penalty(time_left: timedelta) -> tuple[Decimal, int]:
    """(jarima $, ogohlantirishlar soni)."""
    hours = time_left.total_seconds() / 3600
    if hours >= 72:
        return Decimal("0"), 0
    if hours >= 48:
        return Decimal("5"), 0
    if hours >= 24:
        return Decimal("10"), 1
    return Decimal("20"), 2
