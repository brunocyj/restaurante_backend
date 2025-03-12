"""
Repositório para mesas
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.mesa import Mesa, StatusMesa
from app.models.cardapio import TipoCardapio

class BaseRepository:
    """
    Repositório base com operações comuns.
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
    
    def delete(self, db: Session, *, id: str) -> None:
        """
        Deleta um objeto pelo ID.
        """
        try:
            obj = db.query(self.model).get(id)
            db.delete(obj)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao deletar {self.model.__name__}: {str(e)}")
        
    def get(self, db: Session, id: str) -> Optional[Any]:
        """
        Obtém um objeto pelo ID.
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            raise Exception(f"Erro ao obter {self.model.__name__}: {str(e)}")
        
    def update(self, db: Session, *, db_obj: Any, obj_in: Dict[str, Any]) -> Any:
        """
        Atualiza um objeto existente.
        """
        try:
            for field in obj_in:
                setattr(db_obj, field, obj_in[field])   
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar {self.model.__name__}: {str(e)}")


class MesaRepository(BaseRepository):
    """
    Repositório para as funcionalidades relacionadas às mesas.
    """
    
    def __init__(self):
        super().__init__(Mesa)
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, tipo_cardapio_id: Optional[UUID] = None) -> List[Mesa]:
        """
        Obtém todas as mesas.
        """
        try:
            if tipo_cardapio_id:
                return db.query(self.model).filter(self.model.tipo_cardapio_id == tipo_cardapio_id).offset(skip).limit(limit).all()
            else:
                return db.query(self.model).offset(skip).limit(limit).all()
        except Exception as e:
            raise Exception(f"Erro ao obter todas as mesas: {str(e)}")
    
    def atualizar_status(self, db: Session, id: str, novo_status: StatusMesa) -> Mesa:
        """
        Atualiza o status de uma mesa.
        """
        try:
            mesa = self.get(db, id)
            if not mesa:
                raise Exception(f"Mesa com ID {id} não encontrada")
            
            mesa.status = novo_status
            db.commit()
            db.refresh(mesa)
            return mesa
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar status da mesa: {str(e)}")

    


