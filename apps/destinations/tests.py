# Create your tests here.
from django.test import TestCase

from .models import Destination, IndustrialPark


class TestIndustrialParkModel(TestCase):
    def test_industrial_park_model_exists(self):
        self.assertIsNotNone(IndustrialPark)

    def test_can_create_industrial_park_instance(self):
        park = IndustrialPark(name="Test Park")
        self.assertIsInstance(park, IndustrialPark)


class TestDestinationModel(TestCase):
    def test_destination_model_exists(self):
        self.assertIsNotNone(Destination)

    def test_can_create_destination_instance(self):
        destination = Destination(name="Test Destination")
        self.assertIsInstance(destination, Destination)