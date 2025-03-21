"""
Endpoints para gerenciamento de cardápio.
"""
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.cardapio_repository import (
    TipoCardapioRepository,
    CategoriaRepository,
    ProdutoRepository
)
from app.schemas.cardapio import (
    TipoCardapio,
    TipoCardapioUpdate,
    TipoCardapioDB,
    Categoria,
    CategoriaUpdate,
    CategoriaDB,
    CategoriaWithTipoCardapio,
    Produto,
    ProdutoUpdate,
    ProdutoDB,
    ProdutoWithCategoria
)

router = APIRouter()

# Instâncias dos repositórios
tipo_cardapio_repo = TipoCardapioRepository()
categoria_repo = CategoriaRepository()
produto_repo = ProdutoRepository()

# Endpoints para Tipo de Cardápio
@router.post("/tipos", response_model=TipoCardapio, status_code=status.HTTP_201_CREATED)
def create_tipo_cardapio(
    *,
    db: Session = Depends(get_db),
    tipo_in: TipoCardapio
) -> Any:
    """
    Cria um novo tipo de cardápio.
    """
    return tipo_cardapio_repo.create(db, obj_in=tipo_in.model_dump(exclude={"id"}))

@router.get("/tipos", response_model=List[TipoCardapioDB])
def list_tipos_cardapio(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros para retornar")
) -> Any:
    """
    Lista todos os tipos de cardápio.
    """
    return tipo_cardapio_repo.get_multi(db, skip=skip, limit=limit)

@router.get("/tipos/{tipo_id}", response_model=TipoCardapioDB)
def read_tipo_cardapio(
    *,
    db: Session = Depends(get_db),
    tipo_id: UUID = Path(..., description="ID do tipo de cardápio")
) -> Any:
    """
    Obtém um tipo de cardápio específico pelo ID.
    """
    tipo = tipo_cardapio_repo.get(db, id=tipo_id)
    if not tipo:
        raise HTTPException(
            status_code=404,
            detail="Tipo de cardápio não encontrado"
        )
    return tipo

@router.put("/tipos/{tipo_id}", response_model=TipoCardapio)
def update_tipo_cardapio(
    *,
    db: Session = Depends(get_db),
    tipo_id: UUID = Path(..., description="ID do tipo de cardápio"),
    tipo_in: TipoCardapioUpdate
) -> Any:
    """
    Atualiza um tipo de cardápio existente.
    """
    tipo = tipo_cardapio_repo.get(db, id=tipo_id)
    if not tipo:
        raise HTTPException(
            status_code=404,
            detail="Tipo de cardápio não encontrado"
        )
    return tipo_cardapio_repo.update(db, db_obj=tipo, obj_in=tipo_in.model_dump(exclude_unset=True))

@router.delete("/tipos/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_cardapio(
    *,
    db: Session = Depends(get_db),
    tipo_id: UUID = Path(..., description="ID do tipo de cardápio")
) -> None:
    """
    Remove um tipo de cardápio.
    """
    tipo = tipo_cardapio_repo.get(db, id=tipo_id)
    if not tipo:
        raise HTTPException(
            status_code=404,
            detail="Tipo de cardápio não encontrado"
        )
    tipo_cardapio_repo.delete(db, id=tipo_id)

# Endpoints para Categorias
@router.post("/categorias", response_model=Categoria, status_code=status.HTTP_201_CREATED)
def create_categoria(
    *,
    db: Session = Depends(get_db),
    categoria_in: Categoria
) -> Any:
    """
    Cria uma nova categoria.
    """
    # Verificar se o tipo de cardápio existe
    tipo = tipo_cardapio_repo.get(db, id=categoria_in.tipo_cardapio_id)
    if not tipo:
        raise HTTPException(
            status_code=404,
            detail="Tipo de cardápio não encontrado"
        )
    return categoria_repo.create(db, obj_in=categoria_in.model_dump(exclude={"id"}))

@router.get("/categorias", response_model=List[CategoriaDB])
def list_categorias(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros para retornar"),
    tipo_cardapio_id: Optional[UUID] = Query(None, description="Filtrar por tipo de cardápio")
) -> Any:
    """
    Lista todas as categorias com filtros opcionais.
    """
    # Implementar filtro por tipo_cardapio_id
    # Esta funcionalidade precisaria ser adicionada ao repositório
    return categoria_repo.get_multi(db, skip=skip, limit=limit)

