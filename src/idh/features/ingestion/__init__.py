"""
Módulo de Ingestión de Datos.

Responsable de la captura de datos desde fuentes OT (PLCs, SCADA)
y su persistencia segura en la capa Raw Data (Bronze).

Funcionalidades:
- Drivers de protocolo (OPC UA, Modbus TCP).
- Normalización inicial de payloads.
- Aterrizaje en tablas JSONB inmutables.
"""
