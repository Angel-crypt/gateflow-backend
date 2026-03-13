# App: destinations

Catálogo de destinos del parque industrial. Un destino puede ser una empresa (`company`) o un área (`area`). Cada destino tiene un único responsable (inquilino).

## Modelos

### `IndustrialPark`

Gestionado exclusivamente desde el Django Admin por superusuario.

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | CharField | Nombre del parque |
| `address` | TextField | Dirección (opcional) |
| `created_at` | DateTimeField | Fecha de creación (auto) |
| `is_active` | BooleanField | Activo/inactivo |

### `Destination`

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | CharField | Nombre del destino |
| `type` | CharField | `company` (empresa) o `area` (área) |
| `park` | FK → IndustrialPark | Parque al que pertenece (CASCADE) |
| `responsible` | FK → User | Inquilino responsable (SET_NULL, opcional) |
| `is_active` | BooleanField | Activo/inactivo |

## Permisos por rol

| Acción | admin | guard | tenant |
|---|---|---|---|
| Listar | todos los del parque | todos los del parque | solo los suyos |
| Ver detalle | ✓ | ✓ | solo si es responsable |
| Crear | ✓ | ✗ | ✗ |
| Editar | ✓ | ✗ | ✗ |
| Eliminar | ✓ | ✗ | ✗ |

> Un tenant que intenta acceder al detalle de un destino que no le pertenece recibe `404` (no se revela la existencia del recurso).

## Endpoints

### `GET /api/destinations/`

Lista destinos según el rol del usuario autenticado.

**Response `200`**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Empresa ABC",
      "type": "company",
      "park": { "id": 1, "name": "Parque Norte" },
      "responsible": {
        "id": 3,
        "email": "carlos@abc.com",
        "first_name": "Carlos",
        "last_name": "López"
      },
      "is_active": true
    },
    {
      "id": 2,
      "name": "Área Recepción",
      "type": "area",
      "park": { "id": 1, "name": "Parque Norte" },
      "responsible": null,
      "is_active": true
    }
  ]
}
```

---

### `POST /api/destinations/`

Crea un destino en el parque del admin autenticado. Solo `admin`.

- El parque se asigna automáticamente.
- `responsible` es opcional; si se proporciona, debe pertenecer al mismo parque.

**Body**
```json
{
  "name": "Empresa Nueva",
  "type": "company",
  "responsible": 3
}
```

**Response `201`** — mismo schema que el objeto en `GET /api/destinations/`.

**Errores**

| Código | Motivo |
|---|---|
| `400` | Datos inválidos o `responsible` de otro parque |
| `401` | No autenticado |
| `403` | Rol sin permiso (`guard` o `tenant`) |

---

### `GET /api/destinations/{id}/`

Detalle de un destino.

- `guard` y `admin`: cualquier destino del parque.
- `tenant`: solo sus propios destinos (404 si no es responsable).

**Response `200`** — mismo schema que el objeto en `GET /api/destinations/`.

---

### `PATCH /api/destinations/{id}/`

Actualización parcial. Solo `admin`.

**Body** (todos los campos son opcionales)
```json
{
  "name": "Nuevo Nombre",
  "is_active": false,
  "responsible": 5
}
```

**Response `200`** — objeto actualizado.

---

### `DELETE /api/destinations/{id}/`

Elimina el destino. Solo `admin`.

**Response `204`** — Sin contenido.
