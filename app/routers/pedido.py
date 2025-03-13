"""
Router para as funcionalidades relacionadas aos pedidos.
"""
from fastapi import APIRouter

from app.api.endpoints import pedido

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"],
    responses={404: {"description": "Item não encontrado"}},
)
router.include_router(pedido.router)
