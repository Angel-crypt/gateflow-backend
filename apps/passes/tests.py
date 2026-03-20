import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.destinations.models import Destination, IndustrialPark
from apps.passes.models import AccessPass
from apps.users.models import User

URL = "/api/passes/"
VALIDATE_URL = "/api/passes/validate/"


# ── Fixtures ───


@pytest.fixture
def park():
    return IndustrialPark.objects.create(name="Parque Norte")


@pytest.fixture
def other_park():
    return IndustrialPark.objects.create(name="Parque Sur")


@pytest.fixture
def destination(park):
    return Destination.objects.create(name="Empresa ABC", type="company", park=park, is_active=True)


@pytest.fixture
def other_destination(other_park):
    return Destination.objects.create(name="Empresa XYZ", type="company", park=other_park, is_active=True)


@pytest.fixture
def admin(park):
    return User.objects.create_user(email="admin@park.com", password="pass1234", role="admin", park=park)


@pytest.fixture
def guard(park):
    return User.objects.create_user(email="guard@park.com", password="pass1234", role="guard", park=park)


@pytest.fixture
def company(park, destination):
    user = User.objects.create_user(email="company@park.com", password="pass1234", role="company", park=park)
    user.destinations.set([destination])
    return user


@pytest.fixture
def other_company(other_park, other_destination):
    user = User.objects.create_user(email="company@other.com", password="pass1234", role="company", park=other_park)
    user.destinations.set([other_destination])
    return user


def make_pass(destination, created_by, pass_type="day", is_active=True, is_used=False):
    now = timezone.now()
    return AccessPass.objects.create(
        destination=destination,
        created_by=created_by,
        visitor_name="Juan Pérez",
        pass_type=pass_type,
        valid_from=now - timezone.timedelta(hours=1),
        valid_to=now + timezone.timedelta(hours=8),
        is_active=is_active,
        is_used=is_used,
    )


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── Model ─────


@pytest.mark.django_db
def test_access_pass_model_exists():
    assert AccessPass is not None


@pytest.mark.django_db
def test_is_valid_active_pass(destination, company):
    ap = make_pass(destination, company)
    assert ap.is_valid() is True


@pytest.mark.django_db
def test_is_valid_inactive_pass(destination, company):
    ap = make_pass(destination, company, is_active=False)
    assert ap.is_valid() is False


@pytest.mark.django_db
def test_is_valid_single_use_already_used(destination, company):
    ap = make_pass(destination, company, pass_type="single", is_used=True)
    assert ap.is_valid() is False