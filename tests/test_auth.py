import pytest

from apps.accounts.models import User

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def test_register_returns_tokens(api):
    res = api.post(
        "/api/v1/auth/register/",
        {"email": "New@Example.com", "password": PASSWORD, "first_name": "Vali", "role": "guide"},
        format="json",
    )
    assert res.status_code == 201, res.data
    assert res.data["user"]["email"] == "new@example.com"
    assert res.data["user"]["role"] == "guide"
    assert res.data["access"] and res.data["refresh"]
    assert User.objects.get(email="new@example.com").check_password(PASSWORD)


def test_register_cannot_become_admin(api):
    res = api.post(
        "/api/v1/auth/register/",
        {"email": "x@example.com", "password": PASSWORD, "role": "admin"},
        format="json",
    )
    assert res.status_code == 400
    assert "role" in res.data


def test_register_duplicate_email(api, user):
    res = api.post(
        "/api/v1/auth/register/", {"email": "TURIST@example.com", "password": PASSWORD}, format="json"
    )
    assert res.status_code == 400
    assert "email" in res.data


def test_register_weak_password(api):
    res = api.post("/api/v1/auth/register/", {"email": "w@example.com", "password": "123"}, format="json")
    assert res.status_code == 400


def test_login_and_me(api, user):
    res = api.post(
        "/api/v1/auth/login/", {"email": "Turist@Example.com", "password": PASSWORD}, format="json"
    )
    assert res.status_code == 200, res.data
    assert res.data["user"]["email"] == user.email

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    me = api.get("/api/v1/auth/me/")
    assert me.status_code == 200
    assert me.data["first_name"] == "Ali"


def test_login_wrong_password(api, user):
    res = api.post("/api/v1/auth/login/", {"email": user.email, "password": "notogri"}, format="json")
    assert res.status_code == 401


def test_me_requires_auth(api):
    assert api.get("/api/v1/auth/me/").status_code == 401


def test_me_update_cannot_change_role(auth_api, user):
    res = auth_api.patch("/api/v1/auth/me/", {"first_name": "Aziz", "role": "admin"}, format="json")
    assert res.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Aziz"
    assert user.role == User.Role.TOURIST


def test_change_password(auth_api, user):
    res = auth_api.post(
        "/api/v1/auth/me/password/",
        {"old_password": PASSWORD, "new_password": "Yangi-Parol-2027"},
        format="json",
    )
    assert res.status_code == 204
    user.refresh_from_db()
    assert user.check_password("Yangi-Parol-2027")


def test_logout_blacklists_refresh(api, user):
    tokens = api.post("/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json").data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert api.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json").status_code == 204

    res = api.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert res.status_code == 401
