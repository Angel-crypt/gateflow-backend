from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.permissions import IsAdminOrTenant

from .models import AccessPass
from .serializers import AccessPassSerializer, AccessPassWriteSerializer


class AccessPassListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrTenant]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AccessPassWriteSerializer
        return AccessPassSerializer

    def get_queryset(self):
        user: User = self.request.user  # type: ignore[assignment]
        if user.role == User.Role.TENANT:
            return AccessPass.objects.filter(destination__responsible=user)
        return AccessPass.objects.filter(destination__park=user.park)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = AccessPassWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        access_pass = serializer.save()
        return Response(AccessPassSerializer(access_pass, context={"request": request}).data, status=201)


class AccessPassDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrTenant]
    http_method_names = ["get", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AccessPassWriteSerializer
        return AccessPassSerializer

    def get_queryset(self):
        user: User = self.request.user  # type: ignore[assignment]
        if user.role == User.Role.TENANT:
            return AccessPass.objects.filter(destination__responsible=user)
        return AccessPass.objects.filter(destination__park=user.park)

    def update(self, request: Request, *args, **kwargs) -> Response:
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = AccessPassWriteSerializer(instance, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        access_pass = serializer.save()
        return Response(AccessPassSerializer(access_pass, context={"request": request}).data)


class AccessPassValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        pass_id = request.data.get("pass_id")
        if not pass_id:
            return Response({"detail": "El campo pass_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_pass = AccessPass.objects.get(id=int(pass_id))
        except AccessPass.DoesNotExist:
            return Response({"detail": "Pase no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if not access_pass.is_valid():
            return Response(
                {"detail": "El pase no es válido o ha expirado.", "is_valid": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"is_valid": True, **AccessPassSerializer(access_pass, context={"request": request}).data})
