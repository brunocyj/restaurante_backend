#imports basicos

import uvicorn
import os
import logging
from dotenv import load_dotenv
from app.main import app

load_dotenv()

#log
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


#variaveis do .env
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = os.getenv("RELOAD", "True").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

def get_application():
    logger.info(f"Iniciando aplicação {ENVIRONMENT}...")
    logger.info(f"Host: {HOST}")
    logger.info(f"Porta: {PORT}")
    logger.info(f"Reload: {RELOAD}")
    return app


if __name__ == "__main__":
    if ENVIRONMENT.lower() == "development":
        print("Modo de desenvolvimento ativado")
    else:
        print("Modo de produção ativado")
        
        
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level = LOG_LEVEL,
    )
