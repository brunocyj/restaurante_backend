import logging
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.init_db import init_db
from app.routers import auth, cardapio, mesa, pedido

#log
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cardapio.router)
app.include_router(mesa.router)
app.include_router(pedido.router)

@app.get("/health", tags=["Saúde"])
def health_check():
    """
    Verifica se a API está funcionando corretamente
    verificação de status e ambiente
    """
    return {"status": "ok", "ambiente": settings.ENVIRONMENT}



@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando a aplicação...")
    if not init_db():
        logger.error("Erro ao inicializar o banco de dados")
        raise Exception("Erro ao inicializar o banco de dados")
    else:
        logger.info("Banco de dados inicializado com sucesso")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Encerrando a aplicação...")




