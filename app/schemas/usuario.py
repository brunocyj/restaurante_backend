"""schemas para o usuario"""


from typing import Optional
from pydantic import BaseModel, Field, validator
import re

class UsuarioBase(BaseModel):
    """
    schema base para o usuario
    """
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    cargo: Optional[str] = Field(default="usuario", max_length=50)
    ativo: Optional[bool] = Field(default=True)
    class Config:
        orm_mode = True

    @validator("username")
    def username_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("O nome de usuário deve conter apenas letras, números, hífens e sublinhados")
        return v
    

class Login(BaseModel):
    """
    Schema para login de usuários.
    """
    username: str = Field(..., min_length=3, max_length=50)
    senha: str = Field(..., min_length=8, max_length=50)


#sendo bem sincero a partir dessa linha para baixo não é necessãrio, mas ja são schemas criados para atualizações futuras
#caso queria criar um sistema de criação de usuarios e dar update nos cargos, no momento vai ser fito manualmente no banco de dados
class UsuarioCreate(BaseModel):
    """
    Schema para atualização de usuários.
    """
    senha: Optional[str] = Field(None, min_length=8, max_length=100)
    cargo: Optional[str] = Field(None, max_length=50)
    ativo: Optional[bool] = None
    
    @validator('senha')
    def senha_forte(cls, v):
        if v is None:
            return v
        if not re.search(r'[A-Z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('A senha deve conter pelo menos uma letra minúscula')
        return v

class UsuarioUpdate(BaseModel):
    """
    Schema para atualização de usuários.
    """
    senha: Optional[str] = Field(None, min_length=8, max_length=100)
    cargo: Optional[str] = Field(None, max_length=50)
    ativo: Optional[bool] = None    



