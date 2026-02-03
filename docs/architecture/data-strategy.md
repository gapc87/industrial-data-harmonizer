# Estrategia de Gestión y Persistencia de Datos

En un entorno industrial, la integridad del dato es innegociable, pero la calidad del dato de entrada (origen) suele ser volátil. Implementamos una arquitectura basada en el patrón **"Medallion Architecture"**.

## 1. Filosofía: "Write Fast, Validate Later"

Separamos drásticamente la Ingesta (captura) del Dominio (uso).

* **Problema:** Validar estrictamente en la puerta de entrada rechazaría datos de telemetría valiosos por errores de formato menores.
* **Solución:** Primero aseguramos la persistencia en crudo, luego procesamos.

* **Zona Bronze (Landing):** Esquema `raw_data`. Uso extensivo de **`JSONB`** para inmutabilidad forense.
* **Zona Silver (Clean):** Esquema `public`. Tablas relacionales validadas vía DDD.

## 2. Arquitectura de Esquemas (PostgreSQL 15.15+)

### A. Zona de Aterrizaje: Esquema `raw_data`
Actúa como un *Data Lake Operativo* y registro de auditoría inmutable.

* **Tecnología:** Uso extensivo de **`JSONB`**.
* **Propósito:** Almacenar el *payload* exacto recibido del *Edge Collector* o SAP.
* **Optimización Industrial:** Se implementa una **Ventana de Escritura en Lote (2s)** para minimizar el desgaste de los discos SSD en PCs Industriales, aprovechando el *Write-Ahead-Log* (WAL).
* **Resiliencia:**
    * **Capacidad de Buffer:** El Gateway mantiene un buffer de **>= 7 días** para sobrevivir a cortes prolongados.
    * **Política de Desalojo (Priority Eviction):** Ante falta de espacio, se descarta primero la `Telemetría`, preservando `Alarmas/Eventos` y `Auditoría` indefinidamente.

```sql
CREATE TABLE raw_data.incoming_events (
    id SERIAL PRIMARY KEY,
    payload JSONB,
    received_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) -- PENDING, PROCESSED, ERROR
);
```

### B. Zona de Dominio: Esquema `public`
Es el santuario de los datos limpios, validados y listos para consumo.

* **Estructura:** Tablas relacionales estrictas con Foreign Keys y tipos nativos.
* **Vinculación:** Mapeadas a Entidades del Dominio vía ORM (SQLAlchemy).

## 3. Pipeline de Transformación Asíncrona (ETL)

El flujo de datos entre `raw_data` y `public` no es sincrónico.

1. **Ingesta (API):** Inserta en `raw_data` y responde `202 Accepted`.
2. **Procesamiento (Worker):** Lee eventos `PENDING`. Invoca la Capa de Dominio (DDD) para validar.
3. **Persistencia:**
    * **Éxito:** Guarda en `public` y marca como `PROCESSED`.
    * **Fallo:** Marca como `ERROR` y registra motivo. No se pierden datos.

## 4. Beneficios

1. **Trazabilidad Total:** Posibilidad de auditar el dato crudo original meses después.
2. **Capacidad de "Replay":** Si se corrige un bug de cálculo, se pueden reprocesar los eventos históricos.
3. **Evolución del Esquema:** `raw_data` acepta nuevos campos sin cambios de esquema inmediato.
4. **Optimización SSD:** Menor frecuencia de commits físicos gracias al procesamiento por batches.
