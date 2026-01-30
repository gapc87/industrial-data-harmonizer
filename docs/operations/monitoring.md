# Monitorización y Observabilidad

El sistema emite señales vitales constantemente. No esperes a que un usuario se queje; vigila estos indicadores.

### 1. Health Checks (Endpoints de Estado)

La API expone endpoints públicos para balanceadores de carga y sistemas de monitoreo (Nagios/Datadog).

- **Liveness Probe:** `GET /api/v1/health`

    - **Uso:** ¿El proceso web está vivo?

    - **Respuesta:** `200 OK` `{"status": "ok"}`.

    - **Acción si falla:** Reiniciar el contenedor.

- **Readiness Probe:** `GET /api/v1/health/ready`

    - **Uso:** ¿El sistema funciona funcionalmente? (Conexión a DB y SAP).

    - **Respuesta JSON:**

        ```json
        {
          "database": "connected",
          "sap_connection": "reachable",
          "last_sync_seconds_ago": 45
        }
        ```

    - **Acción si falla:** Investigar la dependencia caída (DB o Red).


### 2. Logs Estructurados (JSON)

En producción (`ENV_STATE=prod`), los logs salen en formato JSON para ser ingeridos por sistemas ELK/Datadog.

**Ejemplo de Log de Error:**

```json
{
  "timestamp": "2024-03-20T10:00:01Z",
  "level": "ERROR",
  "service": "idh-api",
  "correlation_id": "req-12345-xyz",
  "module": "sap_adapter",
  "message": "SAP Connection Timeout",
  "context": {"retry_count": 3}
}
```

- **`correlation_id`:** Copia este ID y búscalo en todo el sistema. Te mostrará toda la traza de esa petición específica.

- **Niveles:**

    - `INFO`: Operación normal (Ingesta de evento, Login usuario).

    - `WARNING`: Fallo recuperable (SAP lento, reintento de envío).

    - `ERROR`: Fallo de transacción (No se pudo guardar orden, BBDD caída).


### 3. Métricas Clave de Negocio (KPIs)

Si tienes un dashboard (Grafana/Kibana), vigila estos contadores:

1. **Lag de Ingesta:** Diferencia de tiempo entre `event_timestamp` (cuando ocurrió en la máquina) y `processed_at` (cuando lo guardamos). Si sube de 5 segundos, el `Worker` está saturado.

2. **Discrepancias:** Número de eventos en `raw_data` con estado `ERROR`. Si sube de repente, una máquina ha cambiado su formato de datos o hay un bug de validación.

3. **Circuit Breaker SAP:** Estado del circuito (`CLOSED` = Bien, `OPEN` = Mal).
