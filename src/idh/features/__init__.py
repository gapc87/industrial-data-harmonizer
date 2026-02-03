"""
Módulos de Negocio (Features).

Esta carpeta contiene los módulos funcionales aislados del sistema.
Cada feature debe ser autónomo y comunicarse con otros solo a través
de la capa Core (Dominio/Eventos).

Módulos disponibles:
- ingestion: Captura de datos OT (PLC -> Raw Data).
- production: Gestión de órdenes y sincronización con SAP (IT).
- quality: Validación de calidad basada en telemetría.
"""
