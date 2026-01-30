"""
Capa de Dominio - El núcleo de la Arquitectura Hexagonal.

Esta capa contiene:
- models/: Entidades y Value Objects (DDD)
- ports/: Interfaces abstractas (Repository Protocols, Service Ports)
- exceptions.py: Excepciones de negocio

REGLA DE ORO: Esta capa NO debe importar NADA de infrastructure ni application.
"""
