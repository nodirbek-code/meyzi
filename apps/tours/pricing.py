from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings


def installment(price_uzs: int) -> dict:
    """
    Muddatli to'lov hisob-kitobi (Uzum Nasiya kabi).
    Jami = narx x ustama (sukut 1.44), oylik = jami / oylar (sukut 12), so'mgacha yaxlitlanadi.
    Masalan: 890 000 -> 106 800 x 12.
    """
    months = settings.MEYZI_INSTALLMENT_MONTHS
    total = (Decimal(price_uzs) * settings.MEYZI_INSTALLMENT_MARKUP).quantize(Decimal("1"), ROUND_HALF_UP)
    monthly = (total / months).quantize(Decimal("1"), ROUND_HALF_UP)
    return {"months": months, "monthly_uzs": int(monthly), "total_uzs": int(total)}
