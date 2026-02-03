# Guía de Despliegue y Configuración - IDH

**Sistema:** Industrial Data Harmonizer (IDH)
**Estado:** Producción

---

## 1. Topología y Mapa de Componentes

Este sistema opera en una arquitectura híbrida **Edge-Cloud**. Es crucial entender qué componentes corren en el servidor central (IT) y cuáles en la planta física (OT).

### 1.1. Arquitectura de Despliegue (Docker Compose)

En el servidor central, el sistema se orquesta mediante **Docker Compose**. La unidad de despliegue consta de 3 servicios principales interconectados en una red privada virtual (`idh-network`).

|**Servicio**|**Nombre Contenedor**|**Imagen Base**|**Puerto Interno**|**Puerto Expuesto (Host)**|**Volúmenes (Persistencia)**|
|---|---|---|---|---|---|
|**API**|`idh-api`|`python:3.12-slim`|`8000`|`8000` (o Reverse Proxy)|N/A (Stateless)|
|**Worker**|`idh-worker`|`python:3.12-slim`|N/A|N/A|N/A (Stateless)|
|**Database**|`idh-db`|`postgres:15-alpine`|`5432`|`5432` (Solo localhost)|`pg_data:/var/lib/postgresql/data`|

### 1.2. Ubicación Física y Red

- **Zona IT (Servidor Central):** Aloja el Monolito (`API` + `Worker` + `DB`). Debe tener visibilidad de red hacia SAP (Puerto 443/RFC) y ser accesible vía HTTPS desde los _Edge Collectors_.

- **Zona OT (Planta):** Aloja los scripts _Edge Collector_ (en Raspberry Pi / PC Industrial). Estos **NO** son contenedores Docker gestionados centralmente; son agentes independientes que envían datos hacia afuera (Outbound).


### 1.3. Dependencias Críticas

Si estos servicios externos fallan, el IDH operará en modo degradado:

- **SAP S/4HANA:** Crítico para validación de órdenes. Si cae, funciona el _Circuit Breaker_.

- **DNS Corporativo:** Necesario para resolver `sap.internal.org`.

- **Servidor NTP:** Vital para sincronizar los _timestamps_ de los logs entre máquinas y servidor.


---

## 2. Gestión de Configuración y Secretos

El sistema sigue la metodología **12-Factor App**. **NO existe configuración "hardcodeada"** en el código. Todo se inyecta mediante variables de entorno al arrancar el contenedor.

### 2.1. Archivo `.env` (Producción)

En el servidor de producción, debe existir un archivo `.env` en la raíz del despliegue (`/opt/idh/.env`). Este archivo **JAMÁS** se sube al repositorio Git.

> **⚠️ Advertencia de Seguridad:** Si cambias una variable en el `.env`, debes reiniciar los contenedores (`just restart`) para que surta efecto.

### 2.2. Variables Críticas (Tabla de Referencia)

|**Variable**|**Requerido**|**Descripción / Ejemplo**|
|---|---|---|
|**CONFIGURACIÓN GENERAL**|||
|`PROJECT_NAME`|✅|Nombre del proyecto (ej: "Industrial Data Harmonizer").|
|`API_V1_STR`|✅|Prefijo de versión (ej: `/api/v1`).|
|`BACKEND_CORS_ORIGINS`|✅|Orígenes permitidos CORS (ej: `["http://localhost:3000"]`).|
|`ACCESS_TOKEN_EXPIRE_MINUTES`|✅|Tiempo de vida del token JWT (ej: `60`).|
|**INFRAESTRUCTURA**|||
|`ENV_STATE`|✅|`prod` (Activa el modo estricto de seguridad JSON logs).|
|`LOG_LEVEL`|✅|`INFO` (Usar `DEBUG` solo temporalmente para diagnosis).|
|`SECRET_KEY`|✅|Cadena aleatoria larga para firmar JWTs (openssl rand -hex 32).|
|**BASE DE DATOS**|||
|`POSTGRES_SERVER`|✅|Nombre del servicio docker: `idh-db` o `localhost`.|
|`POSTGRES_PORT`|✅|`5432`|
|`POSTGRES_USER`|✅|Usuario PostgreSQL (ej: `idh_admin`).|
|`POSTGRES_PASSWORD`|✅|**SECRETO.** Contraseña robusta del usuario DB.|
|`POSTGRES_DB`|✅|`idh_production`.|
|**INTEGRACIÓN SAP**|||
|`SAP_API_BASE_URL`|✅|Endpoint base de SAP (ej: `https://sap-gw.org/sap/opu/odata`).|
|`SAP_AUTH_USER`|❌|Usuario técnico para Basic Auth (Si aplica).|
|`SAP_AUTH_PASS`|❌|Contraseña técnica SAP.|
|`SAP_TIMEOUT_SECONDS`|✅|Segundos antes de abrir el _Circuit Breaker_ (Default: `5.0`).|

