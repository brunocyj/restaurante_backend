"""
schemas para o token
"""

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """
    Schema para o token
    """
    access_token: str
    refresh_token: str
    token_type: str

#nao me pergunte o porque disso
class TokenPayload(BaseModel):
    """
    Schema para o payload do token
    """
    sub: Optional[str] = None
    exp: Optional[int] = None 
    cargo: Optional[str] = None
    type: Optional[str] = None
    jti: Optional[str] = None
    iat: Optional[int] = None

class TokenData(BaseModel):
    """
    Schema para o token data
    """
    username: Optional[str] = None
    cargo: Optional[str] = None
    jti: Optional[str] = None

class RefreshToken(BaseModel):
    """
    Schema para o refresh token
    """
    refresh_token: str


