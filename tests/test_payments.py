import pytest

pytestmark = pytest.mark.django_db


def test_payment_methods_coming_soon(api):
    res = api.get("/api/v1/payments/methods/")
    assert res.status_code == 200
    assert [m["code"] for m in res.data] == ["payme", "click", "uzum_nasiya"]
    for m in res.data:
        assert m["enabled"] is False
        assert m["status_text"] == "Tez kunda"
        assert "logo" in m


def test_logo_url_when_file_exists(api, monkeypatch):
    from apps.payments import methods

    monkeypatch.setattr(methods.finders, "find", lambda path: path == "payments/payme.svg")
    res = api.get("/api/v1/payments/methods/")
    logos = {m["code"]: m["logo"] for m in res.data}
    assert logos["payme"].endswith("/static/payments/payme.svg")
    assert logos["click"] is None