### 2.3. Validación al Arranque (Fail-Fast)

El sistema utiliza `Pydantic Settings` para validar estas variables al inicio.

- **Si falta una variable obligatoria:** El contenedor `idh-api` se detendrá inmediatamente y arrojará un error claro en los logs:

    ```
    ValidationError: 1 validation error for Settings
    DB_PASSWORD
      field required (type=value_error.missing)
    ```

- **Acción:** Revisa el archivo `.env` y asegúrate de que la variable existe y no tiene espacios en blanco extra.


### 2.4. Rotación de Credenciales

Si se compromete una contraseña (SAP o DB) o la `SECRET_KEY`:

1. Actualizar el valor en el sistema origen (Postgres/SAP).

2. Editar el archivo `.env` en el servidor.

3. Ejecutar `just down && just up` para recrear los contenedores con los nuevos secretos.

4. (Opcional) Si rotas `SECRET_KEY`, todos los usuarios deberán loguearse de nuevo.


---

## 3. Despliegue y Ciclo de Vida

Procedimientos estándar para desplegar nuevas versiones, aplicar parches y gestionar la base de datos en el entorno de producción.

### 3.1. Prerrequisitos del Servidor

Antes de cualquier despliegue, verifica:

- Docker Daemon está corriendo: `docker info`.

- Conectividad con el Container Registry (si usas imágenes privadas): `docker login`.

- Espacio en disco suficiente: `df -h`. (PostgreSQL requiere espacio libre para WAL logs).


### 3.2. Procedimiento de Actualización Estándar (Zero-Downtime Relativo)

Para desplegar una nueva versión del código (`latest`) sin detener el servicio más de unos segundos:

1. **Descargar imágenes:**

    ```bash
    docker-compose pull
    ```

2. **Aplicar Migraciones de Base de Datos (CRÍTICO):**

    Antes de reiniciar el código, asegura que la BBDD tiene la estructura nueva.

    ```bash
    # Usando Just (Recomendado)
    just db-migrate

    # O manual con Docker
    docker-compose run --rm api alembic upgrade head
    ```

3. **Reiniciar Contenedores:**

    Docker recreará solo los contenedores que han cambiado.

    ```bash
    docker-compose up -d
    ```

1. **Verificar Salud:**

    ```bash
    docker-compose ps
    curl http://localhost:8000/api/v1/health
    ```


### 3.3. Procedimiento de "Instalación Limpia" (Cold Deploy)

Úsalo solo si el entorno está corrompido o es la primera instalación. **⚠️ Esto implica tiempo de inactividad.**

```bash
# 1. Detener todo
just down

# 2. Limpiar volúmenes huerfanos (Opcional - Cuidado con la BBDD)
docker system prune -f

# 3. Arrancar de cero
just up
just db-migrate
```

### 3.4. Rollback (Vuelta Atrás)

Si la nueva versión falla (ej: error 500 continuo):

1. Edita el `docker-compose.yml` y cambia el tag de imagen a la versión anterior (ej: `v1.2.0`).

2. Ejecuta `docker-compose up -d`.

3. **Nota sobre BBDD:** Si la migración de BBDD no es retrocompatible, deberás ejecutar `alembic downgrade -1`. _Consulta al equipo de desarrollo antes de hacer esto._
