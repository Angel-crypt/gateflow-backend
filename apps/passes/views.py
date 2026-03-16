# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AccessPass


class AccessPassListCreateView(generics.ListCreateAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]


class AccessPassDetailView(generics.RetrieveAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]