from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.models import User
from apps.users.permissions import IsAdmin, IsGuard

from .models import AccessLog
from .serializers import AccessLogCreateSerializer, AccessLogSerializer


class AccessLogListView(generics.ListAPIView):
    """
    Listar registros de acceso del parque. Guard y Admin.

    Retorna todos los registros de entrada/salida correspondientes
    al parque industrial del usuario autenticado, ordenados por `entry_time` descendente.
    """

    serializer_class = AccessLogSerializer

    def get_permissions(self):
        return [IsGuard() if self.request.user.role == User.Role.GUARD else IsAdmin()]

    def get_queryset(self):
        return AccessLog.objects.filter(destination__park=self.request.user.park)


class AccessLogCreateView(generics.CreateAPIView):
    """
    Registrar un acceso. Solo Guard.

    Soporta dos flujos según si se provee `access_pass` o no:

    **Flujo QR** (`access_pass` presente) — El guardia escanea el código QR y obtiene
    el ID del pase. Al enviar solo `access_pass`, el sistema valida que el pase sea
    vigente y pertenezca al parque, luego transcribe automáticamente `visitor_name`,
    `plate` y `destination` desde el pase. El campo `access_type` se establece en `qr`.

    **Flujo Manual** (`access_pass` ausente) — El guardia ingresa manualmente
    `visitor_name`, `plate` y `destination`. El `access_type` se establece en `manual`.

    En ambos casos, el `guard` se toma del perfil del usuario autenticado y
    `entry_time` se asigna automáticamente al momento de la petición si no se provee.
    """

    permission_classes = [IsGuard]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = AccessLogCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        log = serializer.save()
        return Response(AccessLogSerializer(log, context={"request": request}).data, status=201)


class AccessLogDetailView(generics.RetrieveAPIView):
    """
    Detalle de un registro de acceso. Guard y Admin.

    Retorna el registro completo con datos del pase asociado (si aplica),
    destino, guardia que registró, tiempos de entrada/salida y estado.
    Solo accede a registros del parque del usuario autenticado.
    """

    serializer_class = AccessLogSerializer

    def get_permissions(self):
        return [IsGuard() if self.request.user.role == User.Role.GUARD else IsAdmin()]

    def get_queryset(self):
        return AccessLog.objects.filter(destination__park=self.request.user.park)
