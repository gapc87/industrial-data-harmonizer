# Tareas de Mantenimiento Rutinario (SOPs)

Procedimientos operativos estándar (SOP) para garantizar la longevidad del sistema y la seguridad de los datos.

### 1. Backups de Base de Datos

La base de datos es el activo más valioso. Se debe configurar una tarea programada (Cron) en el servidor host para realizar volcados diarios.

- **Comando Manual (One-Off):**

    ```bash
    # Crea un archivo .sql.gz con la fecha actual
    docker exec -t idh-db pg_dump -U idh_admin idh_production | gzip > backup_$(date +%Y%m%d).sql.gz
    ```

- **Política de Retención Sugerida:**

    - Diarios: Mantener últimos 7 días.

    - Semanales: Mantener últimas 4 semanas.

    - Mensuales: Mantener últimos 6 meses (Off-site / S3).


### 2. Limpieza de Datos Crudos (Pruning)

La tabla `raw_data.incoming_events` crece indefinidamente. Para evitar llenar el disco, se debe purgar la data antigua que ya ha sido procesada correctamente.

- **Política:** Eliminar eventos `PROCESSED` con más de 90 días de antigüedad.

- **Ejecución:**

    Se recomienda ejecutar este SQL mensualmente:

    ```SQL
    DELETE FROM raw_data.incoming_events
    WHERE status = 'PROCESSED'
    AND received_at < NOW() - INTERVAL '90 days';
    ```


### 3. Mantenimiento de Docker

Con el tiempo, las imágenes antiguas y los volúmenes huérfanos consumen espacio.

- **Comando de Limpieza:**

    ```bash
    docker system prune -f
    ```

    > ⚠️ **Nota:** Esto borra imágenes no usadas y caché de build. No borra volúmenes de datos activos.
