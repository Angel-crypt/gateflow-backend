# Create your tests here.
from django.test import TestCase

from .models import Destination, IndustrialPark


class IndustrialParkModelTest(TestCase):
    def test_industrial_park_model_exists(self):
        self.assertIsNotNone(IndustrialPark)


class DestinationModelTest(TestCase):
    def test_destination_model_exists(self):
        self.assertIsNotNone(Destination)