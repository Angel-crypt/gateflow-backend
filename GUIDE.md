# Guía: Crear este proyecto Django desde cero

Stack: **Python 3.13+ · Django 6 · PostgreSQL/SQLite3 · Docker/Podman · uv**

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

## 1. Inicializar el proyecto

```bash
uv init NAME_PROJECT
cd NAME_PROJECT
```

Esto crea la estructura base con `pyproject.toml` y el entorno virtual.

---

## 2. Agregar dependencias

```bash
uv add django django-environ django-jazzmin psycopg2-binary ruff black mypy django-stubs
```

| Paquete | Propósito |
|---|---|
| `django` | Framework principal |
| `django-environ` | Lectura de variables de entorno |
| `django-jazzmin` | Admin panel mejorado |
| `psycopg2-binary` | Driver PostgreSQL |
| `ruff` | Linter rápido |
| `black` | Formatter |
| `mypy` + `django-stubs` | Type checking |

---

## 3. Activar el entorno virtual

```bash
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

---

## 4. Crear el proyecto Django

```bash
django-admin startproject config .
```

El `.` al final crea `manage.py` en la raíz (no en una subcarpeta extra).

Estructura resultante:
```
NAME_PROJECT/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── pyproject.toml
└── uv.lock
```

---

## 5. Configurar herramientas de calidad en `pyproject.toml`

Agregar al final del `pyproject.toml` generado por `uv init`:

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "C4", "UP"]

[tool.black]
line-length = 120
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
warn_return_any = true
warn_unused_configs = true
plugins = ["mypy_django_plugin.main"]
ignore_missing_imports = true

[tool.django-stubs]
django_settings_module = "config.settings"
```

---

## 6. Crear `.gitignore`

```bash
touch .gitignore
```

Contenido:

```gitignore
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# Environment variables
.env
.env.dev
.env.prod
```

---

## 7. Crear los archivos de variables de entorno

```bash
touch .env .env.dev .env.prod
```

### `.env` — entorno activo

```env
ENV=dev
```

Cambia entre `dev` y `prod` según el entorno donde corras el proyecto.

### `.env.dev` — desarrollo local (SQLite3)

```env
SECRET_KEY=unsafe-dev-key
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3
```

### `.env.prod` — producción (PostgreSQL)

```env
SECRET_KEY=super-secret-production-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://app_user:app_password@localhost:5432/app_db
```

> **Importante:** `.env`, `.env.dev` y `.env.prod` están en `.gitignore`. Nunca los subas al repositorio.

### Crear archivos de ejemplo (para el repo)

Para que otros colaboradores sepan qué variables configurar, crea una carpeta con ejemplos:

```bash
mkdir "examples env"
```

**`examples env/.env.example`**
```env
ENV=dev
```

**`examples env/.env.dev.example`**
```env
SECRET_KEY=unsafe-dev-key
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3
```

**`examples env/.env.prod.example`**
```env
SECRET_KEY=super-secret-production-key
DEBUG=False
ALLOWED_HOSTS=*
DATABASE_URL=postgres://app_user:app_password@localhost:5432/app_db
```

---

## 8. Configurar `config/settings.py`

Reemplaza el contenido del `settings.py` generado por Django con:

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

env.read_env(BASE_DIR / ".env")
ENV = env("ENV", default="dev")
env.read_env(BASE_DIR / f".env.{ENV}", overwrite=True)

print(f"Environment: {ENV}")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


# Application definition
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# django-environ detecta el engine por el prefijo de DATABASE_URL:
#   sqlite:///  → SQLite3
#   postgres:// → PostgreSQL
DATABASES = {"default": env.db("DATABASE_URL")}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
```

**Cómo funciona la carga de entornos:**

1. Lee `.env` → obtiene `ENV=dev` (o `prod`)
2. Lee `.env.dev` (o `.env.prod`) → sobreescribe con los valores específicos del entorno
3. `django-environ` detecta automáticamente el engine de base de datos por el prefijo de `DATABASE_URL`

---

## 9. Crear `docker-compose.yml`

Para levantar PostgreSQL en desarrollo/producción:

```yaml
services:
  db:
    image: docker.io/postgres:15
    container_name: django_db
    restart: always
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: app_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

> **Nota Podman:** Usa `docker.io/postgres:15` (con el registro explícito) para evitar errores de resolución de registro.

Levantar la base de datos:

```bash
# Docker
docker compose up -d

# Podman
podman-compose up -d
```

---

## 10. Migraciones y servidor

```bash
# Aplicar migraciones
uv run manage.py migrate

# (Opcional) Crear superusuario para el admin
uv run manage.py createsuperuser

# Iniciar servidor de desarrollo
uv run manage.py runserver
```

Visita: `http://127.0.0.1:8000/`

---

## 11. Herramientas de calidad de código

```bash
# Linter
ruff check .
ruff check . --fix      # auto-fix

# Formatter
black .

# Type checking
mypy .
```

### Flujo recomendado antes de cada commit

```bash
ruff check . --fix && black . && mypy .
```

---

## 12. Cambiar de entorno

Solo edita `.env`:

```env
ENV=prod   # ← dev | prod
```

---

## Estructura final del proyecto

```
NAME_PROJECT/
├── examples env/
│   ├── .env.example        # Plantilla de .env
│   ├── .env.dev.example    # Plantilla de .env.dev
│   └── .env.prod.example   # Plantilla de .env.prod
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── .env                    # Entorno activo — NO subir a git
├── .env.dev                # Config desarrollo — NO subir a git
├── .env.prod               # Config producción — NO subir a git
├── .gitignore
├── docker-compose.yml
├── manage.py
├── pyproject.toml
└── uv.lock
```

---

## Referencia rápida de comandos

| Comando | Descripción |
|---|---|
| `uv add <pkg>` | Agregar dependencia |
| `uv sync` | Instalar dependencias del `uv.lock` |
| `uv run manage.py migrate` | Aplicar migraciones |
| `uv run manage.py createsuperuser` | Crear superusuario |
| `uv run manage.py runserver` | Iniciar servidor |
| `docker compose up -d` | Levantar PostgreSQL |
| `docker compose down` | Detener contenedores |
| `ruff check . --fix && black . && mypy .` | Pipeline de calidad |
