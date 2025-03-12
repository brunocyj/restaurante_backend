"""
jwt para autenticação e autorização
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from jose import jwt, JWTError
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenPayload
from app.core.security.token_blacklist import token_blacklist

ALGORITHM = "HS256"
logger = logging.getLogger(__name__)

def create_acess_token(
        subject: str,
        cargo: Optional[str] = None,
        expires_delta : Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT de acesso

    Args:
        subject: str
        cargo: Optional[str] = None
        expires_delta: Optional[timedelta] = None

    Returns:
        str: Token JWT de acesso
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "jti": str(uuid.uuid4()),
        "iat": datetime.utcnow(),

    }

    if cargo:
        to_encode["cargo"] = cargo

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
        subject: str,
        cargo: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT de atualização(REFRESH TOKEN)

    Args:
        subject: str
        cargo: Optional[str] = None
        expires_delta: Optional[timedelta] = None

    Returns:
        str: Token JWT de atualização
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(7)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "jti": str(uuid.uuid4()),
        "iat": datetime.utcnow(),
        "type": "refresh",


    }
    if cargo:
        to_encode["cargo"] = cargo

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenPayload:
    """
    Verifica e decodifica um token JWT

    Args:
        token: str

    Returns:
        TokenPayload: Payload do token
    """
    try:
        if token_blacklist.is_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revogado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti and token_blacklist.is_jti_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revogado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenPayload(**payload)

        if token_data.exp and datetime.utcnow() > datetime.fromtimestamp(token_data.exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return token_data
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
def revoke_token(token: str) -> None:
    """
    Revoga um token JWT
    
    Args:
        token: Token JWT a ser revogado
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp) if exp else None

        token_blacklist.add_to_blacklist(token, expires_at)

        jti = payload.get("jti")
        if jti:
            token_blacklist.add_jti_to_blacklist(jti, expires_at)
            logger.info(f"Token JWT revogado: {token[:10]}...")

    except (JWTError, ValidationError) as e :
        logger.error(f"Erro ao revogar token: {token[:10]}... : {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )