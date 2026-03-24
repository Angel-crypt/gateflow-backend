"""
Management command: seed
========================
Carga datos iniciales (seed) en la base de datos.

Funciona en cualquier entorno (dev, staging, prod) — los datos
se identifican por email/nombre para ser idempotentes:
ejecutar el comando dos veces no duplica registros.

Uso:
    python manage.py seed                  # carga todo
    python manage.py seed --flush          # borra datos previos y recarga
    python manage.py seed --only users     # solo usuarios
    python manage.py seed --only passes    # solo pases
    python manage.py seed --only logs      # solo registros de acceso

Advertencia --flush en producción:
    El flag --flush elimina TODOS los registros de las tablas
    controladas por este seed. Usar con cuidado en prod.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.access.models import AccessLog
from apps.destinations.models import Destination, IndustrialPark
from apps.passes.models import AccessPass
from apps.users.models import User

# ── Credenciales por defecto (override vía --password) ────────────────────────
DEFAULT_ADMIN_PASSWORD = "Bajio2026!"
DEFAULT_GUARD_PASSWORD = "Seguridad6!"
DEFAULT_TENANT_PASSWORD = "Parque2026!"

# ── Datos estáticos del seed ───────────────────────────────────────────────────

PARK = {
    "name": "Parque Industrial Bajío",
    "address": "Carr. Silao–León Km 4.5, Silao de la Victoria, Gto.",
}

ADMIN = {
    "email": "admin@gateflow.mx",
    "first_name": "Carlos",
    "last_name": "Mendoza",
    "role": User.Role.ADMIN,
}

DESTINATIONS = [
    {"name": "Aceros del Norte S.A. de C.V.", "type": Destination.Type.COMPANY},
    {"name": "TechParts México", "type": Destination.Type.COMPANY},
    {"name": "Almacén Central", "type": Destination.Type.AREA},
    {"name": "Patio de Maniobras", "type": Destination.Type.AREA},
    {"name": "Zona de Carga A", "type": Destination.Type.AREA},
    {"name": "Zona de Carga B", "type": Destination.Type.AREA},
]

GUARDS = [
    {"email": "guardia1@gateflow.mx", "first_name": "Luis", "last_name": "Torres"},
    {"email": "guardia2@gateflow.mx", "first_name": "Ana", "last_name": "Ramírez"},
]

TENANTS = [
    {"email": "inquilino1@acerosnorte.mx", "first_name": "Roberto", "last_name": "Sánchez"},
    {"email": "inquilino2@techparts.mx", "first_name": "Valeria", "last_name": "Cruz"},
]

# ── Pass / log templates (relativos a timezone.now()) ────────────────────────
#
# Las fechas se calculan dinámicamente en _seed_passes() y _seed_logs()
# para que siempre sean válidas respecto al momento de ejecución.

NOW: datetime = None  # type: ignore[assignment]  # se asigna en handle()


class Command(BaseCommand):
    help = "Carga datos seed en la base de datos (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Elimina registros seed previos antes de recargar.",
        )
        parser.add_argument(
            "--only",
            choices=["users", "passes", "logs"],
            help="Ejecuta solo una sección del seed.",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Contraseña para todos los usuarios creados (sobreescribe los defaults).",
        )

    # ── Entry point ───────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        global NOW
        NOW = timezone.now()

        self.stdout.write(self.style.MIGRATE_HEADING("\n── GateFlow Seed ────────────────────────────────"))

        only = options["only"]
        flush = options["flush"]
        pwd_override = options.get("password")

        admin_pwd = pwd_override or DEFAULT_ADMIN_PASSWORD
        guard_pwd = pwd_override or DEFAULT_GUARD_PASSWORD
        tenant_pwd = pwd_override or DEFAULT_TENANT_PASSWORD

        try:
            with transaction.atomic():
                if flush:
                    self._flush()

                # Siempre se crean parque + destinos (son la base de todo)
                park = self._seed_park()
                destinations = self._seed_destinations(park)
                guard_user = self._get_or_create_guard(park, guard_pwd)

                if only is None or only == "users":
                    self._seed_users(park, admin_pwd, guard_pwd, tenant_pwd)

                if only is None or only == "passes":
                    creator = User.objects.filter(park=park, role=User.Role.ADMIN).first()
                    if not creator:
                        raise CommandError("No hay admin en el parque. Ejecuta primero sin --only.")
                    self._seed_passes(destinations, creator)

                if only is None or only == "logs":
                    passes = AccessPass.objects.filter(destination__park=park)
                    if not passes.exists():
                        raise CommandError("No hay pases en el parque. Ejecuta primero sin --only.")
                    self._seed_logs(destinations, guard_user, passes)

        except CommandError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(self.style.ERROR(f"\nError inesperado: {exc}"))
            raise

        self.stdout.write(self.style.SUCCESS("\n✓ Seed completado.\n"))

    # ── Flush ─────────────────────────────────────────────────────────────────

    def _flush(self):
        self.stdout.write(self.style.WARNING("  [flush] Eliminando datos seed previos…"))
        AccessLog.objects.filter(destination__park__name=PARK["name"]).delete()
        AccessPass.objects.filter(destination__park__name=PARK["name"]).delete()
        User.objects.filter(park__name=PARK["name"]).delete()
        Destination.objects.filter(park__name=PARK["name"]).delete()
        IndustrialPark.objects.filter(name=PARK["name"]).delete()
        self.stdout.write(self.style.WARNING("  [flush] Listo.\n"))

    # ── Park ──────────────────────────────────────────────────────────────────

    def _seed_park(self) -> IndustrialPark:
        park, created = IndustrialPark.objects.get_or_create(
            name=PARK["name"],
            defaults={"address": PARK["address"], "is_active": True},
        )
        self._log("Parque", park.name, created)
        return park

    # ── Destinations ──────────────────────────────────────────────────────────

    def _seed_destinations(self, park: IndustrialPark) -> list[Destination]:
        result = []
        for d in DESTINATIONS:
            dest, created = Destination.objects.get_or_create(
                name=d["name"],
                park=park,
                defaults={"type": d["type"], "is_active": True},
            )
            self._log("Destino", dest.name, created)
            result.append(dest)

        # Asignar responsables a destinos
        tenants = list(User.objects.filter(role=User.Role.TENANT, park=park))
        if tenants and len(tenants) >= 2:
            # Tenant 1 -> múltiples destinos (Aceros + Almacén + Zona A)
            result[0].responsible = tenants[0]
            result[0].save()
            result[2].responsible = tenants[0]
            result[2].save()
            result[4].responsible = tenants[0]
            result[4].save()
            # Tenant 2 -> múltiples destinos (TechParts + Patio + Zona B)
            result[1].responsible = tenants[1]
            result[1].save()
            result[3].responsible = tenants[1]
            result[3].save()
            result[5].responsible = tenants[1]
            result[5].save()

        return result

    # ── Users ─────────────────────────────────────────────────────────────────

    def _get_or_create_guard(self, park: IndustrialPark, password: str) -> User:
        """Garantiza que al menos un guardia exista para crear logs."""
        guard_data = GUARDS[0]
        guard, created = User.objects.get_or_create(
            email=guard_data["email"],
            defaults={
                "first_name": guard_data["first_name"],
                "last_name": guard_data["last_name"],
                "role": User.Role.GUARD,
                "park": park,
                "password": make_password(password),
                "username": guard_data["email"],
            },
        )
        return guard

    def _seed_users(self, park: IndustrialPark, admin_pwd, guard_pwd, tenant_pwd):
        self.stdout.write("\n  Usuarios:")

        # Admin
        admin, created = User.objects.get_or_create(
            email=ADMIN["email"],
            defaults={
                "first_name": ADMIN["first_name"],
                "last_name": ADMIN["last_name"],
                "role": User.Role.ADMIN,
                "park": park,
                "password": make_password(admin_pwd),
                "username": ADMIN["email"],
                "is_staff": True,
            },
        )
        self._log("Admin", admin.email, created, indent=4)
        if created:
            self.stdout.write(self.style.WARNING(f"      → credenciales: {ADMIN['email']} / {admin_pwd}"))

        # Guards
        for g in GUARDS:
            user, created = User.objects.get_or_create(
                email=g["email"],
                defaults={
                    "first_name": g["first_name"],
                    "last_name": g["last_name"],
                    "role": User.Role.GUARD,
                    "park": park,
                    "password": make_password(guard_pwd),
                    "username": g["email"],
                },
            )
            self._log("Guardia", user.email, created, indent=4)
            if created:
                self.stdout.write(self.style.WARNING(f"      → credenciales: {g['email']} / {guard_pwd}"))

        # Tenants
        for t in TENANTS:
            user, created = User.objects.get_or_create(
                email=t["email"],
                defaults={
                    "first_name": t["first_name"],
                    "last_name": t["last_name"],
                    "role": User.Role.TENANT,
                    "park": park,
                    "password": make_password(tenant_pwd),
                    "username": t["email"],
                },
            )
            self._log("Inquilino", user.email, created, indent=4)
            if created:
                self.stdout.write(self.style.WARNING(f"      → credenciales: {t['email']} / {tenant_pwd}"))

    # ── Passes ───────────────────────────────────────────────────────────────

    def _seed_passes(self, destinations: list[Destination], creator: User):
        self.stdout.write("\n  Pases de acceso:")
        dest0, dest1, dest2 = destinations[0], destinations[1], destinations[2]

        passes_data = [
            # Pases activos (vigentes ahora)
            {
                "visitor_name": "Juan Pérez",
                "plate": "ABC-123",
                "destination": dest0,
                "pass_type": AccessPass.PassType.DAY,
                "valid_from": NOW - timedelta(hours=2),
                "valid_to": NOW + timedelta(hours=22),
                "is_active": True,
            },
            {
                "visitor_name": "María López",
                "plate": "XYZ-456",
                "destination": dest1,
                "pass_type": AccessPass.PassType.DAY,
                "valid_from": NOW - timedelta(hours=1),
                "valid_to": NOW + timedelta(hours=7),
                "is_active": True,
            },
            {
                "visitor_name": "Pedro Ruiz",
                "plate": "LMN-789",
                "destination": dest2,
                "pass_type": AccessPass.PassType.SINGLE,
                "valid_from": NOW - timedelta(minutes=30),
                "valid_to": NOW + timedelta(hours=4),
                "is_active": True,
            },
            # Pase próximo (futuro)
            {
                "visitor_name": "Sofía Herrera",
                "plate": "QRS-321",
                "destination": dest0,
                "pass_type": AccessPass.PassType.DAY,
                "valid_from": NOW + timedelta(days=1),
                "valid_to": NOW + timedelta(days=1, hours=8),
                "is_active": True,
            },
            # Pase expirado
            {
                "visitor_name": "Diego Morales",
                "plate": "TUV-654",
                "destination": dest1,
                "pass_type": AccessPass.PassType.DAY,
                "valid_from": NOW - timedelta(days=3),
                "valid_to": NOW - timedelta(days=2),
                "is_active": True,
            },
            # Pase desactivado
            {
                "visitor_name": "Elena Castro",
                "plate": "WXY-987",
                "destination": dest2,
                "pass_type": AccessPass.PassType.SINGLE,
                "valid_from": NOW - timedelta(hours=5),
                "valid_to": NOW + timedelta(hours=3),
                "is_active": False,
            },
        ]

        for p in passes_data:
            obj, created = AccessPass.objects.get_or_create(
                visitor_name=p["visitor_name"],
                plate=p["plate"],
                destination=p["destination"],
                defaults={
                    "created_by": creator,
                    "pass_type": p["pass_type"],
                    "valid_from": p["valid_from"],
                    "valid_to": p["valid_to"],
                    "is_active": p["is_active"],
                },
            )
            self._log("Pase", f"{obj.visitor_name} / {obj.plate}", created, indent=4)

    # ── Access logs ───────────────────────────────────────────────────────────

    def _seed_logs(self, destinations: list[Destination], guard: User, passes):
        self.stdout.write("\n  Registros de acceso:")
        dest0, dest1, dest2, dest3 = destinations[0], destinations[1], destinations[2], destinations[3]

        logs_data = [
            # ── Activos recientes (< 24h) ──────────────────────────────────
            {
                "visitor_name": "Juan Pérez",
                "plate": "ABC-123",
                "destination": dest0,
                "access_type": AccessLog.AccessType.QR,
                "entry_time": NOW - timedelta(hours=2),
                "status": AccessLog.Status.OPEN,
            },
            {
                "visitor_name": "María López",
                "plate": "XYZ-456",
                "destination": dest1,
                "access_type": AccessLog.AccessType.QR,
                "entry_time": NOW - timedelta(hours=1, minutes=15),
                "status": AccessLog.Status.OPEN,
            },
            {
                "visitor_name": "Camión Reparto Bodega",
                "plate": "DEF-001",
                "destination": dest2,
                "access_type": AccessLog.AccessType.MANUAL,
                "entry_time": NOW - timedelta(hours=3),
                "status": AccessLog.Status.OPEN,
            },
            # ── ALERTAS: activos con más de 24h dentro del parque ─────────
            # Estos registros son los que deben mostrarse con alerta naranja
            # en el frontend (AccesosPage).
            {
                "visitor_name": "Proveedor Metales Pesados",
                "plate": "GHI-200",
                "destination": dest0,
                "access_type": AccessLog.AccessType.MANUAL,
                "entry_time": NOW - timedelta(hours=26),  # 26h dentro
                "status": AccessLog.Status.OPEN,
            },
            {
                "visitor_name": "Mantenimiento Externo",
                "plate": "JKL-300",
                "destination": dest3,
                "access_type": AccessLog.AccessType.MANUAL,
                "entry_time": NOW - timedelta(hours=30),  # 30h dentro
                "status": AccessLog.Status.OPEN,
            },
            {
                "visitor_name": "Trailer Carga Pesada",
                "plate": "MNO-400",
                "destination": dest2,
                "access_type": AccessLog.AccessType.MANUAL,
                "entry_time": NOW - timedelta(days=2, hours=3),  # >48h
                "status": AccessLog.Status.OPEN,
            },
            # ── Cerrados recientes ─────────────────────────────────────────
            {
                "visitor_name": "Pedro Ruiz",
                "plate": "LMN-789",
                "destination": dest2,
                "access_type": AccessLog.AccessType.QR,
                "entry_time": NOW - timedelta(hours=5),
                "exit_time": NOW - timedelta(hours=1),
                "status": AccessLog.Status.CLOSED,
            },
            {
                "visitor_name": "Carlos Visita",
                "plate": "PQR-500",
                "destination": dest1,
                "access_type": AccessLog.AccessType.MANUAL,
                "entry_time": NOW - timedelta(hours=8),
                "exit_time": NOW - timedelta(hours=4),
                "status": AccessLog.Status.CLOSED,
            },
            # ── Cerrados de días anteriores ────────────────────────────────
            {
                "visitor_name": "Auditoría IMSS",
                "plate": "STU-600",
                "destination": dest0,
                "access_type": AccessLog.AccessType.MANUAL,
                "entry_time": NOW - timedelta(days=2, hours=4),
                "exit_time": NOW - timedelta(days=2, hours=1),
                "status": AccessLog.Status.CLOSED,
            },
            {
                "visitor_name": "Proveedor TechParts",
                "plate": "VWX-700",
                "destination": dest1,
                "access_type": AccessLog.AccessType.QR,
                "entry_time": NOW - timedelta(days=3, hours=6),
                "exit_time": NOW - timedelta(days=3, hours=2),
                "status": AccessLog.Status.CLOSED,
            },
        ]

        for log in logs_data:
            # Buscar por visitor_name y plate para evitar duplicados
            existing = AccessLog.objects.filter(
                visitor_name=log["visitor_name"],
                plate=log["plate"],
            ).first()

            if existing:
                # Actualizar si ya existe (para mantener idempotencia con timestamps diferentes)
                existing.guard = guard
                existing.destination = log["destination"]
                existing.access_type = log["access_type"]
                existing.entry_time = log["entry_time"]
                existing.status = log["status"]
                if log.get("exit_time"):
                    existing.exit_time = log["exit_time"]
                else:
                    existing.exit_time = None
                existing.notes = ""
                existing.save()
                obj = existing
                created = False
            else:
                # Crear nuevo registro
                obj = AccessLog.objects.create(
                    guard=guard,
                    destination=log["destination"],
                    visitor_name=log["visitor_name"],
                    plate=log["plate"],
                    access_type=log["access_type"],
                    entry_time=log["entry_time"],
                    exit_time=log.get("exit_time"),
                    status=log["status"],
                    notes="",
                )
                created = True

            label = f"{obj.visitor_name} / {obj.plate} — {obj.status}"
            if log["status"] == AccessLog.Status.OPEN:
                entry_time = log["entry_time"]  # type: ignore[assignment]
                hrs = (NOW - entry_time).total_seconds() / 3600  # type: ignore[operator]
                if hrs >= 24:
                    label += f" ⚠ ({hrs:.0f}h)"
            self._log("Log", label, created, indent=4)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, kind: str, name: str, created: bool, indent: int = 2):
        prefix = " " * indent
        if created:
            self.stdout.write(f"{prefix}{self.style.SUCCESS('+')} [{kind}] {name}")
        else:
            self.stdout.write(f"{prefix}  [{kind}] {name} (ya existe)")
