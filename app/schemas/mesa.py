"""
Schemas para mesas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

from app.schemas.cardapio import TipoCardapio
from app.models.mesa import StatusMesa

class Mesa(BaseModel):
    """
    Schema para a mesa
    """
    id: str = Field(..., description="ID único da mesa")
    status: StatusMesa = Field(..., description="Status da mesa")
    qr_code: Optional[str] = Field(None, description="Código QR da mesa")
    ativa: bool = Field(..., description="Mesa está ativa")
    tipo_cardapio_id: UUID = Field(..., description="ID do tipo de cardápio")
    
    class Config:
        from_attributes = True


class MesaUpdate(BaseModel):
    """
    Schema para atualização da mesa
    """
    status: Optional[StatusMesa] = None
    qr_code: Optional[str] = None
    ativa: Optional[bool] = None
    tipo_cardapio_id: Optional[UUID] = None

class MesaWithTipoCardapio(Mesa):
    """
    Schema para a mesa com o tipo de cardápio
    """
    tipo_cardapio: Optional[TipoCardapio] = None
