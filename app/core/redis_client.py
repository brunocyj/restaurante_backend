import redis
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Cliente Redis para armazenamento de tokens revogados e cache.
    
    Esta classe implementa o padrão Singleton para garantir
    que apenas uma conexão com o Redis seja criada.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance
    
    def _initialize_connection(self):
        """
        Inicializa a conexão com o Redis.
        """
        try:
            redis_host = settings.REDIS_HOST
            redis_port = settings.REDIS_PORT
            redis_password = settings.REDIS_PASSWORD
            redis_db = settings.REDIS_DB
            
            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password if redis_password else None,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
            )
            
            self.client.ping()
            logger.info("Conexão com REDIS em funcionamento!")
            
        except Exception as e:
            logger.warning(f"Não foi possível conectar ao Redis: {str(e)}")
            logger.warning("Usando fallback em memória para blacklist de tokens")
            self.client = None
    
    def is_connected(self) -> bool:
        if not self.client:
            return False
        
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def set_key(self, key: str, value: str, expiry_seconds: Optional[int] = None) -> bool:
        """
        Define um valor para uma chave no Redis.
        
        Args:
            key: Chave a ser definida
            value: Valor a ser armazenado
            expiry_seconds: Tempo de expiração em segundos (opcional)
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        if not self.is_connected():
            return False
        
        try:
            if expiry_seconds:
                return self.client.setex(key, expiry_seconds, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Erro ao definir chave no Redis: {str(e)}")
            return False
    
    def get_key(self, key: str) -> Optional[str]:
        """
        Obtém o valor de uma chave no Redis.
        
        Args:
            key: Chave a ser obtida
            
        Returns:
            Optional[str]: Valor da chave ou None se não existir
        """
        if not self.is_connected():
            return None
        
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Erro ao obter chave do Redis: {str(e)}")
            return None
    
    def delete_key(self, key: str) -> bool:
        """
        Remove uma chave do Redis.
        
        Args:
            key: Chave a ser removida
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        if not self.is_connected():
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Erro ao remover chave do Redis: {str(e)}")
            return False
    
    def key_exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no Redis.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            bool: True se a chave existir, False caso contrário
        """
        if not self.is_connected():
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Erro ao verificar existência de chave no Redis: {str(e)}")
            return False

redis_client = RedisClient() 