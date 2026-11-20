"""
Bekor qilish siyosatlari (TripHub modeli).
Bronlar bosqichida qaytariladigan summa shu yerdan hisoblanadi.

- free (bepul):         jo'nashdan >= 24 soat oldin — 100%, keyin — 0%
- partial (qisman):     jo'nashdan > 48 soat oldin — 50%, keyin — 0%
- non_refundable:       0%
"""

from datetime import datetime, timedelta
from decimal import Decimal

from .models import CancellationPolicy

POLICY_TEXT = {
    CancellationPolicy.FREE: "Jo'nashdan kamida 24 soat oldin bekor qilsangiz — to'liq qaytariladi. "
    "24 soatdan kam qolganda qaytarilmaydi.",
    CancellationPolicy.PARTIAL: "Jo'nashdan 48 soatdan ko'proq oldin bekor qilsangiz — 50% qaytariladi. "
    "48 soat va undan kam qolganda qaytarilmaydi.",
    CancellationPolicy.NON_REFUNDABLE: "To'langan summa qaytarilmaydi.",
}


def refund_ratio(policy: str, departure_at: datetime, cancelled_at: datetime) -> Decimal:
    """Qaytariladigan ulush (0..1)."""
    left = departure_at - cancelled_at
    if policy == CancellationPolicy.FREE:
        return Decimal("1") if left >= timedelta(hours=24) else Decimal("0")
    if policy == CancellationPolicy.PARTIAL:
        return Decimal("0.5") if left > timedelta(hours=48) else Decimal("0")
    return Decimal("0")
