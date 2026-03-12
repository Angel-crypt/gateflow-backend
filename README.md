# Django Project

Stack: **Python 3.13 · Django 6 · PostgreSQL/SQLite3 · Docker/Podman · uv**

> Para crear este proyecto desde cero consulta [`GUIDE.md`](./GUIDE.md).

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
ENV=dev
```

Cambia a `ENV=prod` cuando quieras usar la configuración de producción.

### `.env.dev` — desarrollo (SQLite3, sin Docker)

```env
SECRET_KEY=unsafe-dev-key
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3
```

No necesitas Docker para desarrollo: SQLite3 funciona sin configuración adicional.

### `.env.prod` — producción (PostgreSQL)

```env
SECRET_KEY=<genera-una-clave-segura>
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://app_user:app_password@localhost:5432/app_db
```

Ajusta `SECRET_KEY`, `ALLOWED_HOSTS` y la URL de la base de datos a tus valores reales.

> **Nunca subas `.env`, `.env.dev` ni `.env.prod` al repositorio.** Están en `.gitignore`.

---

## 4. (Solo para PostgreSQL) Levantar la base de datos

Si usas `ENV=prod` o quieres probar con PostgreSQL en local:

```bash
# Docker
docker compose up -d

# Podman
podman-compose up -d
```

Si usas `ENV=dev` con SQLite3, omite este paso.

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

## 7. Iniciar el servidor de desarrollo

```bash
uv run manage.py runserver
```

Visita: `http://127.0.0.1:8000/`
Admin: `http://127.0.0.1:8000/admin/`

---

## Cambiar de entorno

Solo edita `.env`:

```env
ENV=dev    # SQLite3, DEBUG=True
ENV=prod   # PostgreSQL, DEBUG=False
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
| `uv run manage.py runserver` | Iniciar servidor |
| `uv run pytest` | Correr tests |
| `docker compose up -d` | Levantar PostgreSQL |
| `docker compose down` | Detener contenedores |

## License

Proprietary – All Rights Reserved
Copyright (c) 2026 Angel Cruz and Diego Lara

See the [LICENSE](LICENSE) file for details.
