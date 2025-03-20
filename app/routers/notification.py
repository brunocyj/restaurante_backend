"""
Router para as funcionalidades relacionadas às notificações.
"""
from fastapi import APIRouter

from app.api.endpoints import notification

router = APIRouter(
    prefix="/notificacoes",
    tags=["Notificações"],
    responses={404: {"description": "Item não encontrado"}},
)
router.include_router(notification.router) 