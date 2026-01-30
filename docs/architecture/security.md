# Estrategia de Seguridad y Control de Acceso

El sistema implementa un modelo de seguridad de **"Confianza Cero" (Zero Trust)** con una estricta segregación de funciones (Humans vs Machines).

## 1. Matriz de Roles y Permisos (RBAC Interno)

Para los empleados, el sistema gestiona la autenticación mediante **JWT (JSON Web Tokens)**.

| Rol Técnico | Caso de Uso | Permisos (Scopes) |
| --- | --- | --- |
| `PLANT_OPERATOR` | Operario a pie de máquina | `orders:read`, `telemetry:write` |
| `QUALITY_AUDITOR` | Inspector de calidad | `batch:block`, `traceability:read` |
| `PRODUCT_ENGINEER` | I+D+i | `specs:write` |
| `SYSTEM_ADMIN` | IT | `*` |

## 2. Autenticación M2M (Machine-to-Machine)

Para la recolección de datos automática (Edge Collectors), se utiliza **OAuth2 Client Credentials Flow**.

* **Seguridad:** Los dispositivos tienen un scope restringido de **Solo Escritura** (`telemetry:push`). Si se hackea una máquina, no pueden leer datos sensibles del servidor.

## 3. Estrategia Multitenencia (B2B)

El sistema permite extender la visibilidad a Partners externos:

* **Aislamiento Lógico:** Un cliente externo autenticado solo puede consultar *sus* propias órdenes.
* **Mecanismo:** Filtro SQL automático (`WHERE client_id = :current_partner`) inyectado por el middleware de seguridad.

## 4. Auditoría (Compliance)

* **Logging de Seguridad:** Cada acción crítica de modificación genera un registro inmutable (Quién, Cuándo, Qué).

## 5. Protección de Infraestructura

* **Rate Limiting:** Límites de consumo para evitar "Vecinos Ruidosos".
    * Partners: Límites estrictos (ej: 100 req/min).
    * Sensores: Límites altos (ej: 1000 req/min) pero con mecanismos de frenado.
