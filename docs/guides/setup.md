# Guía de Instalación y Configuración (Getting Started)

Sigue estos pasos para levantar tu entorno de desarrollo local en menos de 5 minutos.

## 1. Prerrequisitos Técnicos

Antes de clonar el repositorio, asegúrate de tener instaladas las siguientes herramientas en tu sistema (Windows, Mac o Linux):

|**Herramienta**|**Versión Mínima**|**Uso**|**Instalación Recomendada**|
|---|---|---|---|
|**Python**|`3.12+`|Lenguaje base|[python.org](https://www.python.org/)|
|**Docker**|`24.0+`|Infraestructura (DB)|Docker Desktop / OrbStack|
|**uv**|`Latest`|Gestor de Paquetes|`curl -LsSf https://astral.sh/uv/install.sh`|
|**Just**|`Latest`|Ejecutor de Comandos|[Ver guía](https://github.com/casey/just) (ej: `brew install just`)|

## 2. Configuración del Entorno

1. **Clonar el Repositorio:**

    ```bash
    git clone https://github.com/gapc87/industrial-data-harmonizer.git
    cd industrial-data-harmonizer
    ```

2. **Configurar Variables de Entorno:**

    El proyecto sigue la metodología _12-Factor App_. Utilizamos un comando automatizado para generar el archivo de configuración y las claves de seguridad.

    ```bash
    just setup-env
    ```

    > **Nota:** Este comando copia `.env.example` a `.env` y genera automáticamente una `SECRET_KEY` segura.

3. **Instalar Dependencias (La Magia de `uv`):**

    En lugar de crear venvs manualmente y esperar minutos con pip, ejecuta:

    ```bash
    just install
    # Equivale a: uv sync
    ```

    Esto creará el entorno virtual (`.venv`) e instalará todas las dependencias (prod + dev) en segundos.


## 3. Tu Primer Despliegue Local

Utilizamos **Just** para abstraer la complejidad de Docker. Levanta la infraestructura (PostgreSQL) y la API con un solo comando:

```bash
just up
```

Verás los logs de la API indicando que el servidor está listo.

Puedes verificar que todo funciona accediendo a la documentación interactiva:

**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

Para detener el entorno:

```bash
just down
```

## 4. Catálogo Completo de Comandos (Justfile)

Para facilitar el desarrollo, el proyecto incluye un catálogo de comandos estandarizados accesibles mediante `just`.

### Gestión del Entorno
* `just install`: Instala todas las dependencias del proyecto (dev + prod) usando `uv`.
* `just setup-env`: Crea el archivo `.env` inicial si no existe.

### Desarrollo y Ejecución
* `just up`: Levanta todo el stack (API + PostgreSQL) en Docker.
* `just up-dev`: **Recomendado.** Levanta stack + **pgAdmin** en [http://localhost:5050](http://localhost:5050).
* `just down`: Detiene y elimina los contenedores.
* `just run`: Ejecuta el servidor API localmente con *hot-reload* (requiere DB corriendo).
* `just logs`: Muestra los logs de los contenedores en tiempo real.

### Calidad y Testing
* `just test`: Ejecuta la suite completa de tests (Unitarios + Integración).
* `just lint`: Ejecuta auditoría de código con **Ruff** (formato y estilo) y **MyPy** (tipado estricto).
* `just typecheck`: Ejecuta solo la verificación de tipos con MyPy.

### Base de Datos
* `just db-migrate`: Aplica las migraciones pendientes con Alembic.
* `just db-revision "mensaje"`: Genera un nuevo archivo de migración detectando cambios en los modelos.

### Documentación
* `just docs-serve`: Levanta este sitio de documentación en local (`http://localhost:8000`).
* `just docs-build`: Genera la versión estática del sitio en `site/`.
* `just docs-export`: Exporta la especificación OpenAPI (`openapi.json`).

## 5. Seguridad y mTLS

El proyecto soporta autenticación mediante **mTLS (Mutual TLS)** para la comunicación segura entre el Edge y el Cloud.

### Generación de Certificados

Para pruebas locales, puedes generar una CA (Authoridad de Certificación) y certificados de cliente/servidor autofirmados usando el script de utilidad:

```bash
uv run scripts/generate_test_certs.py
```

Esto creará la carpeta `certs/` en la raíz del proyecto con:
*   `ca.crt`: Certificado de la CA.
*   `server.crt` / `server.key`: Para el servidor (API).
*   `client.crt` / `client.key`: Para el cliente (simulando un Gateway).

### Ejecutar con mTLS Habilitado

Para levantar el servidor forzando la validación de certificados de cliente:

```bash
just run-mtls
```

Esto ejecutará Uvicorn con `ssl_cert_reqs=2` (requerido). Puedes probar la conexión usando `curl`:

```bash
curl -v --cert certs/client.crt --key certs/client.key --cacert certs/ca.crt https://localhost:8000/health
```
