# Recuperación ante Desastres (DRP)

Plan de acción para escenarios de pérdida total del servicio o corrupción de datos irrecuperable.

### 1. Objetivos de Recuperación

- **RPO (Recovery Point Objective):** **24 Horas**.

    - _Significado:_ En el peor caso (fallo total del disco antes del backup nocturno), aceptamos perder hasta 24h de datos procesados en el servidor central.

    - _Mitigación:_ Los _Edge Collectors_ en planta tienen un buffer local de 7 días. Tras restaurar el servidor, los colectores re-enviarán los datos pendientes, reduciendo la pérdida de datos real a casi cero.

- **RTO (Recovery Time Objective):** **< 2 Horas**.

    - _Significado:_ Tiempo máximo estimado desde que se declara el desastre hasta que el servicio vuelve a estar online.


### 2. Procedimiento de Restauración Total ("From Scratch")

Sigue estos pasos si el servidor original ha sido destruido o formateado.

**Fase 1: Infraestructura Base**

1. Aprovisionar nuevo servidor (Ubuntu/Debian recomendado).

2. Instalar Docker, Docker Compose y Git.

3. Clonar el repositorio:

    ```bash
    git clone https://github.com/gapc87/industrial-data-harmonizer.git /opt/idh
    ```


**Fase 2: Configuración**

1. Recuperar el archivo `.env` desde el gestor de contraseñas seguro (1Password/Vault) de la empresa.

2. Colocarlo en `/opt/idh/.env`.


**Fase 3: Arranque Limpio**

1. Levantar los servicios (esto creará una BBDD vacía):

    ```bash
    just up
    ```

2. Esperar a que la API responda en `/health`.


**Fase 4: Inyección de Datos (Restore)**

1. Transferir el último backup válido (`backup_YYYYMMDD.sql.gz`) al servidor.

2. Ejecutar la restauración:

    ```bash
    # Descomprimir y entubar directo al contenedor de base de datos
    zcat backup_YYYYMMDD.sql.gz | docker exec -i idh-db psql -U idh_admin -d idh_production
    ```

1. Verificar que los datos han aparecido:

    ```bash
    curl http://localhost:8000/api/v1/orders/count
    ```


### 3. Operación en Modo Degradado

Si el sistema central (IDH) está caído, la planta debe seguir produciendo.

- **Protocolo de Planta:**

    1. Las máquinas siguen operando.

    2. Los operarios registran las incidencias de calidad en papel o Excel local temporalmente.

    3. Los _Edge Collectors_ acumularán datos en su SQLite local (Buffer).

- **Protocolo de Resincronización:**

    1. Una vez el IDH vuelva a estar online (Fase 3), los _Edge Collectors_ detectarán la conexión y comenzarán a vaciar su buffer automáticamente ("Catch-up mode").

    2. Se debe monitorizar la carga de CPU durante este proceso, ya que la ingesta será masiva.
