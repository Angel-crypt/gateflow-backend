# Create your tests here.
from django.test import TestCase

from .models import AccessPass


class AccessPassModelTest(TestCase):
    def test_access_pass_model_exists(self):
        self.assertIsNotNone(AccessPass)