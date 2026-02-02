# Stack Tecnológico ("La Caja de Herramientas")

La selección tecnológica para el proyecto **IDH** prioriza tres pilares: **Rendimiento Asíncrono** (para no bloquear la ingesta masiva de datos), **Tipado Estricto** (para evitar errores en tiempo de ejecución) e **Interoperabilidad Universal** (para hablar tanto con PLCs modernos como con SAP legacy).

## 1. Núcleo y Gestión del Entorno

### Lenguaje: Python 3.12+
Se selecciona esta versión por sus mejoras significativas en el *Event Loop* de `asyncio` y su soporte avanzado de *Type Hints* y *Generics*.

### Gestor de Paquetes: `uv` (Astral)
**Innovación:** Sustituimos herramientas tradicionales (`pip`, `poetry`) por **`uv`**, un gestor escrito en Rust. Garantiza tiempos de instalación instantáneos y resolución determinista de dependencias, eliminando discrepancias entre desarrollo y producción.

## 2. API y Capa de Servicio

### Framework: FastAPI
*   **Rol:** Exposición de la API REST y gestión de Webhooks.
*   **Ventaja:** Generación automática de documentación **OpenAPI (Swagger UI)**, permitiendo que los equipos de IT de los partners prueben la integración sin nuestra intervención.

### Validación: Pydantic V2
*   **Rol:** Validación estricta de datos en la frontera del sistema.
*   **Implementación:** El núcleo de validación está escrito en Rust, ofreciendo un rendimiento superior en la serialización de grandes volúmenes de JSON.

## 3. Integración SAP y Conectividad Híbrida

Para soportar la estrategia de "Conectividad Universal" (OData + IDocs), se incorporan librerías específicas de integración:

*   **Cliente HTTP: `httpx` (Async)**
    *   **Uso:** Consultas *Pull* a servicios **OData** de SAP.
    *   **Justificación:** A diferencia de `requests` (que es bloqueante), `httpx` es nativamente asíncrono. Esto permite que el sistema consulte precios o stock a SAP sin detener la ingesta de telemetría de las máquinas.

*   **Parsing XML: `xmltodict` + `defusedxml`**
    *   **Uso:** Procesamiento de **IDocs** recibidos vía Webhook.
    *   **Estrategia:** Se utiliza `defusedxml` para proteger el sistema contra ataques de inyección XML (XXE), y `xmltodict` para convertir la estructura jerárquica del IDoc en un diccionario Python estándar, facilitando su almacenamiento como JSON.

*   **Planificador: `APScheduler`**
    *   **Uso:** Orquestación de tareas de fondo (*Cron Jobs*).
    *   **Caso:** Ejecución periódica (ej: cada 10 min) de la sincronización de Maestros de Artículos desde SAP.

## 4. Persistencia y Datos

### Base de Datos: PostgreSQL 15.15+
**Motor:** Seleccionado por su soporte robusto de datos híbridos (Datos Relacionales SQL + Documentos JSONB) en el mismo motor. Es fundamental para el patrón **Medallion**.

### ORM: SQLAlchemy 2.0 (Async)
**Patrón:** Uso del patrón *Data Mapper* asíncrono para desacoplar las tablas SQL de los objetos de dominio. Soporta tipado estricto nativo.

### Migraciones: Alembic
**Rol:** Gestión del ciclo de vida del esquema de base de datos (*Infrastructure as Code*).

## 5. Estándares de Calidad (Code Quality)

El proyecto impone estándares estrictos mediante análisis estático automatizado:

### Tipado Estático: MyPy (`--strict`)
Todo el código debe estar tipado. Previene errores de tipo (ej: `NoneType`) antes de ejecutar el código.

### Linter & Formatter: Ruff
Herramienta "todo en uno" (escrita en Rust) que reemplaza a Flake8, Black e Isort. Asegura el cumplimiento de **PEP-8** y optimiza importaciones en milisegundos.

### Auditoría Arquitectónica: `just check-architecture`
Se utiliza herramental de linting de importaciones (como `Import-Linter`) para asegurar que las dependencias entre `core`, `features` e `infrastructure` respeten los límites de la Arquitectura Hexagonal.

## 6. Experiencia de Desarrollo (DX)

### Contenerización: Docker & Docker Compose
Réplica exacta del entorno de producción en local para todos los desarrolladores.

### Task Runner: Justfile (`Just`)
**Modernización:** Se utiliza **Just** como ejecutor de comandos estandarizado. Abstrae la complejidad operativa (ej: `just up`, `just test`).

### Testing: Pytest + Testcontainers
Uso de contenedores efímeros para pruebas de integración reales contra una base de datos PostgreSQL viva, evitando mocks frágiles.

## 7. Gestión de Configuración

### Herramienta: Pydantic Settings
*   **Enfoque:** Centralización de todas las variables de entorno (`.env`) en clases de configuración estrictamente tipadas.
*   **Validación al Arranque ("Fail Fast"):** El sistema valida la existencia y el formato correcto de todas las credenciales críticas durante la inicialización.
