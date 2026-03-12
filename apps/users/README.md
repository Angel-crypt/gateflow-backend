# App: users

Autenticación JWT, roles y gestión de usuarios del parque.

## Modelo `User`

Extiende `AbstractUser`. Login por email, username se autogenera.

| Campo | Tipo | Descripción |
|---|---|---|
| `email` | EmailField (unique) | Login principal, reemplaza a `username` |
| `username` | CharField | Autogenerado, no se usa para login |
| `role` | CharField | `admin` / `guard` / `company` |
| `park` | FK → IndustrialPark | Parque al que pertenece (SET_NULL) |
| `destinations` | M2M → Destination | Solo relevante para `company` |
| `is_active` | BooleanField | Activo/inactivo, no se borran usuarios |

## Roles

| Rol | Creado por | Puede hacer |
|---|---|---|
| `admin` | superuser (Django Admin) | Gestiona su parque completo |
| `guard` | admin | Registra entradas/salidas, valida QR |
| `company` | admin | Genera pases QR para sus destinos |

## Endpoints

### `POST /auth/login/`

**Body**
```json
{ "email": "admin@parque.com", "password": "secret123" }
```

**Response `200`**
```json
{
  "access": "<token>",
  "refresh": "<token>",
  "user": {
    "id": 1,
    "email": "admin@parque.com",
    "role": "admin",
    "is_active": true,
    "park": { "id": 1, "name": "Parque Norte" },
    "destinations": []
  }
}
```

---

### `POST /auth/refresh/`

**Body**
```json
{ "refresh": "<token>" }
```

**Response `200`**
```json
{ "access": "<nuevo_token>" }
```

---

### `POST /auth/logout/`

Invalida el `refresh` token. Requiere autenticación.

**Body**
```json
{ "refresh": "<token>" }
```

**Response `204`** — Sin contenido.

---

### `GET /auth/me/`

Perfil del usuario autenticado. Si `role=company`, incluye `destinations`.

**Response `200`**
```json
{
  "id": 2,
  "email": "empresa@abc.com",
  "role": "company",
  "is_active": true,
  "park": { "id": 1, "name": "Parque Norte" },
  "destinations": [
    { "id": 3, "name": "Empresa ABC", "type": "company" }
  ]
}
```

---

### `POST /auth/change-password/`

**Body**
```json
{
  "current_password": "actual",
  "new_password": "nueva_segura",
  "confirm_password": "nueva_segura"
}
```

**Response `204`** — Sin contenido.

---

### `GET /api/users/`

Lista usuarios del parque del admin autenticado. Excluye superusuarios. Solo `admin`.

**Query params**

| Param | Tipo | Descripción |
|---|---|---|
| `role` | string | Filtrar por `admin`, `guard` o `company` |
| `is_active` | boolean | Filtrar por estado activo |
| `page` | integer | Número de página (default: 1) |
| `page_size` | integer | Tamaño de página (default: 20) |

**Response `200`**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "email": "guard@parque.com",
      "role": "guard",
      "is_active": true,
      "park": { "id": 1, "name": "Parque Norte" },
      "destinations": []
    }
  ]
}
```

---

### `POST /api/users/`

Crea un usuario `guard` o `company` en el parque del admin. Solo `admin`.

- El parque se asigna automáticamente al parque del admin.
- Si `role=company`, `destinations` es obligatorio y deben pertenecer al parque del admin.
- No se puede crear `role=admin` desde este endpoint.

**Body — guardia**
```json
{ "email": "guardia01@parque.com", "password": "temp1234", "role": "guard" }
```

**Body — empresa**
```json
{
  "email": "empresa@abc.com",
  "password": "temp1234",
  "role": "company",
  "destinations": [3, 7]
}
```

**Response `201`** — mismo schema que `GET /auth/me/`.
