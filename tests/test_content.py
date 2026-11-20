import pytest

from apps.content.models import Article, FaqItem, Page

pytestmark = pytest.mark.django_db


def test_articles_only_published(api, samarqand, tour):
    a = Article.objects.create(
        title="Samarqandga 1 kunda",
        slug="samarqand-1-kun",
        body="Matn",
        status="published",
        destination=samarqand,
    )
    a.tours.add(tour)
    Article.objects.create(title="Qoralama", slug="qoralama", body="x")

    res = api.get("/api/v1/articles/")
    assert [x["slug"] for x in res.data["results"]] == ["samarqand-1-kun"]
    assert res.data["results"][0]["published_at"]
    assert api.get("/api/v1/articles/qoralama/").status_code == 404

    detail = api.get("/api/v1/articles/samarqand-1-kun/").data
    assert detail["body"] == "Matn"
    assert [t["slug"] for t in detail["tours"]] == [tour.slug]
    assert api.get("/api/v1/articles/?destination=buxoro").data["count"] == 0


def test_faq_and_pages(api):
    FaqItem.objects.create(question="Qanday bron qilaman?", answer="...", sort_order=1)
    FaqItem.objects.create(question="Yashirin", answer="...", is_active=False)
    Page.objects.create(slug="terms", title="Foydalanish shartlari", body="...")

    assert [f["question"] for f in api.get("/api/v1/faq/").data] == ["Qanday bron qilaman?"]
    assert api.get("/api/v1/pages/terms/").data["title"] == "Foydalanish shartlari"
    assert api.get("/api/v1/pages/privacy/").status_code == 404


def test_seed_content_idempotent(api):
    from django.core.management import call_command

    call_command("seed_content")
    call_command("seed_content")
    faq = api.get("/api/v1/faq/").data
    assert len(faq) == FaqItem.objects.count() >= 8
    assert faq[0]["question"] == "Turni qanday bron qilaman?"
