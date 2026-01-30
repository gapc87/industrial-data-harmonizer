# ADR 002: Estrategia de Implementación del Worker Asíncrono

## Estado

Aceptado

## Contexto

El diseño arquitectónico del IDH contempla un `Worker` dedicado para procesar tareas pesadas (ingesta masiva, ETL, comunicación con SAP) fuera del ciclo de vida de la petición HTTP.

Sin embargo, en la fase actual de "Scaffolding" e implementación inicial:
1.  La complejidad operativa de gestionar múltiples contenedores dificulta el desarrollo.
2.  El volumen de datos en desarrollo no justifica la separación física de procesos aún.
3.  Desplegar un servicio vacío añade ruido y consumo de recursos innecesario.

## Decisión

Adoptamos una **Estrategia de Implementación Diferida (Phased Rollout)** para el `idh-worker`:

1.  **Fase 1 (MVP/Desarrollo):** El "Worker" se ejecutará como hilos background (`asyncio.create_task` o `APScheduler`) **dentro** del proceso `idh-api`.
    *   Comparten el mismo contenedor y memoria.
    *   Simplifica el despliegue (`just up` solo levanta API y DB).

2.  **Fase 2 (Producción/Carga):** Se extraerá el código del scheduler/worker a su propio punto de entrada (`src/idh/worker.py`) y se habilitará el servicio dedicado en `docker-compose.yml`.
    *   Se hará cuando se implemente la integración real con SAP o cuando la carga de ingesta impacte la latencia de la API.

## Consecuencias

### Positivas
- **Velocidad de Desarrollo:** Menos "piezas móviles" que gestionar y depurar ahora mismo.
- **Simplicidad:** Un solo comando para arrancar todo el stack lógico.
- **Eficiencia:** Menor consumo de RAM en entornos locales.

### Negativas
- **Riesgo de Bloqueo:** Si una tarea en background bloquea el *Event Loop* (CPU bound), la API dejará de responder. (Mitigable usando `run_in_executor` o threads).
- **Acoplamiento Temporal:** La documentación (`OPS.md`) menciona un componente que "aún no existe" físicamente.

## Plan de Acción
- Mantener `OPS.md` describiendo la arquitectura final (Worker separado).
- Implementar lógica de negocio agnóstica de dónde se ejecuta (desacoplada).
- Crear ticket en backlog: "Extraer Worker a servicio dedicado".
