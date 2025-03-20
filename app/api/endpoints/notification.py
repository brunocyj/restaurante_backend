"""
Endpoints básicos para gerenciamento de notificações.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.notification_service import notification_service

router = APIRouter()

@router.get("/", response_model=List[Dict])
def list_notifications(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de notificações para retornar")
) -> Any:
    """
    Lista todas as notificações não lidas.
    """
    return notification_service.get_unread_notifications(limit=limit)

@router.put("/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_as_read(
    *,
    db: Session = Depends(get_db),
    notification_id: str = Path(..., description="ID da notificação")
) -> Any:
    """
    Marca uma notificação como lida.
    """
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    return {
        "success": True,
        "message": "Notificação marcada como lida"
    }

@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
def delete_notification(
    *,
    db: Session = Depends(get_db),
    notification_id: str = Path(..., description="ID da notificação")
) -> Any:
    """
    Remove uma notificação.
    """
    success = notification_service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    return {
        "success": True,
        "message": "Notificação removida com sucesso"
    } 