# GateFlow — Referencia de API

**Base URL:** `http://localhost:8000`
**Autenticación:** JWT Bearer Token — `Authorization: Bearer <access_token>`
**Formato:** JSON en todos los endpoints

---

## Índice

- [Auth](#auth)
- [Users](#users)
- [Industrial Parks](#industrial-parks)
- [Destinations](#destinations)
- [Passes](#passes)
- [Access Logs](#access-logs)
- [Metrics](#metrics)

---

## Auth

Endpoints de sesión y perfil. Los de login y refresh no requieren token.

---

### `POST /auth/login/`

Inicia sesión y obtiene tokens JWT.

**Roles:** ninguno (público)

**Body:**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `email` | string | Sí |
| `password` | string | Sí |

**Respuesta `200`:**

```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": 1,
    "email": "admin@demo.com",
    "first_name": "Admin",
    "last_name": "Demo",
    "role": "admin",
    "is_active": true,
    "park": { "id": 1, "name": "Parque Industrial Norte" },
    "destinations": []
  }
}
```

**Errores:** `401` credenciales inválidas.

---

### `POST /auth/refresh/`

Renueva el `access` token usando el `refresh` token.

**Roles:** ninguno (público)

**Body:**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `refresh` | string | Sí |

**Respuesta `200`:**

```json
{ "access": "<nuevo_jwt_access_token>" }
```

**Errores:** `401` token inválido o expirado.

---

### `POST /auth/logout/`

Invalida el `refresh` token (blacklist).

**Roles:** cualquier autenticado

**Body:**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `refresh` | string | Sí |

**Respuesta `204`:** sin cuerpo.

**Errores:** `400` token no enviado o ya inválido.

---

### `GET /auth/me/`

Retorna el perfil del usuario autenticado.

**Roles:** cualquier autenticado

**Respuesta `200`:**

```json
{
  "id": 1,
  "email": "admin@demo.com",
  "first_name": "Admin",
  "last_name": "Demo",
  "role": "admin",
  "is_active": true,
  "park": { "id": 1, "name": "Parque Industrial Norte" },
  "destinations": []
}
```

> Para un tenant, `destinations` lista los destinos de los que es `responsible`.

---

### `POST /auth/change-password/`

Cambia la contraseña del usuario autenticado.

**Roles:** cualquier autenticado

**Body:**

| Campo | Tipo | Requerido | Validación |
|-------|------|-----------|------------|
| `current_password` | string | Sí | Debe coincidir con la contraseña vigente |
| `new_password` | string | Sí | Mínimo 8 caracteres |
| `confirm_password` | string | Sí | Debe ser igual a `new_password` |

**Respuesta `204`:** sin cuerpo.

**Errores:** `400` contraseña actual incorrecta, no coinciden o muy corta.

---

## Users

Gestión de usuarios del parque. Solo accesible por el Admin.

---

### `GET /api/users/`

Lista todos los usuarios del parque del admin.

**Roles:** `admin`

**Query params opcionales:**

| Param | Valores | Descripción |
|-------|---------|-------------|
| `role` | `guard` \| `tenant` | Filtrar por rol |
| `is_active` | `true` \| `false` | Filtrar por estado |

**Respuesta `200`:** lista de usuarios con `park` y `destinations` anidados.

---

### `POST /api/users/`

Crea un guardia o inquilino en el parque del admin.

**Roles:** `admin`

**Body:**

| Campo | Tipo | Requerido | Validación |
|-------|------|-----------|------------|
| `email` | string | Sí | Único en el sistema |
| `password` | string | Sí | Mínimo 8 caracteres |
| `first_name` | string | No | — |
| `last_name` | string | No | — |
| `role` | `guard` \| `tenant` | Sí | No se permite crear `admin` |

El parque se asigna automáticamente al del admin autenticado.

**Respuesta `201`:** perfil completo del usuario creado.

**Errores:** `400` email duplicado, contraseña corta o rol inválido. `403` no es admin.

---

## Industrial Parks

---

### `GET /api/destinations/parks/`

Lista todos los parques industriales del sistema.

**Roles:** cualquier autenticado

**Respuesta `200`:**

```json
[
  { "id": 1, "name": "Parque Industrial Norte" }
]
```

---

## Destinations

El Admin tiene control total. El Tenant solo puede leer sus propios destinos.

---

### `GET /api/destinations/`

Lista destinos según el rol del usuario.

**Roles:** `admin`, `tenant`

- **Admin:** todos los destinos de su parque, ordenados por `id`.
- **Tenant:** solo los destinos donde es `responsible`.

**Respuesta `200`:**

```json
[
  {
    "id": 1,
    "name": "Empresa ABC",
    "type": "company",
    "park": { "id": 1, "name": "Parque Industrial Norte" },
    "responsible": { "id": 3, "email": "inquilino@abc.com", "first_name": "Carlos", "last_name": "López" },
    "is_active": true
  }
]
```

---

### `POST /api/destinations/`

Crea un nuevo destino en el parque del admin.

**Roles:** `admin`

**Body:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `name` | string | Sí | Nombre del destino |
| `type` | `company` \| `area` | Sí | Tipo de destino |
| `responsible` | int (user ID) \| null | No | Tenant responsable, debe pertenecer al mismo parque |
| `is_active` | bool | No | Por defecto `true` |

El parque se asigna automáticamente al del admin.

**Respuesta `201`:** destino completo con `park` y `responsible` anidados.

**Errores:** `400` responsible de otro parque. `403` no es admin.

---

### `GET /api/destinations/{id}/`

Detalle de un destino.

**Roles:** `admin`, `tenant`

- Tenant solo puede acceder a sus propios destinos.

**Respuesta `200`:** objeto destino completo.

**Errores:** `404` no existe o fuera del scope del usuario.

---

### `PATCH /api/destinations/{id}/`

Actualiza parcialmente un destino.

**Roles:** `admin`

**Body** (todos opcionales):

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | string | Nuevo nombre |
| `type` | `company` \| `area` | Nuevo tipo |
| `responsible` | int \| null | Nuevo responsable (mismo parque) |
| `is_active` | bool | Activar / desactivar |

**Respuesta `200`:** destino actualizado completo.

**Errores:** `403` no es admin. `404` no existe.

---

### `DELETE /api/destinations/{id}/`

Elimina permanentemente un destino.

**Roles:** `admin`

**Respuesta `204`:** sin cuerpo.

> ⚠️ Eliminación en cascada: se borran todos los `AccessPass` y `AccessLog` asociados.

---

## Passes

El Admin y el Tenant pueden crear y gestionar pases. El Guard solo puede validarlos.

El `id` retornado al crear un pase es el valor que el frontend usa para generar el código QR.

---

### `GET /api/passes/`

Lista pases según el rol del usuario.

**Roles:** `admin`, `tenant`

- **Admin:** todos los pases del parque, ordenados por `created_at` descendente.
- **Tenant:** solo los pases de sus destinos.

**Respuesta `200`:**

```json
[
  {
    "id": 1,
    "destination": { "id": 1, "name": "Empresa ABC", "type": "company" },
    "created_by": { "id": 2, "email": "admin@demo.com", "first_name": "Admin", "last_name": "Demo" },
    "visitor_name": "Juan Pérez",
    "plate": "ABC-1234",
    "pass_type": "day",
    "valid_from": "2026-03-17T08:00:00Z",
    "valid_to": "2026-03-17T18:00:00Z",
    "is_active": true,
    "created_at": "2026-03-16T20:00:00Z"
  }
]
```

---

### `POST /api/passes/`

Crea un pase de acceso para un visitante.

**Roles:** `admin`, `tenant`

**Body:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `visitor_name` | string | Sí | Nombre del visitante |
| `plate` | string | Sí | Placa del vehículo |
| `pass_type` | `day` \| `single` | No | `day` = pase de día, `single` = uso único. Por defecto `day` |
| `valid_from` | datetime ISO 8601 | Sí | Inicio de validez |
| `valid_to` | datetime ISO 8601 | Sí | Fin de validez. Debe ser posterior a `valid_from` |
| `destination` | int (ID) | Condicional | Requerido si el usuario tiene más de un destino disponible. Si tiene exactamente uno, se asigna automáticamente |

El `created_by` se asigna automáticamente al usuario autenticado.

**Respuesta `201`:** pase completo. El `id` es el valor para generar el QR.

**Errores:**
- `400` `valid_to` anterior a `valid_from`, placa faltante, o usuario con múltiples destinos sin especificar `destination`.
- `403` no es admin ni tenant.

---

### `GET /api/passes/{id}/`

Detalle de un pase.

**Roles:** `admin`, `tenant`

**Respuesta `200`:** objeto pase con `destination` y `created_by` anidados.

**Errores:** `404` no existe o fuera del scope.

---

### `PATCH /api/passes/{id}/`

Actualiza parcialmente un pase.

**Roles:** `admin`, `tenant`

**Body** (todos opcionales):

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `visitor_name` | string | Nuevo nombre del visitante |
| `plate` | string | Nueva placa |
| `destination` | int | Reasignar destino |
| `pass_type` | `day` \| `single` | Cambiar tipo |
| `valid_from` | datetime | Nueva fecha de inicio |
| `valid_to` | datetime | Nueva fecha de fin (debe ser posterior a `valid_from`) |
| `is_active` | bool | `false` para desactivar el pase sin eliminarlo |

**Respuesta `200`:** pase actualizado completo.

---

### `DELETE /api/passes/{id}/`

Elimina permanentemente un pase.

**Roles:** `admin`, `tenant`

**Respuesta `204`:** sin cuerpo.

> Los `AccessLog` que referenciaban este pase quedarán con `access_pass: null`.

---

### `POST /api/passes/validate/`

Verifica si un pase es vigente dado su ID. Usado por el guardia al escanear el QR.

**Roles:** cualquier autenticado

**Body:**

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `pass_id` | int | Sí |

**Respuesta `200`:** pase válido.

```json
{
  "is_valid": true,
  "id": 1,
  "destination": { "id": 1, "name": "Empresa ABC", "type": "company" },
  "visitor_name": "Juan Pérez",
  "plate": "ABC-1234",
  "pass_type": "day",
  "valid_from": "2026-03-17T08:00:00Z",
  "valid_to": "2026-03-17T18:00:00Z",
  "is_active": true,
  "created_at": "2026-03-16T20:00:00Z"
}
```

**Respuesta `400`:** pase inactivo o fuera de rango.

```json
{ "detail": "El pase no es válido o ha expirado.", "is_valid": false }
```

**Errores:** `400` `pass_id` no enviado o pase inválido. `404` pase no encontrado.

---

## Access Logs

Solo el Guard puede registrar y consultar accesos. Todos los datos están limitados al parque del guardia.

---

### `GET /api/access-logs/`

Lista registros de acceso del parque del guardia.

**Roles:** `guard`

**Respuesta `200`:** lista ordenada por `entry_time` descendente.

```json
[
  {
    "id": 1,
    "access_pass": { "id": 1, "visitor_name": "Juan Pérez", "plate": "ABC-1234", "pass_type": "day", "valid_from": "...", "valid_to": "..." },
    "destination": { "id": 1, "name": "Empresa ABC", "type": "company" },
    "guard": { "id": 4, "email": "guardia01@parque.com", "first_name": "Luis", "last_name": "Martínez" },
    "visitor_name": "Juan Pérez",
    "plate": "ABC-1234",
    "notes": "",
    "access_type": "qr",
    "entry_time": "2026-03-17T09:05:00Z",
    "exit_time": null,
    "status": "open",
    "created_at": "2026-03-17T09:05:00Z"
  }
]
```

> `access_pass` es `null` en accesos manuales.

---

### `POST /api/access-logs/create/`

Registra un acceso. Soporta dos flujos.

**Roles:** `guard`

#### Flujo QR — `access_pass` presente

El guardia escanea el QR, obtiene el `pass_id` y lo envía. El sistema transcribe automáticamente `visitor_name`, `plate` y `destination` desde el pase.

**Body:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `access_pass` | int (pass ID) | Sí | ID del pase escaneado |
| `notes` | string | No | Observaciones del guardia |

**Validaciones:** el pase debe ser vigente (`is_active=true` y dentro del rango de fechas) y pertenecer al parque del guardia.

#### Flujo Manual — `access_pass` ausente

El guardia ingresa todos los datos manualmente.

**Body:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `destination` | int (ID) | Sí | Destino del parque del guardia |
| `visitor_name` | string | Sí | Nombre del visitante |
| `plate` | string | Sí | Placa del vehículo |
| `notes` | string | No | Observaciones |
| `entry_time` | datetime ISO 8601 | No | Por defecto: hora actual |

#### Comportamiento automático (ambos flujos)

- `guard` → se toma del perfil del usuario autenticado.
- `entry_time` → se asigna a `now()` si no se provee.
- `access_type` → `"qr"` si hay `access_pass`, `"manual"` si no.
- `status` → siempre `"open"` al crear.

**Respuesta `201`:** objeto `AccessLog` completo.

**Errores:**
- `400` pase inactivo, expirado, de otro parque, o campos manuales faltantes.
- `404` pase no encontrado.

---

### `GET /api/access-logs/{id}/`

Detalle de un registro de acceso.

**Roles:** `guard`

**Respuesta `200`:** objeto `AccessLog` completo con todos los datos anidados.

**Estados de `status`:**

| Valor | Significado |
|-------|-------------|
| `open` | Visitante dentro del parque |
| `closed` | Visitante ya salió |

**Errores:** `404` no existe o pertenece a otro parque.

---

## Metrics

Solo el Admin puede consultar métricas. Todos los datos están limitados al parque del admin.

---

### `GET /api/metrics/dashboard/`

Snapshot general del estado actual del parque.

**Roles:** `admin`

**Respuesta `200`:**

```json
{
  "park": { "id": 1, "name": "Parque Industrial Norte" },
  "users": {
    "total": 10,
    "guards": 4,
    "tenants": 6
  },
  "destinations": {
    "total": 5,
    "active": 4,
    "inactive": 1
  },
  "passes": {
    "total": 50,
    "active": 12,
    "upcoming": 3,
    "expired": 35,
    "deactivated": 3
  },
  "access_logs": {
    "total": 200,
    "today": 15,
    "open_now": 3,
    "by_type": { "qr": 120, "manual": 80 }
  }
}
```

**Estados de pases:**

| Campo | Descripción |
|-------|-------------|
| `active` | `is_active=true` y dentro del rango de fechas ahora mismo |
| `upcoming` | `is_active=true` pero `valid_from` aún no ha llegado |
| `expired` | `valid_to` ya pasó |
| `deactivated` | Desactivado manualmente (`is_active=false`) |

`open_now` — visitantes físicamente dentro del parque en este momento.

---

### `GET /api/metrics/access-logs/`

Analíticas de registros de acceso para un periodo.

**Roles:** `admin`

**Query params:**

| Param | Valores | Por defecto |
|-------|---------|-------------|
| `period` | `today` \| `week` \| `month` | `week` |

**Respuesta `200`:**

```json
{
  "period": "week",
  "total": 45,
  "open_now": 3,
  "by_type": { "qr": 35, "manual": 10 },
  "by_destination": [
    { "destination": "Empresa ABC", "count": 25 },
    { "destination": "Área Logística", "count": 20 }
  ],
  "by_day": [
    { "date": "2026-03-10", "count": 5 },
    { "date": "2026-03-11", "count": 8 }
  ]
}
```

- `by_destination` — ordenado por mayor número de accesos.
- `by_day` — evolución diaria del periodo, orden cronológico.
- `open_now` — no está filtrado por periodo; refleja el estado actual.

---

### `GET /api/metrics/passes/`

Analíticas de pases del parque.

**Roles:** `admin`

**Respuesta `200`:**

```json
{
  "total": 50,
  "active": 12,
  "upcoming": 3,
  "expired": 35,
  "deactivated": 3,
  "by_type": {
    "day": 40,
    "single": 10
  },
  "by_destination": [
    { "destination": "Empresa ABC", "count": 30 },
    { "destination": "Área Logística", "count": 20 }
  ]
}
```

- `by_destination` — total de pases (cualquier estado) por destino, orden descendente.

---

## Resumen de permisos por endpoint

| Método | Ruta | Admin | Tenant | Guard |
|--------|------|:-----:|:------:|:-----:|
| POST | `/auth/login/` | ✓ | ✓ | ✓ |
| POST | `/auth/refresh/` | ✓ | ✓ | ✓ |
| POST | `/auth/logout/` | ✓ | ✓ | ✓ |
| GET | `/auth/me/` | ✓ | ✓ | ✓ |
| POST | `/auth/change-password/` | ✓ | ✓ | ✓ |
| GET | `/api/users/` | ✓ | — | — |
| POST | `/api/users/` | ✓ | — | — |
| GET | `/api/destinations/parks/` | ✓ | ✓ | ✓ |
| GET | `/api/destinations/` | ✓ | ✓ | — |
| POST | `/api/destinations/` | ✓ | — | — |
| GET | `/api/destinations/{id}/` | ✓ | ✓ | — |
| PATCH | `/api/destinations/{id}/` | ✓ | — | — |
| DELETE | `/api/destinations/{id}/` | ✓ | — | — |
| GET | `/api/passes/` | ✓ | ✓ | — |
| POST | `/api/passes/` | ✓ | ✓ | — |
| GET | `/api/passes/{id}/` | ✓ | ✓ | — |
| PATCH | `/api/passes/{id}/` | ✓ | ✓ | — |
| DELETE | `/api/passes/{id}/` | ✓ | ✓ | — |
| POST | `/api/passes/validate/` | ✓ | ✓ | ✓ |
| GET | `/api/access-logs/` | — | — | ✓ |
| POST | `/api/access-logs/create/` | — | — | ✓ |
| GET | `/api/access-logs/{id}/` | — | — | ✓ |
| GET | `/api/metrics/dashboard/` | ✓ | — | — |
| GET | `/api/metrics/access-logs/` | ✓ | — | — |
| GET | `/api/metrics/passes/` | ✓ | — | — |
