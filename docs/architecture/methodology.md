# Metodología de Diseño y Desarrollo

La complejidad inherente a los procesos industriales (trazabilidad, gestión de mermas, control de calidad) requiere un enfoque que priorice la lógica de negocio sobre la infraestructura tecnológica. Para lograrlo, el proyecto adopta metodologías de diseño que alinean el software con la realidad operativa de la planta.

## 1. Domain-Driven Design (DDD) Táctico

El núcleo del sistema se ha modelado siguiendo los patrones tácticos de **DDD**. Esto asegura que el código sea una representación fiel del lenguaje y las reglas utilizadas por los expertos de planta, reduciendo la brecha semántica entre "lo que dice el código" y "lo que hace la fábrica".

### A. Lenguaje Ubicuo (*Ubiquitous Language*)

Se ha establecido un vocabulario estricto compartido entre el equipo de desarrollo y los responsables de negocio. Este lenguaje se utiliza tanto en las reuniones como en el nombre de las clases y métodos.

*   **Ejemplo:** No se utilizan términos técnicos genéricos como `update_record` o `delete_row`. Se utilizan términos del dominio como `reconcile_inventory` (Conciliar inventario), `quarantine_batch` (Poner lote en cuarentena) o `declare_waste` (Declarar merma).

### B. Patrones Tácticos Implementados

El modelo de dominio (capa central del hexágono) se estructura mediante los siguientes bloques de construcción:

*   **Entidades (*Entities*):** Objetos definidos por su identidad única y ciclo de vida continuo.
    *   *Caso:* Una `ProductionOrder` es una entidad. Aunque cambie su estado de "Planificada" a "Finalizada", su identidad (`ID: ORD-2024-X`) permanece inmutable.

*   **Objetos de Valor (*Value Objects*):** Objetos inmutables definidos por sus atributos, utilizados para modelar medidas y características.
    *   *Caso:* `Humidity(value=12, unit=%)`. Si la humedad cambia, se crea una nueva instancia. Esto previene errores de referencia y efectos secundarios (*Side Effects*) al pasar datos entre funciones.

*   **Agregados (*Aggregates*) y Raíz (*Root*):**
    *   Grupo de objetos que se tratan como una unidad de consistencia transaccional.
    *   *Regla:* El acceso externo está restringido a la Raíz del Agregado.
    *   *Ejemplo:* `ProductionOrder` es la raíz. No se puede modificar una `LineItem` (Línea de detalle) directamente; se debe invocar `order.add_production_report(...)`. Esto garantiza que la Orden siempre valide sus invariantes (ej: "No reportar más cantidad de la planificada") antes de aceptar el cambio.

## 2. Test-Driven Development (TDD)

Para garantizar la fiabilidad absoluta en los cálculos críticos (ej: costes, mermas), se aplica la disciplina de **TDD** en el desarrollo de la Capa de Dominio.

*   **Enfoque "Inside-Out":** Se escriben primero los tests para las reglas de negocio puras (Dominio), sin dependencias de base de datos ni API.

*   **Ciclo Red-Green-Refactor:**
    1.  **RED:** Se crea un test que falla describiendo una regla de negocio (ej: `test_waste_calculation_should_alert_if_exceeds_threshold`).
    2.  **GREEN:** Se implementa la lógica mínima necesaria en la Entidad o Servicio de Dominio para pasar el test.
    3.  **REFACTOR:** Se optimiza el código asegurando que sigue siendo legible y eficiente.

*   **Beneficio:** Esto genera una "documentación viva" del sistema y permite refactorizar la lógica compleja con la seguridad de que los tests detectarán cualquier regresión matemática instantáneamente.

## 3. Segregación de Responsabilidades (CQRS Simplificado)

Reconociendo que los patrones de acceso a datos difieren entre la escritura (transaccional) y la lectura (analítica), se aplica una separación lógica de responsabilidades.

*   **Comandos (Writes - The Domain):**
    *   Modifican el estado del sistema (`IngestarLectura`, `CerrarOrden`).
    *   Pasan obligatoriamente por el Modelo de Dominio (DDD) para garantizar la integridad y el cumplimiento de reglas.

*   **Consultas (Reads - The Projection):**
    *   Recuperan datos (`ObtenerDashboard`, `ListarOrdenes`).
    *   Evitan la complejidad del Dominio y consultan proyecciones optimizadas (DTOs) directamente desde la base de datos (Esquema `public`).
    *   *Justificación:* Los dashboards de gerencia necesitan velocidad de lectura, no validación de reglas de negocio.

## 4. Catálogo de Patrones de Diseño

Además de la estructura macro (Hexagonal), se aplican patrones de diseño específicos para resolver problemas recurrentes de integración industrial:

*   **Patrón Estrategia (*Strategy Pattern*) para Ingesta:**
    *   **Problema:** La heterogeneidad de fuentes (JSON de SAP, CSV de máquinas, XML legacy).
    *   **Solución:** Se define una interfaz común `DataSourceStrategy`. El "Orquestador" desconoce el formato origen y delega la lectura a la estrategia concreta.

*   **Patrón *Circuit Breaker* (Cortacircuitos):**
    *   **Problema:** Las caídas o latencias extremas en el ERP corporativo.
    *   **Solución:** Si SAP falla X veces consecutivas, el sistema deja de enviar peticiones temporalmente.

*   **Patrón Observador (*Observer*) vía Eventos de Dominio:**
    *   **Uso:** Desacoplamiento de efectos secundarios. Cuando una orden se completa, el dominio emite un evento `OrderCompleted` y múltiples escuchas reaccionan independientemente.
