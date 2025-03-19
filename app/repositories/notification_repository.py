"""
Repositório para notificações
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models.notification import Notificacao, tipos_notificacao
from datetime import datetime
from uuid import UUID

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

    
class NotificacaoRepository(BaseRepository):
    """
    Repositório para notificações
    """
    
    def __init__(self):
        super().__init__(Notificacao)

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Notificacao]:
        """
        Obtém todas as notificações.
        """
        try:
            return db.query(self.model).offset(skip).limit(limit).all()
        except Exception as e:
            raise Exception(f"Erro ao obter todas as notificações: {str(e)}")
    
    def get_active_notifications(self, db: Session, *, mesa_id: Optional[str] = None) -> List[Notificacao]:
        """
        Obtém notificações ativas (não lidas).
        
        Args:
            db: Sessão do banco de dados
            mesa_id: ID da mesa (opcional)
            
        Returns:
            Lista de notificações ativas
        """
        try:
            query = db.query(self.model).filter(self.model.status == True)
            
            if mesa_id:
                query = query.filter(self.model.mesa_id == mesa_id)
                
            return query.all()
        except Exception as e:
            raise Exception(f"Erro ao obter notificações ativas: {str(e)}")
    
    def mark_as_read(self, db: Session, *, notification_id: UUID) -> bool:
        """
        Marca uma notificação como lida.
        
        Args:
            db: Sessão do banco de dados
            notification_id: ID da notificação
            
        Returns:
            True se marcada com sucesso, False caso contrário
        """
        try:
            notification = self.get(db, str(notification_id))
            if not notification:
                return False
            
            notification.status = False
            db.commit()
            db.refresh(notification)
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao marcar notificação como lida: {str(e)}")
    
    def create_notification(
        self, 
        db: Session, 
        *, 
        mesa_id: str,
        tipo: tipos_notificacao,
        mensagem: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None
    ) -> Notificacao:
        """
        Cria uma nova notificação.
        
        Args:
            db: Sessão do banco de dados
            mesa_id: ID da mesa
            tipo: Tipo da notificação
            mensagem: Mensagem da notificação
            detalhes: Detalhes adicionais em formato JSON
            
        Returns:
            A notificação criada
        """
        obj_in = {
            "mesa_id": mesa_id,
            "tipo": tipo,
            "mensagem": mensagem,
            "detalhes": detalhes,
            "status": True
        }
        
        return self.create(db, obj_in=obj_in)

notificacao_repository = NotificacaoRepository()