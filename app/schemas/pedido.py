"""
Schemas para pedidos
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.models.pedido import StatusPedido

# Schemas para ItemPedido

class ItemPedidoBase(BaseModel):
    """
    Schema base para item de pedido
    """
    produto_id: UUID
    quantidade: int
    observacoes: Optional[str] = None
    
    @validator("quantidade")
    def validar_quantidade(cls, v):
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que 0")
        return v

class ItemPedidoCreate(ItemPedidoBase):
    """
    Schema para criar item de pedido
    """
    pass

class ItemPedidoUpdate(BaseModel):
    """
    Schema para atualizar item de pedido
    """
    quantidade: Optional[int] = None
    observacoes: Optional[str] = None
    
    @validator("quantidade")
    def validar_quantidade(cls, v):
        if v is not None and v <= 0:
            raise ValueError("A quantidade deve ser maior que 0")
        return v

class ItemPedido(ItemPedidoBase):
    """
    Schema para item de pedido
    """
    id: UUID
    pedido_id: UUID
    preco_unitario: Decimal
    criado_em: datetime
    
    class Config:
        orm_mode = True

# Schemas para Pedido

class PedidoBase(BaseModel):
    """
    Schema base para pedido
    """
    mesa_id: str
    observacao_geral: Optional[str] = None
    manual: bool = False

class PedidoCreate(PedidoBase):
    """
    Schema para criar pedido
    """
    itens: List[ItemPedidoCreate]
    
    @validator("itens")
    def validar_itens(cls, v):
        if not v:
            raise ValueError("Deve haver pelo menos um item no pedido")
        return v

class PedidoUpdate(BaseModel):
    """
    Schema para atualizar pedido
    """
    observacao_geral: Optional[str] = None
    status: Optional[StatusPedido] = None
    mesa_id: Optional[str] = None

class Pedido(PedidoBase):
    """
    Schema para pedido
    """
    id: UUID
    status: StatusPedido
    valor_total: Decimal
    criado_em: datetime
    itens: List[ItemPedido]
    
    class Config:
        orm_mode = True

class PedidoList(BaseModel):
    """
    Schema para lista de pedidos
    """
    pedidos: List[Pedido]
    total: int
    pagina: int
    
    class Config:
        orm_mode = True

# Schemas adicionais para operações específicas

class AdicionarItemPedido(BaseModel):
    """
    Schema para adicionar item a um pedido existente
    """
    item: ItemPedidoCreate

class RemoverItemPedido(BaseModel):
    """
    Schema para remover item de um pedido
    """
    item_id: UUID

class AtualizarItemPedido(BaseModel):
    """
    Schema para atualizar item de um pedido
    """
    item_id: UUID
    dados: ItemPedidoUpdate
    