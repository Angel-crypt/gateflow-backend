import pytest
from rest_framework.test import APIClient

from apps.destinations.models import Destination, IndustrialPark
from apps.users.models import User

URL = "/api/destinations/"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def park():
    return IndustrialPark.objects.create(name="Parque Norte")


@pytest.fixture
def other_park():
    return IndustrialPark.objects.create(name="Parque Sur")


@pytest.fixture
def admin(park):
    return User.objects.create_user(email="admin@park.com", password="pass1234", role="admin", park=park)


@pytest.fixture
def guard(park):
    return User.objects.create_user(email="guard@park.com", password="pass1234", role="guard", park=park)


@pytest.fixture
def tenant(park):
    return User.objects.create_user(email="tenant@park.com", password="pass1234", role="tenant", park=park)


@pytest.fixture
def other_admin(other_park):
    return User.objects.create_user(email="admin@other.com", password="pass1234", role="admin", park=other_park)


@pytest.fixture
def destination(park, tenant):
    dest = Destination.objects.create(name="Empresa ABC", type="company", park=park)
    dest.responsible = tenant
    dest.save()
    return dest


@pytest.fixture
def other_destination(park):
    return Destination.objects.create(name="Área Recepción", type="area", park=park)


@pytest.fixture
def foreign_destination(other_park):
    return Destination.objects.create(name="Empresa XYZ", type="company", park=other_park)


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── GET /api/destinations/ ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_list_admin_sees_all_park_destinations(admin, destination, other_destination):
    response = auth_client(admin).get(URL)
    assert response.status_code == 200
    names = [d["name"] for d in response.data["results"]]
    assert "Empresa ABC" in names
    assert "Área Recepción" in names


@pytest.mark.django_db
def test_list_admin_does_not_see_other_park(admin, destination, foreign_destination):
    response = auth_client(admin).get(URL)
    names = [d["name"] for d in response.data["results"]]
    assert "Empresa XYZ" not in names


@pytest.mark.django_db
def test_list_guard_sees_all_park_destinations(guard, destination, other_destination):
    response = auth_client(guard).get(URL)
    assert response.status_code == 200
    names = [d["name"] for d in response.data["results"]]
    assert "Empresa ABC" in names
    assert "Área Recepción" in names


@pytest.mark.django_db
def test_list_tenant_sees_only_own_destinations(tenant, destination, other_destination):
    response = auth_client(tenant).get(URL)
    assert response.status_code == 200
    names = [d["name"] for d in response.data["results"]]
    assert "Empresa ABC" in names
    assert "Área Recepción" not in names


@pytest.mark.django_db
def test_list_unauthenticated_returns_401(destination):
    response = APIClient().get(URL)
    assert response.status_code == 401


# ── POST /api/destinations/ ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_create_admin_returns_201(admin):
    payload = {"name": "Nueva Empresa", "type": "company"}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 201
    assert response.data["name"] == "Nueva Empresa"


@pytest.mark.django_db
def test_create_park_assigned_automatically(admin):
    payload = {"name": "Nueva Empresa", "type": "company"}
    response = auth_client(admin).post(URL, payload)
    assert response.data["park"]["id"] == admin.park_id


@pytest.mark.django_db
def test_create_with_responsible(admin, tenant):
    payload = {"name": "Nueva Empresa", "type": "company", "responsible": tenant.id}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 201
    assert response.data["responsible"]["id"] == tenant.id


@pytest.mark.django_db
def test_create_responsible_from_other_park_returns_400(admin, other_park):
    other_tenant = User.objects.create_user(
        email="other@tenant.com", password="pass1234", role="tenant", park=other_park
    )
    payload = {"name": "Nueva Empresa", "type": "company", "responsible": other_tenant.id}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_guard_forbidden(guard):
    response = auth_client(guard).post(URL, {"name": "X", "type": "company"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_tenant_forbidden(tenant):
    response = auth_client(tenant).post(URL, {"name": "X", "type": "company"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_unauthenticated_returns_401():
    response = APIClient().post(URL, {"name": "X", "type": "company"})
    assert response.status_code == 401


# ── GET /api/destinations/{id}/ ───────────────────────────────────────────────


@pytest.mark.django_db
def test_retrieve_admin_returns_200(admin, destination):
    response = auth_client(admin).get(f"{URL}{destination.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_retrieve_guard_returns_200(guard, destination):
    response = auth_client(guard).get(f"{URL}{destination.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_retrieve_tenant_own_destination_returns_200(tenant, destination):
    response = auth_client(tenant).get(f"{URL}{destination.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_retrieve_tenant_other_destination_returns_404(tenant, other_destination):
    response = auth_client(tenant).get(f"{URL}{other_destination.id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_retrieve_unauthenticated_returns_401(destination):
    response = APIClient().get(f"{URL}{destination.id}/")
    assert response.status_code == 401


# ── PATCH /api/destinations/{id}/ ────────────────────────────────────────────


@pytest.mark.django_db
def test_update_admin_returns_200(admin, destination):
    response = auth_client(admin).patch(f"{URL}{destination.id}/", {"name": "Nuevo Nombre"})
    assert response.status_code == 200
    assert response.data["name"] == "Nuevo Nombre"


@pytest.mark.django_db
def test_update_guard_forbidden(guard, destination):
    response = auth_client(guard).patch(f"{URL}{destination.id}/", {"name": "X"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_update_tenant_forbidden(tenant, destination):
    response = auth_client(tenant).patch(f"{URL}{destination.id}/", {"name": "X"})
    assert response.status_code == 403


# ── DELETE /api/destinations/{id}/ ───────────────────────────────────────────


@pytest.mark.django_db
def test_delete_admin_returns_204(admin, destination):
    response = auth_client(admin).delete(f"{URL}{destination.id}/")
    assert response.status_code == 204
    assert not Destination.objects.filter(id=destination.id).exists()


@pytest.mark.django_db
def test_delete_guard_forbidden(guard, destination):
    response = auth_client(guard).delete(f"{URL}{destination.id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_tenant_forbidden(tenant, destination):
    response = auth_client(tenant).delete(f"{URL}{destination.id}/")
    assert response.status_code == 403
