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
    """
    Listar y crear pases de acceso. Solo Admin y Tenant.

    **GET** — El Admin ve todos los pases de su parque. El Tenant ve únicamente
    los pases correspondientes a los destinos de los que es responsable.

    **POST** — Crea un nuevo pase de acceso para un visitante. El campo `destination`
    es opcional si el usuario tiene un único destino disponible; en ese caso se asigna
    automáticamente. Si tiene varios, debe seleccionarlo explícitamente.
    El `id` retornado en la respuesta es el valor que el frontend debe usar para
    generar el código QR.

    Campos requeridos: `visitor_name`, `plate`, `valid_from`, `valid_to`.
    """

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
    """
    Detalle, editar y eliminar un pase de acceso. Solo Admin y Tenant.

    **GET** — Retorna el detalle del pase. El Tenant solo accede a pases de sus destinos.

    **PATCH** — Permite modificar parcialmente un pase: extender `valid_to`,
    cambiar `plate`, o desactivarlo con `is_active: false`.

    **DELETE** — Elimina permanentemente el pase.
    """

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
    """
    Validar un pase de acceso por ID. Cualquier usuario autenticado.

    Usado por el guardia al escanear un código QR. Recibe el `pass_id` y retorna
    los datos completos del pase si es válido (activo y dentro del rango de fechas).

    Retorna 400 si el pase está inactivo o fuera del rango de validez.
    Retorna 404 si el pase no existe.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        from django.utils import timezone

        pass_id = request.data.get("pass_id")
        if not pass_id:
            return Response({"detail": "El campo pass_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_pass = AccessPass.objects.get(id=int(pass_id))
        except (AccessPass.DoesNotExist, ValueError):
            return Response(
                {"detail": "Pase no encontrado.", "error_code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()

        if access_pass.is_used:
            return Response(
                {"detail": "Este pase de uso único ya fue utilizado.", "error_code": "already_used", "is_valid": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not access_pass.is_active:
            return Response(
                {"detail": "El pase está desactivado.", "error_code": "inactive", "is_valid": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if now < access_pass.valid_from:
            valid_from_str = access_pass.valid_from.strftime("%d/%m/%Y %H:%M")
            return Response(
                {
                    "detail": f"El pase aún no es válido. Será válido a partir del {valid_from_str}.",
                    "error_code": "not_yet_valid",
                    "is_valid": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if now > access_pass.valid_to:
            valid_to_str = access_pass.valid_to.strftime("%d/%m/%Y %H:%M")
            return Response(
                {
                    "detail": f"El pase expiró el {valid_to_str}.",
                    "error_code": "expired",
                    "is_valid": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"is_valid": True, **AccessPassSerializer(access_pass, context={"request": request}).data})
