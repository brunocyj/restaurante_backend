"""
Endpoints para gerenciamento de mesas.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.mesa_repository import MesaRepository
from app.schemas.mesa import Mesa, MesaUpdate, MesaWithTipoCardapio
from uuid import UUID

router = APIRouter()

mesa_repo = MesaRepository()

@router.post("/", response_model=Mesa, status_code=status.HTTP_201_CREATED)
def create_mesa(
    *,
    db: Session = Depends(get_db),
    mesa_in: Mesa
) -> Any:
    """
    Cria uma nova mesa.
    """
    return mesa_repo.create(db, obj_in=mesa_in.model_dump())

@router.get("/", response_model=List[MesaWithTipoCardapio])
def list_mesas(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros para retornar"),
    tipo_cardapio_id: Optional[UUID] = Query(None, description="Filtrar por tipo de cardápio")
) -> Any:
    """
    Lista todas as mesas com opção de filtro por tipo de cardápio.
    """
    return mesa_repo.get_multi(db, skip=skip, limit=limit, tipo_cardapio_id=tipo_cardapio_id)

@router.get("/{mesa_id}", response_model=MesaWithTipoCardapio)
def read_mesa(
    *,
    db: Session = Depends(get_db),
    mesa_id: str = Path(..., description="ID da mesa")
) -> Any:
    """
    Obtém uma mesa específica pelo ID.
    """
    mesa = mesa_repo.get(db, mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return mesa

@router.put("/{mesa_id}", response_model=Mesa)
def update_mesa(
    *,
    db: Session = Depends(get_db),
    mesa_id: str = Path(..., description="ID da mesa"),
    mesa_in: MesaUpdate
) -> Any:
    """
    Atualiza uma mesa existente.
    """
    mesa = mesa_repo.get(db, mesa_id)   
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return mesa_repo.update(db, db_obj=mesa, obj_in=mesa_in.model_dump(exclude_unset=True))

@router.delete("/{mesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mesa(    
    *,
    db: Session = Depends(get_db),
    mesa_id: str
) -> None:
    """
    Remove uma mesa.
    """ 
    mesa = mesa_repo.get(db, id = mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    mesa_repo.delete(db, id = mesa_id)
    

