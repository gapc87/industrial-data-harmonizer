"""
Puertos del Dominio: Interfaces abstractas.

Define los contratos que la capa de infraestructura debe implementar:
- Repository Protocols: Interfaces para persistencia
- Service Ports: Interfaces para servicios externos (SAP, Email, etc.)

Ejemplo:
    class OrderRepositoryProtocol(Protocol):
        async def get_by_id(self, order_id: str) -> Order | None: ...
        async def save(self, order: Order) -> None: ...
"""