@router.get("/categorias/{categoria_id}", response_model=CategoriaWithTipoCardapio)
def read_categoria(
    *,   
    db: Session = Depends(get_db),
    categoria_id: UUID = Path(..., description="ID da categoria")
) -> Any:
    """
    Obtém uma categoria específica pelo ID.
    """
    categoria = categoria_repo.get(db, id=categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=404,
            detail="Categoria não encontrada"
        )
    return categoria

@router.put("/categorias/{categoria_id}", response_model=Categoria)
def update_categoria(
    *,
    db: Session = Depends(get_db),
    categoria_id: UUID = Path(..., description="ID da categoria"),
    categoria_in: CategoriaUpdate
) -> Any:
    """
    Atualiza uma categoria existente.
    """
    categoria = categoria_repo.get(db, id=categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=404,
            detail="Categoria não encontrada"
        )
    
    # Verificar se o tipo de cardápio existe, se fornecido
    if categoria_in.tipo_cardapio_id:
        tipo = tipo_cardapio_repo.get(db, id=categoria_in.tipo_cardapio_id)
        if not tipo:
            raise HTTPException(
                status_code=404,
                detail="Tipo de cardápio não encontrado"
            )
    
    return categoria_repo.update(db, db_obj=categoria, obj_in=categoria_in.model_dump(exclude_unset=True))

@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    *,
    db: Session = Depends(get_db),
    categoria_id: UUID = Path(..., description="ID da categoria")
) -> None:
    """
    Remove uma categoria.
    """
    categoria = categoria_repo.get(db, id=categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=404,
            detail="Categoria não encontrada"
        )
    categoria_repo.delete(db, id=categoria_id)

# Endpoints para Produtos
@router.post("/produtos", response_model=Produto, status_code=status.HTTP_201_CREATED)
def create_produto(
    *,
    db: Session = Depends(get_db),
    produto_in: Produto
) -> Any:
    """
    Cria um novo produto.
    """
    categoria = categoria_repo.get(db, id=produto_in.categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=404,
            detail="Categoria não encontrada"
        )
    return produto_repo.create(db, obj_in=produto_in.model_dump(exclude={"id"}))

@router.get("/produtos", response_model=List[ProdutoDB])
def list_produtos(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(1000, ge=1, le=1000, description="Número máximo de registros para retornar"),
    categoria_id: Optional[UUID] = Query(None, description="Filtrar por categoria")
) -> Any:
    """
    Lista todos os produtos com filtros opcionais.
    """
    return produto_repo.get_multi(db, skip=skip, limit=limit)

@router.get("/produtos/{produto_id}", response_model=ProdutoWithCategoria)
def read_produto(
    *,
    db: Session = Depends(get_db),
    produto_id: UUID = Path(..., description="ID do produto")
) -> Any:
    """
    Obtém um produto específico pelo ID.
    """
    produto = produto_repo.get(db, id=produto_id)
    if not produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )
    return produto

@router.put("/produtos/{produto_id}", response_model=Produto)
def update_produto(
    *,
    db: Session = Depends(get_db),
    produto_id: UUID = Path(..., description="ID do produto"),
    produto_in: ProdutoUpdate
) -> Any:
    """
    Atualiza um produto existente.
    """
    produto = produto_repo.get(db, id=produto_id)
    if not produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )
    
    # Verificar se a categoria existe, se fornecida
    if produto_in.categoria_id:
        categoria = categoria_repo.get(db, id=produto_in.categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=404,
                detail="Categoria não encontrada"
            )
    
    return produto_repo.update(db, db_obj=produto, obj_in=produto_in.model_dump(exclude_unset=True))

@router.delete("/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produto(
    *,
    db: Session = Depends(get_db),
    produto_id: UUID = Path(..., description="ID do produto")
) -> None:
    """
    Remove um produto.
    """
    produto = produto_repo.get(db, id=produto_id)
    if not produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )
    produto_repo.delete(db, id=produto_id)