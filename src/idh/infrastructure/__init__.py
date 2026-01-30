"""
Capa de Infraestructura - El Mundo Real.

Esta capa contiene las implementaciones concretas:
- api/: FastAPI routers y endpoints
- persistence/: Repositorios SQLAlchemy (implementan domain/ports)
- adapters/: Clientes externos (SAP, Email, etc.)
- config.py: Configuración con Pydantic Settings

Esta capa PUEDE importar Domain y Application.
"""
