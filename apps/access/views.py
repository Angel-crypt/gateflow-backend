# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AccessLog, AccessPass


class AccessLogListView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    permission_classes = [IsAuthenticated]


class AccessPassListView(generics.ListAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]