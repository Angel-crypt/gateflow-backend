from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.permissions import IsGuard

from .models import AccessLog
from .serializers import AccessLogCreateSerializer, AccessLogSerializer


class AccessLogListView(generics.ListAPIView):
    permission_classes = [IsGuard]
    serializer_class = AccessLogSerializer

    def get_queryset(self):
        return AccessLog.objects.filter(destination__park=self.request.user.park)


class AccessLogCreateView(generics.CreateAPIView):
    permission_classes = [IsGuard]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = AccessLogCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        log = serializer.save()
        return Response(AccessLogSerializer(log, context={"request": request}).data, status=201)


class AccessLogDetailView(generics.RetrieveAPIView):
    permission_classes = [IsGuard]
    serializer_class = AccessLogSerializer

    def get_queryset(self):
        return AccessLog.objects.filter(destination__park=self.request.user.park)
