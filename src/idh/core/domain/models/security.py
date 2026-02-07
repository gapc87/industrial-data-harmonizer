"""
Modelos de dominio relacionados con seguridad.
"""

from pydantic import BaseModel, Field


class GatewayIdentity(BaseModel):
    """
    Representa la identidad de un gateway o usuario autenticado vía JWT.
    """

    id: str = Field(..., alias="sub")
