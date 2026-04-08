import pytest
from rest_framework.test import APIClient

from apps.destinations.models import Destination, IndustrialPark
from apps.users.models import User

URL = "/api/users/"


@pytest.fixture
def park():
    return IndustrialPark.objects.create(name="Parque Norte")


@pytest.fixture
def other_park():
    return IndustrialPark.objects.create(name="Parque Sur")


@pytest.fixture
def destination(park):
    return Destination.objects.create(name="Empresa ABC", type="company", park=park)


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


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── GET /users/ ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_list_users_admin_returns_200(admin, guard, tenant):
    response = auth_client(admin).get(URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_users_only_own_park(admin, guard, other_admin):
    response = auth_client(admin).get(URL)
    emails = [u["email"] for u in response.data["results"]]
    assert "guard@park.com" in emails
    assert "admin@other.com" not in emails


@pytest.mark.django_db
def test_list_users_excludes_superusers(admin):
    User.objects.create_superuser(email="super@park.com", password="pass1234")
    response = auth_client(admin).get(URL)
    emails = [u["email"] for u in response.data["results"]]
    assert "super@park.com" not in emails


@pytest.mark.django_db
def test_list_users_filter_by_role(admin, guard, tenant):
    response = auth_client(admin).get(URL, {"role": "guard"})
    assert response.status_code == 200
    assert all(u["role"] == "guard" for u in response.data["results"])


@pytest.mark.django_db
def test_list_users_filter_by_is_active(admin, guard):
    guard.is_active = False
    guard.save()
    response = auth_client(admin).get(URL, {"is_active": "false"})
    emails = [u["email"] for u in response.data["results"]]
    assert "guard@park.com" in emails
    assert "admin@park.com" not in emails


@pytest.mark.django_db
def test_list_users_guard_forbidden(guard):
    response = auth_client(guard).get(URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_users_tenant_forbidden(tenant):
    response = auth_client(tenant).get(URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_users_unauthenticated_returns_401():
    response = APIClient().get(URL)
    assert response.status_code == 401


# ── POST /users/ ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_create_guard_returns_201(admin):
    payload = {"email": "new_guard@park.com", "password": "pass1234", "role": "guard"}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 201
    assert response.data["role"] == "guard"
    assert response.data["email"] == "new_guard@park.com"


@pytest.mark.django_db
def test_create_guard_park_assigned_automatically(admin):
    payload = {"email": "new_guard@park.com", "password": "pass1234", "role": "guard"}
    response = auth_client(admin).post(URL, payload)
    assert response.data["park"]["id"] == admin.park_id


@pytest.mark.django_db
def test_create_tenant_returns_201(admin):
    payload = {"email": "new_tenant@park.com", "password": "pass1234", "role": "tenant"}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 201
    assert response.data["role"] == "tenant"


@pytest.mark.django_db
def test_create_tenant_destinations_ignored_if_sent(admin, destination):
    payload = {
        "email": "new_tenant@park.com",
        "password": "pass1234",
        "role": "tenant",
        "destinations": [destination.id],
    }
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 201
    assert response.data["destinations"] == []


@pytest.mark.django_db
def test_create_admin_role_forbidden(admin):
    payload = {"email": "new_admin@park.com", "password": "pass1234", "role": "admin"}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_user_duplicate_email_returns_400(admin, guard):
    payload = {"email": "guard@park.com", "password": "pass1234", "role": "guard"}
    response = auth_client(admin).post(URL, payload)
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_user_guard_forbidden(guard):
    payload = {"email": "new@park.com", "password": "pass1234", "role": "guard"}
    response = auth_client(guard).post(URL, payload)
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_user_unauthenticated_returns_401():
    payload = {"email": "new@park.com", "password": "pass1234", "role": "guard"}
    response = APIClient().post(URL, payload)
    assert response.status_code == 401


# -- /users/<id>/ -------------------------------------------------------------


@pytest.mark.django_db
def test_user_detail_returns_200_for_same_park_admin(admin, guard):
    response = auth_client(admin).get(f"{URL}{guard.id}/")
    assert response.status_code == 200
    assert response.data["id"] == guard.id


@pytest.mark.django_db
def test_user_detail_forbidden_for_other_park_admin(admin, other_admin):
    response = auth_client(other_admin).get(f"{URL}{admin.id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_user_patch_updates_allowed_fields(admin, guard):
    payload = {"first_name": "Nuevo", "is_active": False, "role": "tenant"}
    response = auth_client(admin).patch(f"{URL}{guard.id}/", payload, format="json")
    assert response.status_code == 200
    assert response.data["first_name"] == "Nuevo"
    assert response.data["is_active"] is False
    assert response.data["role"] == "tenant"


@pytest.mark.django_db
def test_user_patch_rejects_admin_role(admin, guard):
    response = auth_client(admin).patch(f"{URL}{guard.id}/", {"role": "admin"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_user_delete_returns_204(admin, guard):
    response = auth_client(admin).delete(f"{URL}{guard.id}/")
    assert response.status_code == 204
    assert not User.objects.filter(id=guard.id).exists()


@pytest.mark.django_db
def test_user_detail_guard_forbidden(guard, tenant):
    response = auth_client(guard).get(f"{URL}{tenant.id}/")
    assert response.status_code == 403
