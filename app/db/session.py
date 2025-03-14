from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    echo=not settings.is_production,
    pool_pre_ping=True, 
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        logger.debug("Conexão com o banco de dados estabelecida")
        yield db
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise
    finally:
        logger.debug("Conexão com o banco de dados fechada")
        db.close() 