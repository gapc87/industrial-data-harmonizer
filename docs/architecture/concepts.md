# Conceptos Arquitectónicos y Visión

**Versión:** 2.0.0
**Enfoque:** Monolito Modular, Hexagonal & DDD con Edge Computing.

## 1. Visión General

El proyecto **Industrial Data Harmonizer (IDH)** es una plataforma de middleware diseñada para cerrar la brecha tecnológica entre la planta de producción (OT) y los sistemas de gestión corporativa (IT).

Su misión es orquestar la convergencia de datos industriales, recolectando telemetría de maquinaria en tiempo real de forma segura, normalizando dicha información mediante reglas de negocio complejas, y exponiéndola a los departamentos de Producción, Calidad y Logística.

## 2. Estilo Arquitectónico: Monolito Modular

Se ha optado por un **Monolito Modular** en lugar de microservicios distribuidos.

* **Definición:** El sistema se despliega como una única unidad (un contenedor), pero internamente está estrictamente dividido en módulos funcionales (`Contexto de Ingesta`, `Contexto de Producción`, `Contexto de Calidad`).

* **Justificación:** Minimiza la complejidad operativa y la latencia de red, permitiendo a su vez la futura extracción de módulos a microservicios independientes si la escala lo requiere.

## 3. Patrón Estructural: Arquitectura Hexagonal

Para desacoplar la lógica de negocio de las tecnologías externas, se implementa estrictamente la Arquitectura Hexagonal (Ports & Adapters).

* **Núcleo (Dominio):** Contiene la lógica pura de negocio (Reglas DDD). No tiene dependencias externas.

* **Puertos y Adaptadores:** La comunicación con el mundo exterior (Base de datos PostgreSQL, API REST, SAP) se realiza a través de interfaces (Puertos) e implementaciones (Adaptadores).

## 4. Metodología de Diseño (DDD Táctico)

El núcleo del sistema se ha modelado siguiendo los patrones tácticos de **Domain-Driven Design (DDD)**.

### Lenguaje Ubicuo (*Ubiquitous Language*)

Se ha establecido un vocabulario estricto compartido entre el equipo de desarrollo y los responsables de negocio. Términos como `Batch`, `Waste` o `ProductionOrder` son ciudadanos de primera clase en el código.

### Patrones Implementados

- **Entidades:** Objetos con identidad única (`ProductionOrder`).
- **Value Objects:** Objetos inmutables definidos por atributos (`Humidity`, `Temperature`).
- **Agregados:** Unidades de consistencia transaccional.

## 5. Estrategia de Segregación (CQRS Simplificado)

Reconociendo que los patrones de acceso a datos difieren entre la escritura (transaccional) y la lectura (analítica), se aplica una separación lógica de responsabilidades.

* **Comandos (Writes):** Pasan obligatoriamente por el Modelo de Dominio.
* **Consultas (Reads):** Consultan proyecciones optimizadas (DTOs) directamente desde la base de datos (Esquema `public`).

## 6. Stack Tecnológico

La selección tecnológica prioriza **Rendimiento Asíncrono**, **Tipado Estricto** e **Interoperabilidad**.

* **Lenguaje:** Python 3.12+
* **Gestor:** `uv` (Rust-based)
* **API:** FastAPI
* **BBDD:** PostgreSQL 15 + SQLAlchemy 2.0 (Async) + Alembic
* **Calidad:** MyPy (`--strict`), Ruff
