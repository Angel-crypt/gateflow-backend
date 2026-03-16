# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model
from destinations.models import Destination
from .models import AccessLog, AccessPass


class AccessLogModelTest(TestCase):
    pass


class AccessPassModelTest(TestCase):
    def test_access_pass_str(self):
        User = get_user_model()

        user = User.objects.create(email="test@test.com")
        destination = Destination.objects.create(name="Test Destination")

        access_pass = AccessPass.objects.create(
            destination=destination,
            created_by=user,
            visitor_name="John Doe",
            valid_from="2024-01-01T10:00:00Z",
            valid_to="2024-01-01T12:00:00Z",
        )

        self.assertIn("John Doe", str(access_pass))


    def test_access_log_model_exists(self):
        self.assertIsNotNone(AccessLog)
        
    def test_access_pass_model_exists(self):
        self.assertIsNotNone(AccessPass)

