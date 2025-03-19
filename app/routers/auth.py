from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.jwt import create_acess_token, create_refresh_token, verify_token, revoke_token
from app.core.security.password import verify_password
from app.core.security.deps import get_current_active_user, oauth2_scheme
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.token import Token, RefreshToken
from app.schemas.usuario import UsuarioBase as UsuarioSchema

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
    responses={
        401: {"description": "Não autorizado"},
        403: {"description": "Proibido"},
        404: {"description": "Não encontrado"},
    },
)

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Endpoint para autenticação OAuth2 com username e senha.
    Retorna um token JWT de acesso e um token de refresh.
    
    Args:
        db: Sessão do banco de dados
        form_data: Formulário com username e senha
        
    Returns:
        Token: Tokens de acesso e refresh
        
    Raises:
        HTTPException: Se as credenciais forem inválidas
    """
    user = db.query(Usuario).filter(
        Usuario.username == form_data.username,
        Usuario.ativo == True
    ).first()
    
    if not user or not verify_password(form_data.password, user.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_acess_token(
        subject=user.username,
        cargo=user.cargo,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        subject=user.username,
        cargo=user.cargo
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh-token", response_model=Token)
def refresh_token_endpoint(
    db: Session = Depends(get_db),
    refresh_token: str = None
) -> Any:
    """
    Endpoint para renovar o token de acesso usando um token de refresh.
    
    Args:
        db: Sessão do banco de dados
        refresh_token: Token de refresh
        
    Returns:
        Token: Novos tokens de acesso e refresh
        
    Raises:
        HTTPException: Se o token de refresh for inválido
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de refresh não fornecido"
        )
    
    try:
        payload = verify_token(refresh_token)
        
        if not payload.type == "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido: não é um token de refresh"
            )
        
        user = db.query(Usuario).filter(
            Usuario.username == payload.sub,
            Usuario.ativo == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado ou inativo"
            )
        
        access_token = create_acess_token(
            subject=user.username,
            cargo=user.cargo,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        new_refresh_token = create_refresh_token(
            subject=user.username,
            cargo=user.cargo
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erro ao renovar token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )



@router.get("/me", response_model=UsuarioSchema)
def read_users_me(
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    return current_user

@router.post("/logout")
def logout(
    current_user: Usuario = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, str]:
    revoke_token(token)
    
    return {"message": "Logout realizado com sucesso"}

@router.post("/logout/refresh")
def logout_refresh(
    refresh_token_data: RefreshToken
) -> Dict[str, str]:
    revoke_token(refresh_token_data.refresh_token)
    
    return {"message": "Token de refresh revogado com sucesso"} 