from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.models import User

from .models import Destination, IndustrialPark
from .serializers import DestinationSerializer, DestinationWriteSerializer


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)


class IndustrialParkListView(generics.ListAPIView):
    queryset = IndustrialPark.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class DestinationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DestinationWriteSerializer
        return DestinationSerializer

    def get_queryset(self):
        user: User = self.request.user  # type: ignore[assignment]
        if user.role == User.Role.TENANT:
            return Destination.objects.filter(responsible=user).order_by("id")
        return Destination.objects.filter(park=user.park).order_by("id")

    def check_permissions(self, request: Request) -> None:
        super().check_permissions(request)
        if request.method == "POST" and request.user.role != User.Role.ADMIN:  # type: ignore[union-attr]
            self.permission_denied(request)

    def create(self, request, *args, **kwargs):
        serializer = DestinationWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        destination = serializer.save()
        return Response(DestinationSerializer(destination, context={"request": request}).data, status=201)


class DestinationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DestinationWriteSerializer
        return DestinationSerializer

    def get_queryset(self):
        user: User = self.request.user  # type: ignore[assignment]
        if user.role == User.Role.TENANT:
            return Destination.objects.filter(responsible=user).order_by("id")
        return Destination.objects.filter(park=user.park).order_by("id")

    def check_permissions(self, request: Request) -> None:
        super().check_permissions(request)
        if request.method in ("PATCH", "DELETE") and request.user.role != User.Role.ADMIN:  # type: ignore[union-attr]
            self.permission_denied(request)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = DestinationWriteSerializer(instance, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        destination = serializer.save()
        return Response(DestinationSerializer(destination, context={"request": request}).data)
