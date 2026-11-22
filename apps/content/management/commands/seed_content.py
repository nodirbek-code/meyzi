from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Destination
from apps.content.models import Article, FaqItem, Page
from apps.content.seed_data import ARTICLES, FAQ, PAGES


class Command(BaseCommand):
    help = (
        "Sayt kontentini yuklaydi: savol-javob, sahifalar (foydalanish shartlari, maxfiylik siyosati) va "
        "qo'llanmalar. Qayta ishga tushirish xavfsiz: FAQ yangilanadi; admin panelda tahrirlangan sahifa va "
        "maqolalar faqat --force bilan qayta yoziladi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Mavjud sahifa va maqolalarni ham seed_data matni bilan yangilash",
        )

    @transaction.atomic
    def handle(self, *args, force=False, **options):
        faq_new = 0
        for order, (question, answer) in enumerate(FAQ, start=1):
            _, is_new = FaqItem.objects.update_or_create(
                question=question, defaults={"answer": answer, "sort_order": order, "is_active": True}
            )
            faq_new += is_new

        pages_new = pages_updated = 0
        for slug, title, body in PAGES:
            body = body.strip()
            page, is_new = Page.objects.get_or_create(slug=slug, defaults={"title": title, "body": body})
            if is_new:
                pages_new += 1
            elif force:
                page.title, page.body, page.is_published = title, body, True
                page.save()
                pages_updated += 1

        art_new = art_updated = 0
        destinations = {d.slug: d for d in Destination.objects.all()}
        for slug, title, excerpt, dest_slug, body in ARTICLES:
            values = {
                "title": title,
                "excerpt": excerpt,
                "body": body.strip(),
                "destination": destinations.get(dest_slug) if dest_slug else None,
                "status": Article.Status.PUBLISHED,
            }
            article = Article.objects.filter(slug=slug).first()
            if article is None:
                Article.objects.create(slug=slug, **values)
                art_new += 1
            elif force:
                for field, value in values.items():
                    setattr(article, field, value)
                article.save()
                art_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"FAQ: {len(FAQ)} ta ({faq_new} yangi). "
                f"Sahifalar: {pages_new} yangi, {pages_updated} yangilandi. "
                f"Qo'llanmalar: {art_new} yangi, {art_updated} yangilandi."
            )
        )
