# Calidad del Software y Cultura DevOps

Para garantizar la estabilidad operativa en un entorno de producción industrial 24/7, el proyecto prioriza la detección temprana de errores ("Shift-Left Testing").

## 1. La Pirámide de Testing

Siguiendo los principios de la Arquitectura Hexagonal, la estrategia de pruebas se estructura en niveles:

### A. Tests Unitarios (Capa de Dominio)
* **Objetivo:** Verificar Reglas de Negocio.
* **Tecnología:** TDD puro, en memoria. Sin mocks pesados.

### B. Tests de Integración (Capa de Infraestructura)
* **Objetivo:** Verificar Adaptadores (SQL, HTTP).
* **Tecnología:** **Testcontainers**. Base de datos PostgreSQL real efímera para cada test.

### C. Tests End-to-End (Capa de API)
* **Objetivo:** Verificar contratos OpenAPI y flujos completos.

## 2. Análisis Estático

* **Type Checking:** **MyPy** (`--strict`) para prevenir errores de tipo.
* **Linting:** **Ruff** para estilo y errores comunes.

## 3. Observabilidad

Un sistema ciego es un riesgo.

* **Structured Logging:** Logs en formato JSON (`{"level": "INFO", "correlation_id": "..."}`) para ingesta en ELK.
* **Tracing:** Correlation IDs que viajan por todas las capas del sistema.

## 4. Gestión de Ciclo de Vida (Graceful Shutdown)

El sistema maneja señales `SIGTERM` para permitir que las transacciones en vuelo terminen antes de apagar el contenedor, garantizando la consistencia ACID de los datos.
