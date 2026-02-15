"""Modelos de dominio relacionados con seguridad."""

from pydantic import BaseModel, ConfigDict, Field


class GatewayIdentity(BaseModel):
    """Representa la identidad de un gateway autenticado vía JWT."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="sub")
    gateway_id: str | None = None
