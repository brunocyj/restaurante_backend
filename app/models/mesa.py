"""
Modelos para o sistema de mesas.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.db.session import Base

class StatusMesa(str, PyEnum):
    LIVRE = "LIVRE"
    OCUPADA = "OCUPADA"
    RESERVADA = "RESERVADA"
    MANUTENCAO = "MANUTENCAO"

class Mesa(Base):
    
    __tablename__ = "mesas"
    
    id = Column(String(10), primary_key=True)
    status = Column(String(20), default=StatusMesa.LIVRE)
    qr_code = Column(String(255), nullable=True, unique=True)
    ativa = Column(Boolean, default=True)
    tipo_cardapio_id = Column(UUID, ForeignKey("tipos_cardapio.id"), nullable=False)
    
    #pedidos = relationship("Pedido", back_populates="mesa")
    tipo_cardapio = relationship("TipoCardapio")
    
    def __repr__(self):
        return f"<Mesa(id={self.id}, status={self.status})>" 