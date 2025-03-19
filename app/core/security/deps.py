"""
Dependências para autenticação e autorização.
"""
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security.jwt import verify_token
from app.core.security.token_blacklist import token_blacklist
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.token import TokenData

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scheme_name="JWT"
)

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:
    """
    Dependência para obter o usuário atual a partir do token JWT.
    
    Args:
        db: Sessão do banco de dados
        token: Token JWT de autenticação
        
    Returns:
        Usuario: Objeto do usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou o usuário não for encontrado
    """
    try:
        # Verifica se o token está na blacklist
        if token_blacklist.is_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revogado",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Verifica e decodifica o token
        payload = verify_token(token)
        token_data = TokenData(
            username=payload.sub,
            cargo=payload.cargo,
            jti=payload.jti
        )
        
        logger.debug(f"Token validado para usuário: {token_data.username}")
    except (jwt.JWTError, ValidationError) as e:
        logger.warning(f"Falha na validação do token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Busca o usuário no banco de dados
    user = db.query(Usuario).filter(
        Usuario.username == token_data.username,
        Usuario.ativo == True
    ).first()
    
    if not user:
        logger.warning(f"Usuário não encontrado ou inativo: {token_data.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado ou inativo"
        )
    
    return user

async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependência para obter o usuário atual e verificar se está ativo.
    
    Args:
        current_user: Usuário atual obtido do token
        
    Returns:
        Usuario: Objeto do usuário autenticado e ativo
        
    Raises:
        HTTPException: Se o usuário estiver inativo
    """
    if not current_user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user

def check_admin_permission(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """
    Dependência para verificar se o usuário tem permissão de administrador.
    
    Args:
        current_user: Usuário atual obtido do token
        
    Returns:
        Usuario: Objeto do usuário com permissão de administrador
        
    Raises:
        HTTPException: Se o usuário não tiver permissão de administrador
    """
    if current_user.cargo != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente"
        )
    return current_user

def check_gerente_permission(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    """
    Dependência para verificar se o usuário tem permissão de gerente ou superior.
    
    Args:
        current_user: Usuário atual obtido do token
        
    Returns:
        Usuario: Objeto do usuário com permissão de gerente ou superior
        
    Raises:
        HTTPException: Se o usuário não tiver permissão de gerente ou superior
    """
    if current_user.cargo not in ["admin", "gerente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente"
        )
    return current_user 