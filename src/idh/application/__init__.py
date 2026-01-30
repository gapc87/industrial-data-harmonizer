"""
Capa de Aplicación - Orquestación de Casos de Uso.

Esta capa contiene:
- services/: Servicios de aplicación que orquestan el dominio
- dtos/: Data Transfer Objects (entrada/salida de la API)

La capa de aplicación:
- Coordina el flujo entre API y Dominio
- NO contiene lógica de negocio (eso va en Domain)
- Puede importar Domain, pero NO Infrastructure
"""
