# Justfile - Task Runner para IDH
# Documentación: https://github.com/casey/just
# Uso: just <comando>

set dotenv-load

# Variables por defecto
default_port := "8000"

# ============================================
# DESARROLLO LOCAL
# ============================================

# Configurar entorno inicial (crear .env desde ejemplo)
setup-env:
    @test -f .env && echo "⚠️ El archivo .env ya existe. No se ha modificado." || ( \
        cp .env.example .env && \
        echo "✅ Archivo .env creado." && \
        sed -i "s/change_this_secret_key_in_production_999999/`openssl rand -hex 32`/" .env && \
        echo "🔐 SECRET_KEY generada aleatoriamente." \
    )

# Instalar dependencias con uv
install:
    uv sync

# Ejecutar servidor en modo desarrollo (hot-reload)
run:
    uv run uvicorn idh.main:app --reload --host 0.0.0.0 --port {{default_port}}

# ============================================
# DOCKER
# ============================================

# Levantar infraestructura (DB + API)
up:
    docker compose up -d

# Levantar con pgAdmin para desarrollo
up-dev:
    docker compose --profile dev up -d

# Detener todos los servicios
down:
    docker compose down

# Reiniciar servicios (útil tras cambios en .env)
restart:
    docker compose down && docker compose up -d

# Ver logs de los contenedores
logs:
    docker compose logs -f

# Ver logs solo de la API
logs-api:
    docker compose logs -f idh-api

# Limpiar todo (incluyendo volúmenes - BORRA DATOS)
clean:
    docker compose down -v --remove-orphans
    docker system prune -f

# ============================================
# BASE DE DATOS
# ============================================

# Aplicar migraciones pendientes
db-migrate:
    uv run alembic upgrade head

# Crear nueva migración (requiere mensaje)
db-revision message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Ver estado actual de migraciones
db-status:
    uv run alembic current

# Revertir última migración
db-downgrade:
    uv run alembic downgrade -1

# ============================================
# CALIDAD DE CÓDIGO
# ============================================

# Ejecutar linter y formatear código
lint:
    uv run ruff check . --fix
    uv run ruff format .

# Solo verificar (sin modificar)
lint-check:
    uv run ruff check .
    uv run ruff format . --check

# Verificar tipos con MyPy
typecheck:
    uv run mypy src/

# Ejecutar todas las verificaciones de calidad
check: lint-check typecheck

# ============================================
# TESTING
# ============================================

# Ejecutar todos los tests
test:
    uv run pytest -v

# Ejecutar tests con cobertura
test-cov:
    uv run pytest --cov=src/idh --cov-report=html --cov-report=term-missing

# Ejecutar solo tests unitarios
test-unit:
    uv run pytest tests/unit -v

# Ejecutar solo tests de integración
test-integration:
    uv run pytest tests/integration -v

# ============================================
# BUILD & DEPLOY
# ============================================

# Construir imagen Docker
build:
    docker compose build

# Construir sin cache
build-fresh:
    docker compose build --no-cache

# ============================================
# PRE-COMMIT
# ============================================

# Instalar hooks de pre-commit
pre-commit-install:
    uv run pre-commit install --install-hooks

# Ejecutar todos los hooks manualmente
pre-commit-run:
    uv run pre-commit run --all-files

# Actualizar versiones de hooks
pre-commit-update:
    uv run pre-commit autoupdate

# ============================================
# DOCUMENTACIÓN
# ============================================

# Servir documentación localmente
docs-serve:
    uv run mkdocs serve

# Exportar esquema OpenAPI (requiere .env o variables de entorno)
docs-export:
    uv run scripts/export_openapi.py

# Construir documentación estática
docs-build:
    uv run scripts/export_openapi.py
    uv run mkdocs build
