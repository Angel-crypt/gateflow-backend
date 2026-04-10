import csv

from django.http import FileResponse, StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.passes.models import AccessPass
from apps.users.models import User
from apps.users.permissions import IsAdmin, IsAdminOrGuard, IsGuard

from .filters import AccessLogFilter
from .models import AccessLog
from .pdf import build_access_logs_pdf
from .serializers import AccessLogCreateSerializer, AccessLogSerializer


class AccessLogListView(generics.ListAPIView):
    """
    Listar registros de acceso del parque. Guard y Admin.

    Retorna todos los registros de entrada/salida correspondientes
    al parque industrial del usuario autenticado, ordenados por `entry_time` descendente.

    **Filtros disponibles:** `access_type`, `status`, `destination`, `date_from`, `date_to`
    """

    permission_classes = [IsAdminOrGuard]
    serializer_class = AccessLogSerializer
    filterset_class = AccessLogFilter
    ordering_fields = ["entry_time", "status", "access_type"]
    ordering = ["-entry_time"]

    def get_queryset(self):
        qs = AccessLog.objects.select_related(
            "access_pass", "destination", "guard"
        ).filter(destination__park=self.request.user.park)
        access_pass = self.request.query_params.get("access_pass")
        if access_pass:
            qs = qs.filter(access_pass_id=access_pass)

        search = self.request.query_params.get("search")
        if search:
            try:
                pass_id = int(search)
                qs_by_pass = qs.filter(access_pass_id=pass_id)
                if qs_by_pass.exists():
                    qs = qs_by_pass
                else:
                    pass_obj = AccessPass.objects.filter(id=pass_id).first()
                    if pass_obj:
                        qs = qs.filter(visitor_name=pass_obj.visitor_name, plate=pass_obj.plate)
            except ValueError:
                qs = qs.filter(visitor_name__icontains=search) | qs.filter(plate__icontains=search)

        return qs.order_by("-entry_time")


class AccessLogDetailView(generics.RetrieveAPIView):
    """
    Detalle de un registro de acceso. Guard y Admin.

    Retorna los datos completos del registro incluyendo `access_pass`, `destination`, `guard`,
    tiempos y estado.
    """

    permission_classes = [IsAdminOrGuard]
    serializer_class = AccessLogSerializer
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return AccessLog.objects.select_related(
            "access_pass", "destination", "guard"
        ).filter(destination__park=self.request.user.park)  # type: ignore[union-attr]


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
    serializer_class = AccessLogCreateSerializer

    def get_queryset(self):
        assert isinstance(self.request.user, User)
        return AccessLog.objects.filter(destination__park=self.request.user.park)  # type: ignore[union-attr]


class RegisterExitView(APIView):
    """
    Registrar salida de un acceso abierto. Solo Guard.

    Recibe el `pk` del AccessLog, valida que pertenezca al parque del guardia
    y que esté en estado `open`, luego registra `exit_time` y cambia el estado a `closed`.

    Retorna 400 si el acceso ya fue cerrado.
    Retorna 404 si el registro no existe o no pertenece al parque.
    """

    permission_classes = [IsGuard]

    def post(self, request: Request, pk: int) -> Response:
        assert isinstance(request.user, User)
        try:
            log = AccessLog.objects.get(pk=pk, destination__park=request.user.park)  # type: ignore[union-attr]
        except AccessLog.DoesNotExist:
            return Response({"detail": "Registro no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if log.status == AccessLog.Status.CLOSED:
            return Response({"detail": "El acceso ya fue cerrado."}, status=status.HTTP_400_BAD_REQUEST)

        log.register_exit()
        return Response(AccessLogSerializer(log, context={"request": request}).data)


class AccessLogExportCSVView(APIView):
    """
    Exportar registros de acceso en formato CSV. Solo Admin y Guard.

    Retorna todos los registros del parque del usuario autenticado.

    **Filtros disponibles:** `access_type`, `status`, `destination`, `date_from`, `date_to`
    """

    permission_classes = [IsAdminOrGuard]

    def get(self, request: Request) -> StreamingHttpResponse:
        qs = AccessLog.objects.select_related(
            "access_pass", "destination", "guard"
        ).filter(destination__park=request.user.park)  # type: ignore[union-attr]

        filterset = AccessLogFilter(request.query_params, queryset=qs)
        qs = filterset.qs

        def rows():
            yield ["ID", "Visitante", "Placa", "Destino", "Tipo", "Guardia", "Entrada", "Salida", "Estado"]
            for log in qs.iterator():
                guard_name = ""
                if log.guard:
                    guard_name = f"{log.guard.first_name} {log.guard.last_name}".strip() or log.guard.email
                yield [
                    log.id,
                    log.visitor_name,
                    log.plate,
                    log.destination.name,
                    log.get_access_type_display(),
                    guard_name,
                    log.entry_time.strftime("%d/%m/%Y %H:%M"),
                    log.exit_time.strftime("%d/%m/%Y %H:%M") if log.exit_time else "",
                    log.get_status_display(),
                ]

        class Echo:
            def write(self, value):
                return value

        writer = csv.writer(Echo())
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in rows()),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="accesos.csv"'
        return response


class AccessLogExportPDFView(APIView):
    """
    Exportar registros de acceso en formato PDF. Solo Admin.

    Retorna un reporte PDF con todos los registros del parque, incluyendo
    una tabla de datos y un resumen por tipo y estado.

    **Filtros disponibles:** `access_type`, `status`, `destination`, `date_from`, `date_to`
    """

    permission_classes = [IsAdmin]

    def get(self, request: Request) -> FileResponse:
        park = request.user.park  # type: ignore[union-attr]

        qs = AccessLog.objects.select_related(
            "access_pass", "destination", "guard"
        ).filter(destination__park=park)

        filterset = AccessLogFilter(request.query_params, queryset=qs)
        qs = filterset.qs.order_by("entry_time")

        buffer = build_access_logs_pdf(qs, park.name)
        return FileResponse(buffer, as_attachment=True, filename="accesos.pdf")
