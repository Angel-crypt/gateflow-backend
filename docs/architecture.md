# GateFlow — Arquitectura del Backend

Sistema de gestión de accesos para parques industriales. Inquilinos generan pases QR; guardias los validan en la entrada; admins monitorean métricas.

**Stack:** Python 3.13 · Django 6 · PostgreSQL (prod) / SQLite3 (dev) · DRF + SimpleJWT · uv

---

## Roles del sistema

| Rol | Creado por | Responsabilidad |
|---|---|---|
| `is_superuser` | Django shell / createsuperuser | Crea parques industriales y primeros admins vía Django Admin |
| `admin` | superuser | Gestiona su parque: users, destinations |
| `guard` | admin | Registra entradas/salidas, valida QR en la puerta |
| `tenant` | admin | Genera pases QR para sus destinos asignados |

---

## Estructura de apps

Cuatro apps por dominio — el rol define permisos, no estructura de datos.

| App | Modelos | Responsabilidad |
|---|---|---|
| `users` | `User` | Autenticación, roles, JWT |
| `destinations` | `IndustrialPark`, `Destination` | Catálogos del parque |
| `passes` | `AccessPass` | Generación de pases QR |
| `access` | `AccessLog` | Registro de entradas/salidas y métricas |

---

## Flujo principal

```
Admin crea Destination en su parque
         ↓
Admin crea User(tenant) y asigna Destination[]
         ↓  (destination.responsible = user)
Tenant elige uno de sus Destination y genera AccessPass
         ↓
AccessPass.destination_id = Destination específico (FK)
         ↓
Guard escanea QR → valida AccessPass → crea AccessLog
```

**Punto clave:** cada `Destination` tiene un único `responsible` (FK a `User`). `user.destinations.all()` devuelve todos los destinos donde ese usuario es responsable.

---

## Decisiones técnicas

### `User` — diseño del modelo

- `USERNAME_FIELD = "email"` — login por email
- `email` con `unique=True` (Django no lo hace por defecto en `AbstractUser`)
- FK a `IndustrialPark` para saber a qué parque pertenece el usuario
- `UserManager` propio elimina la dependencia de `username` en `create_superuser`
- `CustomUserAdmin` redefine `fieldsets` completo porque mypy no puede garantizar que `UserAdmin.fieldsets` no sea `None`

### `Destination.responsible` — FK en lugar de M2M

- Cada destino tiene **un único responsable** (`ForeignKey(User, SET_NULL)`)
- Un usuario puede ser responsable de **varios destinos** (relación inversa `user.destinations.all()`)
- Se descartó `ManyToManyField` en `User` porque permitía múltiples responsables por destino, lo cual no corresponde al modelo de negocio

### Migraciones

- `AUTH_USER_MODEL` debe declararse **antes** de la primera migración.
- La dependencia circular entre `users` y `destinations` (User→IndustrialPark, Destination→User) obliga a Django a generar dos migraciones en `destinations`: una para crear los modelos y otra para agregar el FK a `User`.

### mypy

- `django_settings_module` va en `[mypy.plugins.django-stubs]`, no en `[mypy]`
- `explicit_package_bases = true` en `mypy.ini` resuelve el conflicto "source file found twice"

---

## Endpoints — resumen por rol

| Tag | Método | Ruta | Roles |
|---|---|---|---|
| Auth | POST | `/auth/login/` | todos |
| Auth | POST | `/auth/refresh/` | todos |
| Auth | POST | `/auth/logout/` | todos |
| Auth | POST | `/auth/change-password/` | todos |
| Users | GET/POST | `/users/` | admin |
| Users | GET/PATCH | `/users/{id}/` | admin |
| Destinations | GET/POST | `/destinations/` | admin (W), otros (R) |
| Destinations | GET/PATCH | `/destinations/{id}/` | admin (W), otros (R) |
| Passes | GET/POST | `/passes/` | tenant (W), admin (R) |
| Passes | GET | `/passes/{id}/` | tenant (propio), admin |
| Passes | POST | `/passes/validate/` | guard |
| AccessLogs | GET/POST | `/access-logs/` | guard (W), admin (R) |
| AccessLogs | POST | `/access-logs/{id}/exit/` | guard |
| Metrics | GET | `/metrics/summary/` | admin |
| Metrics | GET | `/metrics/by-day/` | admin |
| Metrics | GET | `/metrics/by-hour/` | admin |
| Metrics | GET | `/metrics/top-destinations/` | admin |

---

## Diagrama de base de datos (DBML)

![Esquema de Base de Datos](db_schema.png)

### Relaciones clave

```
IndustrialPark (1) ──< Destination (M)
IndustrialPark (1) ──< User (M)
User (1) ──< Destination (M)   [responsible — un destino, un responsable]
User(tenant) (1) ──< AccessPass (M)
Destination (1) ──< AccessPass (M)   ← FK directa, no a User
AccessPass (1) ──< AccessLog (M)     ← null si entrada manual
Destination (1) ──< AccessLog (M)    ← desnormalizado
User(guard) (1) ──< AccessLog (M)
```

---

## Estado actual de implementación

| Modelo | Estado |
|---|---|
| `IndustrialPark` | Implementado |
| `User` | Implementado |
| `Destination` | Implementado |
| `AccessPass` | Pendiente |
| `AccessLog` | Pendiente |

| Endpoint | Estado |
|---|---|
| `POST /auth/login/` | Implementado |
| `POST /auth/refresh/` | Implementado |
| `POST /auth/logout/` | Implementado |
| `GET /auth/me/` | Implementado |
| `POST /auth/change-password/` | Implementado |
| `GET/POST /users/` | Implementado |
| Resto | Pendiente |
