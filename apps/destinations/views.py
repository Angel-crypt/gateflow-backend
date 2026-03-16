from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Destination, IndustrialPark


class IndustrialParkListView(generics.ListAPIView):
    queryset = IndustrialPark.objects.all()
    permission_classes = [IsAuthenticated]


class DestinationListCreateView(generics.ListCreateAPIView):
    queryset = Destination.objects.all()
    permission_classes = [IsAuthenticated]


class DestinationDetailView(generics.RetrieveAPIView):
    queryset = Destination.objects.all()
    permission_classes = [IsAuthenticated]