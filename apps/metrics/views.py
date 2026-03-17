from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.models import AccessLog
from apps.destinations.models import Destination
from apps.passes.models import AccessPass
from apps.users.models import User
from apps.users.permissions import IsAdmin


class DashboardMetricsView(APIView):
    """
    Resumen general del parque. Solo Admin.

    Retorna un snapshot del estado actual del parque industrial:
    conteo de usuarios por rol, destinos activos/inactivos, estado de
    los pases y un resumen de accesos del día con visitantes aún dentro.
    """

    permission_classes = [IsAdmin]

    def get(self, request: Request) -> Response:
        park = request.user.park  # type: ignore[union-attr]
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        park_id: int = park.id  # type: ignore[union-attr]
        park_name: str = park.name  # type: ignore[union-attr]

        users_qs = User.objects.filter(park=park, is_superuser=False)
        dest_qs = Destination.objects.filter(park=park)
        passes_qs = AccessPass.objects.filter(destination__park=park)
        logs_qs = AccessLog.objects.filter(destination__park=park)

        return Response(
            {
                "park": {"id": park_id, "name": park_name},
                "users": {
                    "total": users_qs.count(),
                    "guards": users_qs.filter(role=User.Role.GUARD).count(),
                    "tenants": users_qs.filter(role=User.Role.TENANT).count(),
                },
                "destinations": {
                    "total": dest_qs.count(),
                    "active": dest_qs.filter(is_active=True).count(),
                    "inactive": dest_qs.filter(is_active=False).count(),
                },
                "passes": {
                    "total": passes_qs.count(),
                    "active": passes_qs.filter(is_active=True, valid_from__lte=now, valid_to__gte=now).count(),
                    "upcoming": passes_qs.filter(is_active=True, valid_from__gt=now).count(),
                    "expired": passes_qs.filter(valid_to__lt=now).count(),
                    "deactivated": passes_qs.filter(is_active=False).count(),
                },
                "access_logs": {
                    "total": logs_qs.count(),
                    "today": logs_qs.filter(entry_time__gte=today_start).count(),
                    "open_now": logs_qs.filter(status=AccessLog.Status.OPEN).count(),
                    "by_type": {
                        "qr": logs_qs.filter(access_type=AccessLog.AccessType.QR).count(),
                        "manual": logs_qs.filter(access_type=AccessLog.AccessType.MANUAL).count(),
                    },
                },
            }
        )


class AccessLogMetricsView(APIView):
    """
    Analíticas de registros de acceso por periodo. Solo Admin.

    Retorna totales, desglose por tipo (QR/manual), por destino y
    evolución diaria para el periodo indicado.

    **Query params:**
    - `period`: `today` | `week` (por defecto) | `month`
    """

    permission_classes = [IsAdmin]

    def get(self, request: Request) -> Response:
        park = request.user.park  # type: ignore[union-attr]
        now = timezone.now()

        period = request.query_params.get("period", "week")
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start = now - timedelta(days=30)
        else:
            period = "week"
            start = now - timedelta(days=7)

        logs_qs = AccessLog.objects.filter(destination__park=park, entry_time__gte=start)

        by_destination = list(
            logs_qs.values("destination__name")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("destination__name", "count")
        )

        by_day = list(
            logs_qs.annotate(date=TruncDate("entry_time"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
            .values_list("date", "count")
        )

        return Response(
            {
                "period": period,
                "total": logs_qs.count(),
                "open_now": AccessLog.objects.filter(destination__park=park, status=AccessLog.Status.OPEN).count(),
                "by_type": {
                    "qr": logs_qs.filter(access_type=AccessLog.AccessType.QR).count(),
                    "manual": logs_qs.filter(access_type=AccessLog.AccessType.MANUAL).count(),
                },
                "by_destination": [{"destination": name, "count": count} for name, count in by_destination],
                "by_day": [{"date": str(date), "count": count} for date, count in by_day],
            }
        )


class PassMetricsView(APIView):
    """
    Analíticas de pases de acceso. Solo Admin.

    Retorna el estado de los pases del parque (activos, próximos,
    expirados, desactivados), desglose por tipo y por destino.
    """

    permission_classes = [IsAdmin]

    def get(self, request: Request) -> Response:
        park = request.user.park  # type: ignore[union-attr]
        now = timezone.now()

        passes_qs = AccessPass.objects.filter(destination__park=park)

        by_destination = list(
            passes_qs.values("destination__name")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("destination__name", "count")
        )

        return Response(
            {
                "total": passes_qs.count(),
                "active": passes_qs.filter(is_active=True, valid_from__lte=now, valid_to__gte=now).count(),
                "upcoming": passes_qs.filter(is_active=True, valid_from__gt=now).count(),
                "expired": passes_qs.filter(valid_to__lt=now).count(),
                "deactivated": passes_qs.filter(is_active=False).count(),
                "by_type": {
                    "day": passes_qs.filter(pass_type=AccessPass.PassType.DAY).count(),
                    "single": passes_qs.filter(pass_type=AccessPass.PassType.SINGLE).count(),
                },
                "by_destination": [{"destination": name, "count": count} for name, count in by_destination],
            }
        )
