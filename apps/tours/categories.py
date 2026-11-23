"""Tur toifalari — yagona ro'yxat (seed_tours va 0006 migratsiyasi shundan oladi).

Avvalgi 4 ta toifadan 8 taga (2026-11): "Madaniy" juda keng edi (turlarning 2/3 qismi) — filtr ishlamasdi.
"Dam olish kuni" nomi "faqat shanba-yakshanba" deb tushunilardi — endi davomiylik bo'yicha: "Qisqa sayohat".
"""

# (slug, nomi, ikonka, tartib)
CATEGORIES = [
    ("tarix", "Tarix va me'morchilik", "🕌", 1),
    ("gastronomiya", "Gastronomiya", "🍲", 2),
    ("hunarmandchilik", "Hunarmandchilik", "🧵", 3),
    ("ziyorat", "Ziyorat", "🤲", 4),
    ("tog", "Tog'", "⛰️", 5),
    ("tabiat", "Tabiat va dam olish", "🌿", 6),
    ("sarguzasht", "Sarguzasht", "🧗", 7),
    ("qisqa-sayohat", "Qisqa sayohat (1–2 kun)", "🌤️", 8),
]

# Eski slug → yangi slug (mavjud turlar o'z toifasini saqlab qoladi)
RENAMED = {"madaniy": "tarix", "dam-olish-kuni": "qisqa-sayohat"}
