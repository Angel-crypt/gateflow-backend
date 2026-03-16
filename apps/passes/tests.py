# Create your tests here.
from django.test import TestCase

from .models import AccessPass


class TestAccessPassModel(TestCase):
    def test_access_pass_model_exists(self):
        self.assertIsNotNone(AccessPass)

    def test_is_valid_method_exists(self):
        self.assertTrue(hasattr(AccessPass, "is_valid"))

    def test_can_create_access_pass_instance(self):
        access_pass = AccessPass()
        self.assertIsInstance(access_pass, AccessPass)
