# Estrategia de Seguridad y Control de Acceso

El sistema implementa un modelo de seguridad de **"Confianza Cero" (Zero Trust)** con una estricta segregación de funciones (Humans vs Machines).

## 1. Matriz de Roles y Permisos (RBAC Interno)

Para los empleados, el sistema gestiona la autenticación mediante **JWT (JSON Web Tokens)**.

| Rol Técnico | Caso de Uso | Permisos (Scopes) |
| --- | --- | --- |
| `PLANT_OPERATOR` | Operario a pie de máquina | `orders:read`, `telemetry:write` |
| `QUALITY_AUDITOR` | Inspector de calidad | `batch:block`, `traceability:read` |
| `COST_CONTROLLER` | Controller Financiero | `reports:read`, `cost:read` |
| `PRODUCT_ENGINEER` | I+D+i | `specs:write` |
| `SYSTEM_ADMIN` | IT | `*` |

Para la recolección de datos automática (Edge Collectors), se utiliza un modelo híbrido de **Confianza Cero**:

*   **Nivel de Transporte (mTLS):** Autenticación mutua mediante certificados de cliente para asegurar que solo los Gateways autorizados pueden conectarse.
*   **Nivel de Aplicación (OAuth2):** Client Credentials Flow con rotación de secretos para obtener Scopes dinámicos.
*   **Seguridad:** Los dispositivos tienen un scope restringido de **Solo Escritura** (`telemetry:push`). Si se hackea una máquina, no pueden leer datos sensibles del servidor.

## 3. Estrategia de Red: Zero-Inbound

Para simplificar el despliegue en plantas con firewalls restrictivos, se aplica la política **Outbound-Only**:

*   **Puerto 443:** Toda la comunicación se inicia desde la planta hacia el servidor central. No es necesario abrir puertos de entrada en la red industrial (OT).
*   **Cifrado:** Implementación mandatorio de **TLS 1.3** en tránsito y **AES-256** para datos sensibles en reposo.

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

## 6. Acceso Físico y Plant Authentication
Se soporta el mapeo de identidades para **NFC Login** integrado con el sistema de control de planta, permitiendo que los operarios se autentiquen en las tablets industriales con su credencial física.
