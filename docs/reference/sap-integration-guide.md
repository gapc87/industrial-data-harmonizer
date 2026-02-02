# Guía de Integración SAP (Partner Guide)

Este documento define el **Contrato de Interfaz** para el equipo de integración SAP. Aquí se especifican los formatos esperados, códigos de error y políticas de reintento para integrar SAP S/4HANA (o SAP BTP) con el Industrial Data Harmonizer (IDH).

## 1. Endpoints de Ingesta

### A. Órdenes de Producción
*   **Método:** `POST`
*   **URL:** `/api/v1/ingest/orders`
*   **Auth:** Bearer Token (OAuth2)

#### Formato del Payload (JSON Array)
Aceptamos lotes (arrays) de hasta 100 órdenes por petición.

```json
[
  {
    "external_order_id": "ORD-10023456",  // Obligatorio. ID único SAP.
    "material_code": "MAT-500-A",         // Obligatorio.
    "quantity_target": 5000.0,            // Obligatorio.
    "unit": "KG",
    "delivery_date": "2026-06-15",
    "metadata": {                         // Opcional. Campos extra.
       "sap_plant": "ES01",
       "priority": "HIGH"
    }
  }
]
```

## 2. Códigos de Respuesta HTTP

El sistema IDH utiliza códigos HTTP semánticos. Su middleware debe reaccionar acorde a ellos:

| Código | Estado | Significado para SAP | Acción Requerida |
| :--- | :--- | :--- | :--- |
| **202** | `Accepted` | **Éxito Total.** El JSON ha sido guardado en disco (`raw_data`). | Marcar IDoc como enviado "OK". |
| **400** | `Bad Request` | **Error de Datos.** El JSON está mal formado o falta un campo obligatorio (ej: `external_order_id`). | **NO REINTENTAR.** El error es permanente. Alertar a funcional SAP. |
| **401** | `Unauthorized` | **Token Inválido.** Credenciales caducadas o firma errónea. | Solicitar nuevo Token OAuth2. |
| **429** | `Too Many Requests` | **Freno.** Estás enviando demasiado rápido (>600 req/min). | **REINTENTAR (Backoff).** Esperar `Retry-After` segundos. |
| **5xx** | `Server Error` | **Fallo Interno.** Base de datos caída o bug. | **REINTENTAR.** Usar Exponential Backoff. |

## 3. Política de Reintentos (Circuit Breaker)

Para garantizar la estabilidad:

1.  **Timeouts:** Configure su cliente HTTP con un timeout de **5 segundos**. Si IDH no responde en 5s, aborte y reintente.
2.  **Backoff Exponencial:** Si recibe un error `500` o `503`, espere: 1s, 2s, 4s, 8s... antes de volver a intentar.
3.  **Idempotencia:** IDH es idempotente. Puede enviar la misma orden (`ORD-10023456`) múltiples veces sin miedo a duplicados. Si ya existe, le devolveremos `200 OK`.

## 4. Autenticación (OAuth2 Client Credentials)

Para obtener un token, realice una petición al endpoint de autenticación.

*   **URL:** `/api/v1/auth/token`
*   **Método:** `POST`
*   **Body (`application/x-www-form-urlencoded`):**
    *   `grant_type=client_credentials`
    *   `client_id=sap_integration_suite`
    *   `client_secret=*******`
    *   `scope=orders:ingest`

**Respuesta Exitos:**
```json
{
  "access_token": "eyJhbGciOiJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```
Use este token en el Header `Authorization: Bearer <token>` para las peticiones de datos.
