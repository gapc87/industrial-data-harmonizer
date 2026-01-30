"""
Servicios de Aplicación.

Los servicios de aplicación orquestan casos de uso:
- Reciben DTOs de la API
- Invocan la lógica de dominio
- Coordinan la persistencia mediante puertos

Ejemplo:
    class CreateOrderService:
        def __init__(self, order_repo: OrderRepositoryProtocol):
            self._repo = order_repo

        async def execute(self, dto: CreateOrderDTO) -> OrderResponseDTO:
            order = Order.create(dto.product_id, dto.quantity)
            await self._repo.save(order)
            return OrderResponseDTO.from_entity(order)
"""
