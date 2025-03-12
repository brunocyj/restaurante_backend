from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, Numeric, UUID, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from enum import Enum as PyEnum
from datetime import datetime
import pytz

from app.db.session import Base

#solução para o problema de fuso horário com hospedagem do backend no railway que não tem servido em são paulo ou em qualqur lugar do brasil
#caso isto não seja necessario apenas retirar o import pytz e a função get_brasil_now e substitui o default=get_brasil_now pelo default=func.now()

brasil_tz = pytz.timezone("America/Sao_Paulo")

def get_brasil_now():
    return datetime.now(brasil_tz)

class StatusPedido(str, PyEnum):
    ABERTO = "ABERTO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

class Pedido(Base):
    """Modelo para pedidos."""
    
    __tablename__ = "pedidos"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    mesa_id = Column(String(10), ForeignKey("mesas.id"), nullable=False)
    status = Column(String(20), nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)
    observacao_geral = Column(Text, nullable=True)
    manual = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=get_brasil_now)
    
    mesa = relationship("Mesa", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Pedido(id={self.id}, status={self.status})>"

class ItemPedido(Base):
    
    __tablename__ = "items_pedido"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    pedido_id = Column(UUID, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(UUID, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, default=1)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=get_brasil_now)
    
    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto", back_populates="items_pedido")
    
    def __repr__(self):
        return f"<ItemPedido(id={self.id}, produto_id={self.produto_id}, quantidade={self.quantidade})>" 