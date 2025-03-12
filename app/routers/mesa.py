"""
Router para as funcionalidades relacionadas às mesas.
"""
from fastapi import APIRouter

from app.api.endpoints import mesa

router = APIRouter(
    prefix="/mesas",
    tags=["Mesas"],
    responses={404: {"description": "Item não encontrado"}},
)
router.include_router(mesa.router)

