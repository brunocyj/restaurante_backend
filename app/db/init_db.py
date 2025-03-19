from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.db.session import engine

logger = logging.getLogger(__name__)

def init_db():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                logger.info("Conexão com o banco de dados estabelecida com sucesso!")
                return True
            else:
                logger.error("Falha ao testar a conexão com o banco de dados.")
                return False
    except SQLAlchemyError as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return False 