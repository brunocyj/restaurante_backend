"""
Router para as funcionalidades relacionadas ao cardápio.
"""
from fastapi import APIRouter

from app.api.endpoints import cardapio

router = APIRouter(
    prefix="/cardapio",
    tags=["Cardápio"],
    responses={404: {"description": "Item não encontrado"}},
)
router.include_router(cardapio.router) 