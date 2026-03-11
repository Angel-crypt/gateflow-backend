# Users

Gestión de autenticación y perfil de usuario.

## Modelo

| Campo | Tipo | Descripción |
|---|---|---|
| `email` | EmailField (unique) | Login principal |
| `username` | CharField | Nombre de usuario (opcional) |
| `role` | CharField | `admin` / `guard` / `company` |
| `park` | FK → IndustrialPark | Parque asignado (opcional) |

## Endpoints

### `POST /auth/login/`
Inicia sesión y retorna tokens JWT.

**Body**
```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

**Response `200`**
```json
{
  "access": "<token>",
  "refresh": "<token>",
  "user": {
    "id": 1,
    "username": "",
    "email": "user@example.com",
    "role": "admin",
    "park_id": null
  }
}
```

---

### `POST /auth/refresh/`
Renueva el `access` token.

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

**Headers:** `Authorization: Bearer <access_token>`

**Body**
```json
{ "refresh": "<token>" }
```

**Response `204`** — Sin contenido.

---

### `GET /auth/me/`
Retorna el perfil del usuario autenticado.

**Headers:** `Authorization: Bearer <access_token>`

**Response `200`**
```json
{
  "id": 1,
  "username": "",
  "email": "user@example.com",
  "role": "admin",
  "park_id": null
}
```

---

### `POST /auth/change-password/`
Cambia la contraseña del usuario autenticado.

**Headers:** `Authorization: Bearer <access_token>`

**Body**
```json
{
  "current_password": "actual",
  "new_password": "nueva_segura"
}
```

**Response `200`**
```json
{ "detail": "Contraseña actualizada correctamente." }
```

## Roles

| Rol | Valor |
|---|---|
| Administrador | `admin` |
| Guardia | `guard` |
| Empresa | `company` |
