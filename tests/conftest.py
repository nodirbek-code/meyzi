import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Destination, Place

PASSWORD = "Kuchli-Parol-2026"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="turist@example.com", password=PASSWORD, first_name="Ali")


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(email="admin@example.com", password=PASSWORD)


@pytest.fixture
def auth_api(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def admin_api(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    return client


@pytest.fixture
def samarqand(db):
    return Destination.objects.create(name="Samarqand", slug="samarqand", is_featured=True)


@pytest.fixture
def registon(samarqand):
    return Place.objects.create(
        destination=samarqand, name="Registon", slug="registon", category="monument", entry_fee_uzs=65000
    )


# ---------- Agentliklar va turlar ----------


@pytest.fixture
def agency(db):
    from apps.agencies.models import Agency

    return Agency.objects.create(name="Vodiy Tour", slug="vodiy-tour", is_verified=True)


@pytest.fixture
def agency_user(agency):
    from apps.agencies.models import AgencyMember

    u = User.objects.create_user(email="agent@example.com", password=PASSWORD, role=User.Role.AGENCY)
    AgencyMember.objects.create(agency=agency, user=u, role=AgencyMember.Role.OWNER)
    return u


@pytest.fixture
def agency_api(agency_user):
    client = APIClient()
    client.force_authenticate(agency_user)
    return client


@pytest.fixture
def category(db):
    from apps.tours.models import TourCategory

    return TourCategory.objects.create(name="Tog'", slug="tog")


@pytest.fixture
def tour(agency, samarqand, category):
    from apps.tours.models import Tour

    t = Tour.objects.create(
        agency=agency,
        destination=samarqand,
        title="Samarqand 1 kun",
        slug="samarqand-1-kun",
        price_uzs=890_000,
    )
    t.categories.add(category)
    t.publish()
    t.save()
    return t


@pytest.fixture
def departure(tour):
    from datetime import timedelta

    from django.utils import timezone

    from apps.tours.models import Departure

    return Departure.objects.create(tour=tour, date=timezone.localdate() + timedelta(days=7), seats_total=20)
