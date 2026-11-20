import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_features(api):
    res = api.get("/api/v1/features/")
    assert res.status_code == 200
    assert [lang["code"] for lang in res.data["languages"]] == ["uz", "ru", "en"]
    assert res.data["default_language"] == "uz"
    assert res.data["ai_route"] == {
        "enabled": False,
        "status_text": "Tez kunda",
        "description": res.data["ai_route"]["description"],
    }
    assert res.data["multilingual_content"]["enabled"] is False
    assert [p["code"] for p in res.data["payments"]] == ["payme", "click", "uzum_nasiya"]


def test_only_three_languages_for_users(api):
    assert [c for c, _ in User.Language.choices] == ["uz", "ru", "en"]
    res = api.post(
        "/api/v1/auth/register/",
        {"email": "cn@example.com", "password": "Kuchli-Parol-2026", "language": "zh"},
        format="json",
    )
    assert res.status_code == 400
    assert "language" in res.data


def test_seed_demo_idempotent(api):
    from django.core.management import call_command

    call_command("seed_demo")
    call_command("seed_demo")
    assert api.get("/api/v1/guides/").data["count"] == 2
    assert api.get("/api/v1/hotels/").data["count"] == 2
    assert api.get("/api/v1/tours/").data["count"] == 3
    assert api.get("/api/v1/guides/?destination=zomin").data["results"][0]["slug"] == "dilnoza-rahimova"
