import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.access.models import AccessLog
from apps.destinations.models import Destination, IndustrialPark
from apps.passes.models import AccessPass
from apps.users.models import User

URL = "/api/access/"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def park():
    return IndustrialPark.objects.create(name="Parque Norte")


@pytest.fixture
def destination(park):
    return Destination.objects.create(name="Empresa ABC", type="company", park=park)


@pytest.fixture
def guard(park):
    return User.objects.create_user(email="guard@park.com", password="pass1234", role="guard", park=park)


@pytest.fixture
def admin(park):
    return User.objects.create_user(email="admin@park.com", password="pass1234", role="admin", park=park)


@pytest.fixture
def company(park, destination):
    user = User.objects.create_user(email="company@park.com", password="pass1234", role="company", park=park)
    user.destinations.set([destination])
    return user


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_log(destination, guard):
    return AccessLog.objects.create(
        destination=destination,
        guard=guard,
        visitor_name="Juan Pérez",
        entry_time=timezone.now(),
    )


# ── Model ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_access_log_model_exists():
    assert AccessLog is not None


@pytest.mark.django_db
def test_access_log_default_status_is_open(destination, guard):
    log = make_log(destination, guard)
    assert log.status == AccessLog.Status.OPEN


@pytest.mark.django_db
def test_access_log_default_type_is_qr(destination, guard):
    log = make_log(destination, guard)
    assert log.access_type == AccessLog.AccessType.QR


@pytest.mark.django_db
def test_register_exit_updates_status_and_exit_time(destination, guard):
    log = make_log(destination, guard)
    log.register_exit()
    log.refresh_from_db()
    assert log.status == AccessLog.Status.CLOSED
    assert log.exit_time is not None


# ── GET /api/access/ ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_list_guard_returns_200(guard, destination):
    make_log(destination, guard)
    response = auth_client(guard).get(URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_admin_forbidden(admin):
    response = auth_client(admin).get(URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_unauthenticated_returns_401():
    response = APIClient().get(URL)
    assert response.status_code == 401


# ── POST /api/access/create/ ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_create_manual_access_log_returns_201(guard, destination):
    payload = {
        "visitor_name": "Pedro Sánchez",
        "plate": "ABC-123",
        "destination": destination.id,
    }
    response = auth_client(guard).post(f"{URL}create/", payload)
    assert response.status_code == 201
    assert response.data["access_type"] == "manual"


@pytest.mark.django_db
def test_create_manual_requires_visitor_name(guard, destination):
    payload = {"plate": "ABC-123", "destination": destination.id}
    response = auth_client(guard).post(f"{URL}create/", payload)
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_admin_forbidden(admin):
    response = auth_client(admin).post(f"{URL}create/", {})
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_unauthenticated_returns_401():
    response = APIClient().post(f"{URL}create/", {})
    assert response.status_code == 401


# ── GET /api/access/{id}/ ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_retrieve_guard_returns_200(guard, destination):
    log = make_log(destination, guard)
    response = auth_client(guard).get(f"{URL}{log.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_retrieve_admin_forbidden(admin, guard, destination):
    log = make_log(destination, guard)
    response = auth_client(admin).get(f"{URL}{log.id}/")
    assert response.status_code == 403