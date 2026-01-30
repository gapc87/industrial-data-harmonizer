# Guía de Resolución de Problemas (Troubleshooting)

Utiliza este árbol de decisión para diagnosticar y resolver las incidencias más comunes.

## 1. Escenario A: El sistema no arranca (Boot Failure)

- **Síntoma:** `just up` falla o el contenedor se reinicia en bucle (CrashLoopBackOff).

- **Diagnóstico:**

    1. Ver logs: `docker logs idh-api`.

    2. Buscar `ValidationError` (Configuración) o `Connection refused` (Base de datos).

- **Soluciones Comunes:**

    - **Error de Configuración:** Falta una variable en el archivo `.env`.

    - **Puerto Ocupado:** El puerto 8000 ya está en uso por otro servicio. Cambia `APP_PORT` en el `.env`.

    - **Base de Datos Lenta:** La API intenta conectar antes de que Postgres esté listo. (El sistema tiene _retries_, pero si tarda >30s, fallará).


## 2. Escenario B: SAP no responde (Circuit Breaker Abierto)

- **Síntoma:** Los logs muestran `CircuitBreakerError` o `SAP Connection Timeout`. Los datos se guardan en local pero no sincronizan.

- **Diagnóstico:**

    - Verificar estado del circuito en `/health`.

    - Intentar `curl -v <SAP_URL>` desde dentro del contenedor para descartar problemas de red/DNS.

- **Acción:**

    1. No reiniciar el servicio inmediatamente (perderás la caché del circuito).

    2. Verificar con el equipo de IT si SAP está en mantenimiento.

    3. El sistema reintentará automáticamente (Half-Open) pasados unos segundos.

    4. Si persiste > 1 hora, contactar con Redes.


## 3. Escenario C: Discrepancias de Datos

- **Síntoma:** "Producción dice que fabricaron 1000 unidades, el Dashboard muestra 950".

- **Investigación Forense:**

    1. Obtener el ID de la orden.

    2. Consultar la tabla `raw_data`:

        ```sql
        SELECT * FROM raw_data.incoming_events WHERE payload->>'order_id' = 'ORD-123';
        ```

    3. **Caso 1:** El dato no está en `raw_data` -> El problema es del Edge Collector o la Red de Planta (nunca llegó).

    4. **Caso 2:** El dato está en `raw_data` pero tiene `status='ERROR'` -> El problema es de validación (Bug de software o dato mal formado). Revisar columna `error_log`.


## 4. Escenario D: Lentitud Extrema (Performance Degradation)

- **Síntoma:** La API tarda > 2 segundos en responder.

- **Diagnóstico:**

    - Revisar uso de CPU/RAM: `docker stats`.

    - Revisar bloqueos en BBDD.

- **Acción:**

    - Si es CPU: Posible bucle infinito o procesamiento pesado en el hilo principal.

    - Si es DB: Verificar si hay transacciones largas abiertas ("Stuck locks").

        ```sql
        SELECT * FROM pg_stat_activity WHERE state = 'active';
        ```


## 5. Escenario E: Edge Collector Desconectado

- **Síntoma:** No llegan datos de una máquina específica.

- **Diagnóstico:**

    - Hacer Ping a la IP del Edge Device.

    - Revisar logs del dispositivo en planta (si accesible).

- **Causa Raíz Común:**

    - Cable de red desconectado en planta.

    - Cambio de IP en el PLC sin actualizar la configuración del Collector.

    - Credenciales OAuth2 expiradas (El log del Collector dirá `401 Unauthorized`).
