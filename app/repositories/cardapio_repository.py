"""
Repositorio para as funcionalidades relacionadas ao cardápio.
"""
from typing import  List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, asc
from uuid import UUID

from app.models.cardapio import TipoCardapio, Categoria, Produto

class BaseRepository:
    """
    Repositorio para as funcionalidades relacionadas ao tipo de cardápio.
    """
    
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> Any:
        """
        Cria um novo objeto.
        """
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao criar {self.model.__name__}: {str(e)}")
        
    def get(self, db: Session, id: UUID) -> Optional[Any]:
        """
        Obtém um objeto pelo ID.
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            raise Exception(f"Erro ao obter {self.model.__name__}: {str(e)}")
        
    def update(self, db: Session, *, db_obj: Any, obj_in: Dict[str, Any]) -> Any:
        """
        Atualiza um objeto.
        """
        try:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar {self.model.__name__}: {str(e)}")
        
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Any]:
        """
        Obtém vários objetos.
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def delete(self, db: Session, *, id: UUID) -> None:
        """
        Deleta um objeto.
        """
        obj = db.query(self.model).filter(self.model.id == id).first()
        db.delete(obj)
        db.commit()
        return obj
    
    def desativar(self, db: Session, *, id: UUID) -> None:
        """
        Desativa um objeto.
        """
        obj = db.query(self.model).filter(self.model.id == id).first()
        obj.ativo = False
        db.commit()
        db.refresh(obj)
        return obj

class TipoCardapioRepository(BaseRepository):
    """
    Repositorio para as funcionalidades relacionadas ao tipo de cardápio.
    """
    
    def __init__(self):
        super().__init__(TipoCardapio)
    
    
class CategoriaRepository(BaseRepository):
    """
    Repositorio para as funcionalidades relacionadas às categorias de cardápio.
    """
    
    def __init__(self):
        super().__init__(Categoria)

class ProdutoRepository(BaseRepository):
    """
    Repositorio para as funcionalidades relacionadas aos produtos de cardápio.
    """
    
    def __init__(self):
        super().__init__(Produto)

        
