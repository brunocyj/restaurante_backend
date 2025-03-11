"""
Módulo para gerenciamento de tokens revogados (blacklist).
"""
from datetime import datetime
from typing import  Optional
import threading
import logging

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

class TokenBlacklist:
    """
    Classe para gerenciar tokens revogados (blacklist).
    
    Esta implementação usa Redis como armazenamento principal,
    com fallback para armazenamento em memória quando o Redis
    não está disponível.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TokenBlacklist, cls).__new__(cls)
                cls._instance.blacklist = set()
                cls._instance.jti_blacklist = set()
                cls._instance.expiry_times = {}
            return cls._instance
    
    def add_to_blacklist(self, token: str, expires_at: Optional[datetime] = None) -> None:
        """
        Adiciona um token à blacklist.
        
        Args:
            token: Token a ser adicionado à blacklist
            expires_at: Data de expiração do token
        """
        # Calcula o tempo de expiração em segundos
        expiry_seconds = None
        if expires_at:
            now = datetime.utcnow()
            if expires_at > now:
                expiry_seconds = int((expires_at - now).total_seconds())
        
        # Tenta adicionar ao Redis primeiro
        token_key = f"blacklist:token:{token}"
        if redis_client.is_connected():
            # Adiciona o token ao Redis com expiração automática
            if expiry_seconds:
                redis_client.set_key(token_key, "1", expiry_seconds)
            else:
                # Se não tiver expiração, usa um valor padrão de 24 horas
                redis_client.set_key(token_key, "1", 86400)  # 24 horas em segundos
            
            logger.debug(f"Token adicionado à blacklist no Redis: {token[:10]}...")
        else:
            # Fallback: armazena em memória
            self.blacklist.add(token)
            if expires_at:
                self.expiry_times[token] = expires_at
            
            logger.debug(f"Token adicionado à blacklist em memória: {token[:10]}...")
    
    def add_jti_to_blacklist(self, jti: str, expires_at: Optional[datetime] = None) -> None:
        """
        Adiciona um JTI (JWT ID) à blacklist.
        
        Args:
            jti: JTI a ser adicionado à blacklist
            expires_at: Data de expiração do token
        """
        # Calcula o tempo de expiração em segundos
        expiry_seconds = None
        if expires_at:
            now = datetime.utcnow()
            if expires_at > now:
                expiry_seconds = int((expires_at - now).total_seconds())
        
        # Tenta adicionar ao Redis primeiro
        jti_key = f"blacklist:jti:{jti}"
        if redis_client.is_connected():
            # Adiciona o JTI ao Redis com expiração automática
            if expiry_seconds:
                redis_client.set_key(jti_key, "1", expiry_seconds)
            else:
                # Se não tiver expiração, usa um valor padrão de 30 dias
                redis_client.set_key(jti_key, "1", 2592000)  # 30 dias em segundos
            
            logger.debug(f"JTI adicionado à blacklist no Redis: {jti}")
        else:
            # Fallback: armazena em memória
            self.jti_blacklist.add(jti)
            
            logger.debug(f"JTI adicionado à blacklist em memória: {jti}")
    
    def is_blacklisted(self, token: str) -> bool:
        """
        Verifica se um token está na blacklist.
        
        Args:
            token: Token a ser verificado
            
        Returns:
            bool: True se o token estiver na blacklist, False caso contrário
        """
        # Tenta verificar no Redis primeiro
        token_key = f"blacklist:token:{token}"
        if redis_client.is_connected():
            return redis_client.key_exists(token_key)
        
        # Fallback: verifica em memória
        self._clean_expired_tokens()
        return token in self.blacklist
    
    def is_jti_blacklisted(self, jti: str) -> bool:
        """
        Verifica se um JTI está na blacklist.
        
        Args:
            jti: JTI a ser verificado
            
        Returns:
            bool: True se o JTI estiver na blacklist, False caso contrário
        """
        # Tenta verificar no Redis primeiro
        jti_key = f"blacklist:jti:{jti}"
        if redis_client.is_connected():
            return redis_client.key_exists(jti_key)
        
        # Fallback: verifica em memória
        return jti in self.jti_blacklist
    
    def _clean_expired_tokens(self) -> None:
        """
        Remove tokens expirados da blacklist em memória.
        
        Nota: No Redis, a expiração é automática.
        """
        now = datetime.utcnow()
        expired_tokens = [
            token for token, expires_at in self.expiry_times.items()
            if expires_at < now
        ]
        
        for token in expired_tokens:
            self.blacklist.discard(token)
            del self.expiry_times[token]

# Instância global da blacklist
token_blacklist = TokenBlacklist() 