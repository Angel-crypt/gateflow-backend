# App: access

Registro de entradas y salidas de visitantes al parque industrial.

## Modelo `AccessLog`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer | Identificador único |
| `access_pass` | FK → AccessPass | Pase usado (SET_NULL, nullable) |
| `destination` | FK → Destination | Destino (CASCADE) |
| `guard` | FK → User | Guardia que registró (SET_NULL) |
| `visitor_name` | CharField | Nombre del visitante |
| `plate` | CharField | Placa del vehículo |
| `notes` | TextField | Observaciones (opcional) |
| `access_type` | CharField | `qr` (escaneo) o `manual` |
| `entry_time` | DateTime | Hora de entrada |
| `exit_time` | DateTime | Hora de salida (nullable) |
| `status` | CharField | `open` (dentro) o `closed` (salió) |
| `created_at` | DateTime | Fecha de creación (auto) |
| `updated_at` | DateTime | Fecha de última modificación (auto) |

## Métodos del modelo

- `register_exit()` — Registra `exit_time = now()` y cambia `status` a `closed`.

## Permisos por rol

| Acción | admin | tenant | guard |
|---|---|---|---|
| Listar | ✓ | ✗ | ✓ |
| Ver detalle | ✓ | ✗ | ✓ |
| Crear (entrada) | ✗ | ✗ | ✓ |
| Registrar salida | ✗ | ✗ | ✓ |

> Admin tiene acceso de lectura para métricas, pero no puede crear registros.

## Endpoints

### `GET /api/access-logs/`

Lista registros del parque. Ordenado por `entry_time` descendente.

**Query params opcionales**

| Param | Tipo | Descripción |
|---|---|---|
| `access_pass` | int | Filtrar por pase específico |
| `search` | string | Buscar por ID de pase, nombre o placa |

**Response `200`**
```json
{
  "count": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "access_pass": { "id": 1, "visitor_name": "Juan Pérez", "plate": "ABC-1234", "pass_type": "day", "valid_from": "...", "valid_to": "..." },
      "destination": { "id": 1, "name": "Empresa ABC", "type": "company" },
      "guard": { "id": 4, "email": "guardia@parque.com", "first_name": "Luis", "last_name": "Martínez" },
      "visitor_name": "Juan Pérez",
      "plate": "ABC-1234",
      "notes": "",
      "access_type": "qr",
      "entry_time": "2026-03-20T09:05:00Z",
      "exit_time": null,
      "status": "open",
      "created_at": "2026-03-20T09:05:00Z"
    }
  ]
}
```

> `access_pass` es `null` en accesos manuales.

---

### `POST /api/access-logs/create/`

Registra una entrada. Solo Guard.

Soporta dos flujos:

#### Flujo QR — `access_pass` presente

```json
{
  "access_pass": 1,
  "notes": "Cliente con cita"
}
```

El sistema valida el pase y transcribe automáticamente `visitor_name`, `plate` y `destination`.

#### Flujo Manual — `access_pass` ausente

```json
{
  "destination": 1,
  "visitor_name": "Visitante Espontáneo",
  "plate": "XYZ-5678",
  "notes": "Reunión sin cita"
}
```

**Comportamiento automático:**
- `guard` → usuario autenticado
- `entry_time` → `now()` si no se provee
- `access_type` → `qr` o `manual`
- `status` → `open`

**Response `201`** — mismo schema que `GET /api/access-logs/`.

---

### `GET /api/access-logs/{id}/`

Detalle de un registro.

**Response `200`**

---

### `POST /api/access-logs/{id}/register-exit/`

Registra la salida de un visitante. Solo Guard.

El registro debe estar en estado `open`.

**Response `200`** — registro actualizado con `exit_time` y `status: closed`.

**Errores:**
- `400` — El acceso ya fue cerrado.
- `404` — Registro no encontrado o de otro parque.
