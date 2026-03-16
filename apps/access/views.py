from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AccessLog, AccessPass


class AccessLogListView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    permission_classes = [IsAuthenticated]


class AccessPassListCreateView(generics.ListCreateAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]

class AccessLogCreateView(generics.CreateAPIView):
    queryset = AccessLog.objects.all()
    permission_classes = [IsAuthenticated]

class AccessPassDetailView(generics.RetrieveAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]

class AccessLogDetailView(generics.RetrieveAPIView):
    queryset = AccessLog.objects.all()
    permission_classes = [IsAuthenticated]