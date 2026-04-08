# Django Project

Stack: **Python 3.13 · Django 6 · PostgreSQL/SQLite3 · Docker/Podman · uv**

> Para crear este proyecto desde cero consulta [`GUIDE.md`](./GUIDE.md).

---

## Capturas de pantalla

| | |
|:---|:---|
| ![Dashboard - Admin](docs/SCREENSHOTS/DASHBOARD%20-%20ADMIN.png) | ![Access Management - Admin](docs/SCREENSHOTS/ACCESS%20MANAGEMENT%20-%20ADMIN.png) |
| **Dashboard Admin** - Métricas del parque | **Access Management** - Registros de acceso |
| ![Passes Management - Admin](docs/SCREENSHOTS/PASSES%20MANAGMENT%20-%20ADMIN.png) | ![Active Access - Guard](docs/SCREENSHOTS/ACTIVE%20ACCESS%20-%20GUARD.png) |
| **Passes Management** - Administración de QR | **Active Access** - Visitantes dentro del parque |
| ![Register QR Access - Guard](docs/SCREENSHOTS/REGISTER%20QR%20ACCESS%20-%20GUARD.png) | ![Register Manual Access - Guard](docs/SCREENSHOTS/REGISTER%20MANUAL%20ACCESS%20-%20GUARD.png) |
| **Register QR** - Escaneo de código QR | **Register Manual** - Acceso sin QR |

---

## Requisitos previos

- [`uv`](https://astral.sh/uv) instalado
- Docker o Podman instalado

### Instalar uv

**Linux / macOS**

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 1. Clonar el repositorio

```bash
git clone git@github.com:Angel-crypt/gateflow-backend.git
cd gateflow-backend
```

---

## 2. Instalar dependencias

```bash
uv sync
```

Esto instala exactamente las versiones del `uv.lock`, sin diferencias entre entornos.

---

## 3. Configurar las variables de entorno

El proyecto usa tres archivos `.env`. Encontrarás las plantillas en la carpeta `examples env/`.

```bash
# Copia las plantillas
cp "examples-dev/.env.example" .env
cp "examples-dev/.env.dev.example" .env.dev
cp "examples-dev/.env.prod.example" .env.prod
```

### `.env` — entorno activo

```env
DJANGO_ENV=dev
```

Cambia a `DJANGO_ENV=prod` cuando quieras usar la configuración de producción.

### `.env.dev` — desarrollo (SQLite3, sin Docker)

```env
SECRET_KEY=unsafe-dev-key
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOW_ALL_ORIGINS=True
```

No necesitas Docker para desarrollo: SQLite3 funciona sin configuración adicional.

### `.env.prod` — producción (PostgreSQL)

```env
SECRET_KEY=<genera-una-clave-segura>
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://app_user:app_password@db:5432/app_db
CORS_ALLOWED_ORIGINS=https://tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com
```

Ajusta `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` y la URL de la base de datos a tus valores reales.

> **Nunca subas `.env`, `.env.dev` ni `.env.prod` al repositorio.** Están en `.gitignore`.

---

## 4. (Solo para PostgreSQL) Levantar la base de datos

Si usas `DJANGO_ENV=prod` o quieres probar con PostgreSQL en local:

```bash
# Docker (desde la raíz del workspace)
docker compose --env-file .env.compose up -d db

# Podman
podman-compose up -d
```

Si usas `DJANGO_ENV=dev` con SQLite3, omite este paso.

---

## 5. Aplicar migraciones

```bash
uv run manage.py migrate
```

---

## 6. (Opcional) Crear superusuario

```bash
uv run manage.py createsuperuser
```

---

## 7. Cargar datos iniciales (seed)

Crea un parque industrial, usuarios de prueba, destinos, pases y registros de acceso.
Es **idempotente**: ejecutarlo varias veces no duplica datos.

```bash
# Carga completa
uv run manage.py seed

# Resetear y recargar (elimina datos del seed previo)
uv run manage.py seed --flush

# Solo una sección
uv run manage.py seed --only users
uv run manage.py seed --only passes
uv run manage.py seed --only logs

# Contraseña personalizada para todos los usuarios creados
uv run manage.py seed --password MiPassword123
```

El seed imprime las credenciales de los usuarios creados. Por defecto:

| Rol | Email | Contraseña |
|---|---|---|
| Admin | `admin@gateflow.mx` | `Bajio2026!` |
| Guardia | `guardia1@gateflow.mx` | `Seguridad6!` |
| Guardia | `guardia2@gateflow.mx` | `Seguridad6!` |
| Inquilino | `inquilino1@acerosnorte.mx` | `Parque2026!` |
| Inquilino | `inquilino2@techparts.mx` | `Parque2026!` |

> El seed funciona en cualquier entorno (`dev` con SQLite3 o `prod` con PostgreSQL).

---

## 9. Iniciar el servidor de desarrollo

```bash
uv run manage.py runserver
```

Visita: `http://127.0.0.1:8000/`
Admin: `http://127.0.0.1:8000/admin/`

---

## Cambiar de entorno

Solo edita `.env`:

```env
DJANGO_ENV=dev    # SQLite3, DEBUG=True
DJANGO_ENV=prod   # PostgreSQL, DEBUG=False
```

---

## Calidad de código

```bash
# Linter + formatter + type checking
uv run ruff check . --fix && black . && uv run python -m mypy .
```

---

## Tests

```bash
# Todos los tests
uv run pytest

# Tests de una app específica
uv run pytest apps/users/

# Un test por nombre
uv run pytest -k "test_create_guard"

# Con output detallado
uv run pytest -v
```

---

## Referencia rápida

| Comando | Descripción |
|---|---|
| `uv sync` | Instalar dependencias |
| `uv add <pkg>` | Agregar nueva dependencia |
| `uv run manage.py migrate` | Aplicar migraciones |
| `uv run manage.py createsuperuser` | Crear superusuario |
| `uv run manage.py seed` | Cargar datos iniciales |
| `uv run manage.py seed --flush` | Resetear y recargar seed |
| `uv run manage.py runserver` | Iniciar servidor |
| `uv run pytest` | Correr tests |
| `docker compose --env-file .env.compose up -d --build` | Levantar stack de producción |
| `docker compose down` | Detener contenedores |

---

## Despliegue sin contenedores (Render/Railway/Fly)

Configura variables de entorno usando como base `examples-dev/.env.vercel.example`.

Comandos típicos de despliegue:

```bash
uv sync --frozen
uv run manage.py migrate
uv run manage.py collectstatic --noinput
uv run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Puntos clave:

- Usa PostgreSQL gestionado y `DATABASE_URL` del proveedor.
- Mantén `DEBUG=False` en producción.
- Declara dominios reales en `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS`.

## License

Proprietary – All Rights Reserved
Copyright (c) 2026 Angel Cruz and Diego Lara

See the [LICENSE](LICENSE) file for details.
