"""Tur toifalari: 4 tadan 8 taga. Eski "madaniy" va "dam-olish-kuni" o'chirilmaydi — qayta nomlanadi,
shuning uchun ularga biriktirilgan turlar o'z toifasini yo'qotmaydi."""

from django.db import migrations

# Migratsiya ilova kodiga bog'liq bo'lmasin — ro'yxat shu yerda (apps/tours/categories.py bilan bir xil)
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
RENAMED = {"madaniy": "tarix", "dam-olish-kuni": "qisqa-sayohat"}


def forwards(apps, schema_editor):
    TourCategory = apps.get_model("tours", "TourCategory")
    for old, new in RENAMED.items():
        if not TourCategory.objects.filter(slug=new).exists():
            TourCategory.objects.filter(slug=old).update(slug=new)
    for slug, name, icon, order in CATEGORIES:
        TourCategory.objects.update_or_create(
            slug=slug, defaults={"name": name, "icon": icon, "sort_order": order, "is_active": True}
        )


def backwards(apps, schema_editor):
    TourCategory = apps.get_model("tours", "TourCategory")
    for old, new in RENAMED.items():
        TourCategory.objects.filter(slug=new).update(slug=old)


class Migration(migrations.Migration):
    dependencies = [("tours", "0005_tour_guides_tour_hotels")]

    operations = [migrations.RunPython(forwards, backwards)]
