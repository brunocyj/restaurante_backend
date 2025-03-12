"""
Schemas para o cardápio.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from decimal import Decimal

# TipoCardapio
class TipoCardapio(BaseModel):
    """
    Schema para o tipo de cardápio.
    """
    nome: str = Field(..., min_length=1, max_length=50, description="Nome do tipo de cardápio")
    descricao: Optional[str] = None
    ativo: bool = True

    class Config:
        from_attributes = True

class TipoCardapioDB(TipoCardapio):
    """
    Schema com o ID do tipo de cardápio.
    """
    id: UUID = Field(..., description="ID único do tipo de cardápio")

class TipoCardapioUpdate(BaseModel):
    """
    Schema para atualização do tipo de cardápio.
    """
    nome: Optional[str] = Field(None, min_length=1, max_length=50)
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

# Categoria
class Categoria(BaseModel):
    """
    Schema para a categoria de cardápio.
    """
    nome: str = Field(..., min_length=1, max_length=100, description="Nome da categoria")
    descricao: Optional[str] = None
    ordem: Optional[int] = None
    ativo: bool = True
    tipo_cardapio_id: UUID = Field(..., description="ID do tipo de cardápio")

    class Config:
        from_attributes = True

class CategoriaDB(Categoria):
    """
    Schema com o ID da categoria.
    """
    id: UUID = Field(..., description="ID único da categoria")

class CategoriaUpdate(BaseModel):
    """
    Schema para atualização da categoria de cardápio.
    """
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    ordem: Optional[int] = None
    ativo: Optional[bool] = None
    tipo_cardapio_id: Optional[UUID] = None

class CategoriaWithTipoCardapio(Categoria):
    """
    Schema para a categoria de cardápio com o tipo de cardápio.
    """
    tipo_cardapio: Optional[TipoCardapio] = None

# Produto
class Produto(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do produto")
    descricao: Optional[str] = None
    preco: Decimal = Field(..., gt=0, description="Preço do produto")
    imagem_url: Optional[str] = None
    disponivel: bool = True
    categoria_id: UUID = Field(..., description="ID da categoria")

    class Config:
        from_attributes = True

class ProdutoDB(Produto):
    """
    Schema com o ID do produto.
    """
    id: UUID = Field(..., description="ID único do produto")

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    preco: Optional[Decimal] = Field(None, gt=0)
    imagem_url: Optional[str] = None
    disponivel: Optional[bool] = None
    categoria_id: Optional[UUID] = None

class ProdutoWithCategoria(Produto):
    categoria: Optional[Categoria] = None

class CategoriaWithProdutos(Categoria):
    produtos: Optional[List[Produto]] = None

# Cardápio completo
class CardapioCompleto(BaseModel):
    tipo_cardapio: TipoCardapio
    categorias: List[CategoriaWithProdutos]