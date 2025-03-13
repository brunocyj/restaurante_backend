"""
Modelos para o sistema de cardápio.
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.session import Base

class TipoCardapio(Base):
    
    __tablename__ = "tipos_cardapio"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    nome = Column(String(50), nullable=False)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    
    categorias = relationship("Categoria", back_populates="tipo_cardapio")
    
    def __repr__(self):
        return f"<TipoCardapio(id={self.id}, nome={self.nome})>"

class Categoria(Base):
    
    __tablename__ = "categorias"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    ordem = Column(Integer)
    ativo = Column(Boolean, default=True)
    tipo_cardapio_id = Column(UUID, ForeignKey("tipos_cardapio.id"))
    
    tipo_cardapio = relationship("TipoCardapio", back_populates="categorias")
    produtos = relationship("Produto", back_populates="categoria")
    
    def __repr__(self):
        return f"<Categoria(id={self.id}, nome={self.nome})>"

class Produto(Base):
    
    __tablename__ = "produtos"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    categoria_id = Column(UUID, ForeignKey("categorias.id"))
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco = Column(Numeric(10, 2), nullable=False)
    imagem_url = Column(String(255))
    ativo = Column(Boolean, default=True)
    
    categoria = relationship("Categoria", back_populates="produtos")
    items_pedido = relationship("ItemPedido", back_populates="produto")
    
    def __repr__(self):
        return f"<Produto(id={self.id}, nome={self.nome}, preco={self.preco})>" 