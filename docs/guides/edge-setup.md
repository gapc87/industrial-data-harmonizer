# Guía de Instalación del Edge Collector (OT)

Esta guía está dirigida a los **Ingenieros de Automatización / Mantenimiento** encargados de desplegar el agente de recolección de datos en los PCs industriales o Gateways (Raspberry Pi/Siemens IPC) situados en planta.

## 1. Requisitos del Sistema (Hardware/OS)

El Edge Collector es extremadamente ligero. Puede correr en hardware modesto.

*   **OS:** Linux (Debian/Ubuntu/Alpine) o Windows 10/11 IoT.
*   **Runtime:** Python 3.9 o superior.
*   **Red:**
    *   **Acceso LAN:** Debe ver la IP del PLC (Modbus/OPC-UA).
    *   **Acceso WAN (Salida):** Debe tener salida HTTPS (Puerto 443) hacia el servidor IDH Central (ej: `https://idh.corporativo.internal`).
    *   **IMPORTANTE:** No se necesita IP pública ni abrir puertos de entrada.

## 2. Instalación del Agente

### Paso 1: Obtener el Script
Descarga la última versión del script standalone desde el repositorio de releases.

```bash
mkdir -p /opt/idh-collector
cd /opt/idh-collector
# (Ejemplo)
curl -O https://repo.interno/idh/edge-collector-v1.py
```

### Paso 2: Entorno Virtual
Aísla las dependencias para evitar conflictos con el OS.

```bash
python3 -m venv venv
source venv/bin/activate

# Instalar liberías mínimas
pip install requests oauthlib tenacity python-dotenv
```

### Paso 3: Configuración (`.env`)
Crea un archivo `.env` en la misma carpeta. Solicita las credenciales `CLIENT_ID` y `CLIENT_SECRET` al equipo de IT.

```ini
# IDH Central Server URL
IDH_API_URL=https://idh.corporativo.internal/api/v1/ingest/telemetry

# Auth (Machine-to-Machine)
AUTH_TOKEN_URL=https://idh.corporativo.internal/api/v1/auth/token
CLIENT_ID=edge_linea_01
CLIENT_SECRET=hp... (SECRETO)

# Configuración PLC
PLC_IP=192.168.1.50
PLC_PORT=502

# Configuración del Buffer Local
BUFFER_DB_PATH=./buffer.sqlite
MAX_RETRIES=50
```

## 3. Resiliencia Offline (Local Buffer)

El Edge Collector implementa un mecanismo de **Store & Forward**.

*   **Funcionamiento:** Si la conexión con el servidor central falla (o responde 5xx), los datos **NO se pierden**. Se guardan automáticamente en una base de datos local SQLite (`buffer.sqlite`).
*   **Recuperación:** El script intenta re-enviar los datos pendientes cada 60 segundos automáticamente.
*   **Mantenimiento:** No borre el archivo `buffer.sqlite` a menos que desee purgar datos no enviados.

## 4. Ejecución como Servicio (Systemd)

Para asegurar que el colector arranca automáticamente tras un corte de luz, crea un servicio `systemd`.

Archivo: `/etc/systemd/system/idh-collector.service`

```ini
[Unit]
Description=IDH Edge Collector Data Pump
After=network.target

[Service]
User=idh_user
WorkingDirectory=/opt/idh-collector
ExecStart=/opt/idh-collector/venv/bin/python edge-collector-v1.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Habilitar el servicio:

```bash
sudo systemctl enable idh-collector
sudo systemctl start idh-collector
```

## 4. Verificación

Revisa los logs para confirmar que está enviando datos ("Heartbeat"):

```bash
journalctl -u idh-collector -f
```

Deberías ver:
`INFO: Payload sent successfully. Status: 202 Accepted.`
