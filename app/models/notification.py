"""
modelo basico para implementar os tipos de notificação
conforme escalando pode adicionar mais
"""

from enum import Enum
from sqlalchemy import Column, String, Boolean, ForeignKey, UUID, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from uuid import uuid4
from datetime import datetime
import pytz

brasil_tz = pytz.timezone("America/Sao_Paulo")

def get_brasil_now():
    return datetime.now(brasil_tz)



class tipos_notificacao(str,Enum):
    NOVO_ITEM = "NOVO_ITEM"
    PEDIDO_FINALIZADO = "PEDIDO_FINALIZADO"
    CHAMADO_ATENDENTE = "CHAMADO_ATENDENTE"


class Notificacao(Base):

    __tablename__ = "notificacoes"

    id = Column(UUID, primary_key=True, default=uuid4)
    mesa_id = Column(String(10), ForeignKey("mesas.id"), nullable=False)
    tipo = Column(
        Enum(tipos_notificacao),
        nullable=False,
        unique=False
    )
    mensagem = Column(String(255), nullable=True, unique=False)
    status = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=get_brasil_now)
    lido_em = Column(DateTime, default=get_brasil_now)

    mesa = relationship("Mesa", back_populates="notificacoes")

    def __repr__(self):
        return f"<Notificacao(id={self.id}, tipo={self.tipo})>"