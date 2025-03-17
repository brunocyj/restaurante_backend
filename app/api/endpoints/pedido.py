"""
Endpoints para gerenciamento de pedidos
"""
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.pedido import StatusPedido
from app.models.usuario import Usuario
from app.repositories.pedido_repository import PedidoRepository
from app.schemas.pedido import (
    Pedido, PedidoCreate, PedidoUpdate, PedidoList,
    ItemPedidoCreate, ItemPedidoUpdate
)

router = APIRouter()

@router.post("/", response_model=Pedido, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido_in: PedidoCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Cria um novo pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        # Converter itens para o formato esperado pelo repository
        itens_data = [item.dict() for item in pedido_in.itens]
        
        pedido = repository.criar_pedido(
            mesa_id=pedido_in.mesa_id,
            itens_data=itens_data,
            observacao_geral=pedido_in.observacao_geral,
            manual=pedido_in.manual
        )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar pedido: {str(e)}"
        )

@router.get("/", response_model=PedidoList)
def listar_pedidos(
    status: Optional[StatusPedido] = None,
    mesa_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Any:
    """
    Lista pedidos com filtros opcionais.
    """
    repository = PedidoRepository(db)
    pedidos, total = repository.listar_pedidos(
        skip=skip,
        limit=limit,
        status=status,
        mesa_id=mesa_id
    )
    
    return {
        "pedidos": pedidos,
        "total": total,
        "pagina": skip // limit + 1
    }

@router.get("/{pedido_id}", response_model=Pedido)
def obter_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Obtém um pedido pelo ID.
    """
    repository = PedidoRepository(db)
    pedido = repository.obter_pedido(pedido_id)
    
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    return pedido

@router.put("/{pedido_id}", response_model=Pedido)
def atualizar_pedido(
    pedido_id: UUID,
    pedido_in: PedidoUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Atualiza um pedido.
    """
    try:
        repository = PedidoRepository(db)
        pedido = repository.atualizar_pedido(
            pedido_id=pedido_id,
            status=pedido_in.status,
            observacao_geral=pedido_in.observacao_geral,
            mesa_id = pedido_in.mesa_id
        )
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar pedido: {str(e)}"
        )

@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """
    Deleta um pedido.
    """
    repository = PedidoRepository(db)
    sucesso = repository.deletar_pedido(pedido_id)
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )

@router.post("/{pedido_id}/itens", response_model=Pedido)
def adicionar_item(
    pedido_id: UUID,
    item_in: ItemPedidoCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Adiciona um item a um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        # Adicionar item
        repository.adicionar_item(
            pedido_id=pedido_id,
            produto_id=item_in.produto_id,
            quantidade=item_in.quantidade,
            observacoes=item_in.observacoes
        )
        
        # Retornar pedido atualizado
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar item: {str(e)}"
        )

@router.put("/{pedido_id}/itens/{item_id}", response_model=Pedido)
def atualizar_item(
    pedido_id: UUID,
    item_id: UUID,
    item_in: ItemPedidoUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Atualiza um item de um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        # Atualizar item
        repository.atualizar_item(
            item_id=item_id,
            quantidade=item_in.quantidade,
            observacoes=item_in.observacoes
        )
        
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar item: {str(e)}"
        )

@router.delete("/{pedido_id}/itens/{item_id}", response_model=Pedido)
def remover_item(
    pedido_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Remove um item de um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        sucesso = repository.remover_item(item_id)
        
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado"
            )
        
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover item: {str(e)}"
        )
