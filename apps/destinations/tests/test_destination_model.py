import pytest

from apps.destinations.models import Destination, IndustrialPark
from apps.users.models import User


@pytest.fixture
def park():
    return IndustrialPark.objects.create(name="Parque Norte")


@pytest.fixture
def user(park):
    return User.objects.create_user(email="company@park.com", password="pass1234", role="tenant", park=park)


@pytest.fixture
def destination(park):
    return Destination.objects.create(name="Empresa ABC", type="company", park=park)


# ── responsible field ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_destination_can_have_responsible(destination, user):
    destination.responsible = user
    destination.save()
    destination.refresh_from_db()
    assert destination.responsible == user


@pytest.mark.django_db
def test_destination_responsible_is_optional(park):
    dest = Destination.objects.create(name="Área Recepción", type="area", park=park)
    assert dest.responsible is None


@pytest.mark.django_db
def test_user_can_be_responsible_for_multiple_destinations(park, user):
    dest1 = Destination.objects.create(name="Empresa A", type="company", park=park, responsible=user)
    dest2 = Destination.objects.create(name="Empresa B", type="company", park=park, responsible=user)
    assert set(user.destinations.all()) == {dest1, dest2}


@pytest.mark.django_db
def test_destination_responsible_reverse_relation(park, user):
    Destination.objects.create(name="Empresa A", type="company", park=park, responsible=user)
    assert user.destinations.count() == 1


@pytest.mark.django_db
def test_destination_responsible_null_on_user_delete(park):
    user = User.objects.create_user(email="temp@park.com", password="pass1234", role="tenant", park=park)
    dest = Destination.objects.create(name="Empresa X", type="company", park=park, responsible=user)
    user.delete()
    dest.refresh_from_db()
    assert dest.responsible is None
