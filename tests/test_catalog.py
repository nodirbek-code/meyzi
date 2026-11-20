import pytest
from django.core.management import call_command

from apps.catalog.models import Destination, Place

pytestmark = pytest.mark.django_db


def test_destination_list_public(api, registon):
    res = api.get("/api/v1/catalog/destinations/")
    assert res.status_code == 200
    item = res.data["results"][0]
    assert item["slug"] == "samarqand"
    assert item["places_count"] == 1


def test_unpublished_hidden_from_public(api, admin_api, samarqand):
    Destination.objects.create(name="Yashirin", slug="yashirin", is_published=False)
    assert api.get("/api/v1/catalog/destinations/").data["count"] == 1
    assert api.get("/api/v1/catalog/destinations/yashirin/").status_code == 404
    assert admin_api.get("/api/v1/catalog/destinations/").data["count"] == 2


def test_place_detail_by_slug(api, registon):
    res = api.get("/api/v1/catalog/places/registon/")
    assert res.status_code == 200
    assert res.data["destination"]["slug"] == "samarqand"
    assert res.data["is_free"] is False
    assert "images" in res.data


def test_place_filters(api, samarqand, registon):
    Place.objects.create(destination=samarqand, name="Siyob bozori", slug="siyob", category="bazaar")
    buxoro = Destination.objects.create(name="Buxoro", slug="buxoro")
    Place.objects.create(destination=buxoro, name="Ark", slug="ark", category="monument")

    def slugs(query):
        return {p["slug"] for p in api.get(f"/api/v1/catalog/places/{query}").data["results"]}

    assert slugs("?destination=samarqand") == {"registon", "siyob"}
    assert slugs("?category=monument") == {"registon", "ark"}
    assert slugs("?is_free=true") == {"siyob", "ark"}
    assert slugs("?search=bozor") == {"siyob"}


def test_place_hidden_when_destination_unpublished(api, samarqand, registon):
    samarqand.is_published = False
    samarqand.save()
    assert api.get("/api/v1/catalog/places/").data["count"] == 0


def test_only_admin_can_write(api, auth_api, admin_api, samarqand):
    payload = {"destination": samarqand.id, "name": "Go'ri Amir", "slug": "gori-amir", "category": "monument"}
    assert api.post("/api/v1/catalog/places/", payload, format="json").status_code == 401
    assert auth_api.post("/api/v1/catalog/places/", payload, format="json").status_code == 403
    assert admin_api.post("/api/v1/catalog/places/", payload, format="json").status_code == 201


def test_seed_catalog_is_idempotent():
    call_command("seed_catalog")
    call_command("seed_catalog")
    assert Destination.objects.count() == 4
    assert Place.objects.filter(destination__slug="samarqand").count() == 4


def test_api_docs_schema(api):
    assert api.get("/api/schema/").status_code == 200
