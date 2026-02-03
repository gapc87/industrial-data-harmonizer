# ADR 001: Usar Monolito Modular

## Estado

Aceptado

## Contexto

El proyecto IDH necesita integrar múltiples dominios de negocio (ingesta de telemetría, producción, calidad, logística) y comunicarse con sistemas externos (SAP, PLCs).

Se evaluaron las siguientes opciones arquitectónicas:
- Microservicios distribuidos
- Monolito tradicional
- Monolito modular

El proyecto está mantenido por un solo desarrollador, por lo que la complejidad operativa de microservicios (service mesh, orquestación, trazabilidad distribuida) no se justifica.

Adoptamos una arquitectura de **Monolito Modular** organizado mediante un modelo **Híbrido de Core y Features**.

El sistema se despliega como una única unidad, pero está organizado físicamente en carpetas `core/` (lógica transversal) y `features/` (contextos de negocio aislados) que pueden extraerse a microservicios en el futuro si la escala lo requiere.

## Alternativas Consideradas

### Alternativa 1: Microservicios
- **Pros:** Escalado independiente, despliegue aislado, tecnologías heterogéneas
- **Contras:** Complejidad operativa alta, latencia de red, debugging difícil
- **Razón de rechazo:** Overhead operativo no justificado para el tamaño del equipo

### Alternativa 2: Monolito Tradicional
- **Pros:** Simplicidad, despliegue único
- **Contras:** Acoplamiento alto, difícil de escalar, código espagueti
- **Razón de rechazo:** No permite evolución futura sin refactoring masivo

## Consecuencias

### Positivas
- Simplicidad operativa: un solo contenedor a desplegar
- Baja latencia: comunicación en memoria entre módulos
- Preparado para el futuro: límites claros facilitan extracción a microservicios

### Negativas
- Todo el sistema escala junto (no escalado granular)
- Un bug crítico puede afectar a todos los módulos

## Referencias

- [Modular Monolith: A Primer (Kamil Grzybek)](https://www.kamilgrzybek.com/blog/posts/modular-monolith-primer)
- ARCHITECTURE_DESIGN.md - Sección 1.2
