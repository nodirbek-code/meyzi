import pytest

from apps.accounts.models import User
from apps.agencies.models import Agency, AgencyApplication, AgencyMember

pytestmark = pytest.mark.django_db

APPLICATION = {"agency_name": "Silk Road Tours", "contact_person": "Aziz", "phone": "+998901234567"}


def test_anyone_can_apply(api):
    res = api.post("/api/v1/agencies/applications/", APPLICATION, format="json")
    assert res.status_code == 201, res.data
    assert res.data["status"] == "new"
    assert AgencyApplication.objects.get().user is None


def test_application_requires_fields(api):
    res = api.post("/api/v1/agencies/applications/", {"agency_name": "X"}, format="json")
    assert res.status_code == 400
    assert {"contact_person", "phone"} <= set(res.data)


def test_user_sees_only_own_applications(auth_api, api):
    api.post("/api/v1/agencies/applications/", APPLICATION, format="json")  # anonim
    auth_api.post("/api/v1/agencies/applications/", APPLICATION, format="json")
    assert auth_api.get("/api/v1/agencies/applications/").data["count"] == 1


def test_admin_approves_application(auth_api, admin_api, user):
    app_id = auth_api.post("/api/v1/agencies/applications/", APPLICATION, format="json").data["id"]

    assert auth_api.post(f"/api/v1/agencies/applications/{app_id}/approve/").status_code == 403
    res = admin_api.post(f"/api/v1/agencies/applications/{app_id}/approve/")
    assert res.status_code == 201, res.data
    assert res.data["slug"] == "silk-road-tours"
    assert res.data["is_verified"] is True

    agency = Agency.objects.get(slug="silk-road-tours")
    assert agency.commission_percent == 15
    assert AgencyMember.objects.get(user=user).agency == agency
    user.refresh_from_db()
    assert user.role == User.Role.AGENCY

    # ikkinchi marta tasdiqlab bo'lmaydi
    assert admin_api.post(f"/api/v1/agencies/applications/{app_id}/approve/").status_code == 400


def test_admin_rejects_application(api, admin_api):
    app_id = api.post("/api/v1/agencies/applications/", APPLICATION, format="json").data["id"]
    res = admin_api.post(
        f"/api/v1/agencies/applications/{app_id}/reject/", {"note": "Hujjat yo'q"}, format="json"
    )
    assert res.status_code == 200
    assert res.data["status"] == "rejected"
    assert res.data["admin_note"] == "Hujjat yo'q"
    assert not Agency.objects.exists()


def test_duplicate_slug_gets_suffix(api, admin_api, agency):
    data = {**APPLICATION, "agency_name": "Vodiy Tour"}
    app_id = api.post("/api/v1/agencies/applications/", data, format="json").data["id"]
    res = admin_api.post(f"/api/v1/agencies/applications/{app_id}/approve/")
    assert res.data["slug"] == "vodiy-tour-2"


def test_public_agency_list_hides_suspended(api, agency, tour):
    Agency.objects.create(name="Yopiq", slug="yopiq", status=Agency.Status.SUSPENDED)
    res = api.get("/api/v1/agencies/")
    assert [a["slug"] for a in res.data["results"]] == ["vodiy-tour"]
    assert res.data["results"][0]["tours_count"] == 1
    assert "commission_percent" not in res.data["results"][0]


def test_cabinet_agency_profile(agency_api, auth_api, agency):
    assert auth_api.get("/api/v1/cabinet/agency/").status_code == 403

    res = agency_api.patch(
        "/api/v1/cabinet/agency/",
        {"description": "Yangi tavsif", "commission_percent": "1", "is_verified": False},
        format="json",
    )
    assert res.status_code == 200
    agency.refresh_from_db()
    assert agency.description == "Yangi tavsif"
    assert agency.commission_percent == 15  # o'zgarmaydi
    assert agency.is_verified is True


def test_suspended_agency_loses_cabinet(agency_api, agency):
    agency.status = Agency.Status.SUSPENDED
    agency.save()
    assert agency_api.get("/api/v1/cabinet/agency/").status_code == 403
