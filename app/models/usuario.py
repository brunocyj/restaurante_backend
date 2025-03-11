from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.sql import expression

from app.db.session import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False)
    cargo = Column(String, nullable=False, default="usuario")
    ativo = Column(Boolean, default=True, server_default=expression.true())

    def __repr__(self):
        return f"<Usuario(id={self.id}, username='{self.username}', cargo='{self.cargo}')>"

