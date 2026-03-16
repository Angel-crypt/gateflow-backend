from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.destinations.models import Destination, IndustrialPark
from apps.passes.models import AccessPass
from .models import AccessLog


class AccessLogModelTest(TestCase):
    def test_access_log_model_exists(self):
        self.assertIsNotNone(AccessLog)

    def test_register_exit_updates_status_and_exit_time(self):
        User = get_user_model()

        user = User.objects.create(email="guard@test.com", role="guard")
        park = IndustrialPark.objects.create(name="Test Park")
        destination = Destination.objects.create(
            name="Main Gate",
            type=Destination.Type.AREA,
            park=park,
        )

        access_log = AccessLog.objects.create(
            destination=destination,
            guard=user,
            visitor_name="Jane Doe",
            entry_time=timezone.now(),
        )

        access_log.register_exit()

        self.assertIsNotNone(access_log.exit_time)
        self.assertEqual(access_log.status, "closed")


class AccessPassModelTest(TestCase):
    def test_access_pass_str(self):
        User = get_user_model()

        user = User.objects.create(email="test@test.com", role="admin")
        park = IndustrialPark.objects.create(name="Test Park")
        destination = Destination.objects.create(
            name="Test Destination",
            type=Destination.Type.COMPANY,
            park=park,
        )

        access_pass = AccessPass.objects.create(
            destination=destination,
            created_by=user,
            visitor_name="John Doe",
            valid_from=timezone.now(),
            valid_to=timezone.now(),
        )

        self.assertIn("John Doe", str(access_pass))