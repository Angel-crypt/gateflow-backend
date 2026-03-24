# App: passes

Gestión de pases de acceso QR para visitantes del parque industrial.

## Modelo `AccessPass`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer | Identificador único |
| `destination` | FK → Destination | Destino del visitante (CASCADE) |
| `created_by` | FK → User | Usuario que creó el pase (CASCADE) |
| `visitor_name` | CharField | Nombre del visitante |
| `plate` | CharField | Placa del vehículo |
| `pass_type` | CharField | `single` (uso único) o `day` (pase de día) |
| `valid_from` | DateTime | Inicio de validez |
| `valid_to` | DateTime | Fin de validez |
| `is_active` | BooleanField | Activo/inactivo (para desactivar sin borrar) |
| `is_used` | BooleanField | Marcado como usado (para `single`) |
| `created_at` | DateTime | Fecha de creación (auto) |
| `updated_at` | DateTime | Fecha de última modificación (auto) |

## Métodos del modelo

- `is_valid()` — Retorna `True` si el pase está activo y `valid_from <= now <= valid_to`.

## Permisos por rol

| Acción | admin | tenant | guard |
|---|---|---|---|
| Listar | todos del parque | solo los suyos | ✗ |
| Crear | ✓ | ✓ | ✗ |
| Ver detalle | ✓ | solo los suyos | ✗ |
| Editar | ✓ | solo los suyos | ✗ |
| Eliminar | ✓ | solo los suyos | ✗ |
| Validar (QR) | ✓ | ✓ | ✓ |

## Endpoints

### `GET /api/passes/`

Lista pases según el rol.

- **Admin:** todos los pases del parque.
- **Tenant:** solo los pases de sus destinos.

**Response `200`**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "destination": { "id": 1, "name": "Empresa ABC", "type": "company" },
      "created_by": { "id": 2, "email": "admin@parque.com", "first_name": "Admin", "last_name": "Demo" },
      "visitor_name": "Juan Pérez",
      "plate": "ABC-1234",
      "pass_type": "day",
      "valid_from": "2026-03-20T08:00:00Z",
      "valid_to": "2026-03-20T18:00:00Z",
      "is_active": true,
      "is_used": false,
      "created_at": "2026-03-19T15:00:00Z"
    }
  ]
}
```

---

### `POST /api/passes/`

Crea un pase de acceso.

**Body**
```json
{
  "visitor_name": "Juan Pérez",
  "plate": "ABC-1234",
  "pass_type": "day",
  "valid_from": "2026-03-20T08:00:00Z",
  "valid_to": "2026-03-20T18:00:00Z",
  "destination": 1
}
```

- `destination` es opcional si el usuario tiene un solo destino.
- **Admin:** solo puede asignar destinos de tipo `area`.
- **Tenant:** solo puede asignar destinos de los que es responsable.
- El `id` retornado es el valor para generar el código QR.

**Response `201`** — mismo schema que `GET /api/passes/`.

---

### `GET /api/passes/{id}/`

Detalle de un pase.

**Response `200`**

---

### `PATCH /api/passes/{id}/`

Actualización parcial.

**Body** (campos opcionales)
```json
{
  "valid_to": "2026-03-20T20:00:00Z",
  "is_active": false
}
```

**Response `200`**

---

### `DELETE /api/passes/{id}/`

Elimina el pase.

**Response `204`** — Sin contenido.

---

### `POST /api/passes/validate/`

Valida un pase por ID (usado al escanear QR).

**Body**
```json
{ "pass_id": 1 }
```

**Response `200`** — Pase válido
```json
{
  "is_valid": true,
  "id": 1,
  "destination": { "id": 1, "name": "Empresa ABC", "type": "company" },
  "visitor_name": "Juan Pérez",
  "plate": "ABC-1234",
  "pass_type": "day",
  "valid_from": "2026-03-20T08:00:00Z",
  "valid_to": "2026-03-20T18:00:00Z",
  "is_active": true,
  "created_at": "2026-03-19T15:00:00Z"
}
```

**Response `400`** — Pase inválido
```json
{ "detail": "El pase no es válido o ha expirado.", "is_valid": false }
```

**Errores adicionales:**
- `already_used` — Pase de uso único ya utilizado
- `inactive` — Pase desactivado
- `not_yet_valid` — Aún no es válido (antes de `valid_from`)
- `expired` — Ya expiró (después de `valid_to`)
