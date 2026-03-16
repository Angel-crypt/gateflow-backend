# Create your tests here.
from django.test import TestCase

from .models import AccessLog, AccessPass


class AccessLogModelTest(TestCase):
    pass


class AccessPassModelTest(TestCase):
    pass

    def test_access_pass_model_exists(self):
        self.assertIsNotNone(AccessPass)