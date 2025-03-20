import json
import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Tipos de notificações possíveis no sistema"""
    WAITER_CALL = "waiter_call"
    ORDER_ITEMS_ADDED = "order_items_added"
    ORDER_FINALIZED = "order_finalized"


class NotificationService:
    """
    Serviço para gerenciamento de notificações usando Redis.
    
    Este serviço permite:
    - Criar notificações de diferentes tipos
    - Agregar múltiplas notificações do mesmo tipo em uma janela de tempo
    - Recuperar notificações não lidas
    - Marcar notificações como lidas
    """
    
    # Prefixos para as chaves do Redis
    NOTIFICATION_KEY = "notification:{notification_id}"
    NOTIFICATION_LIST_KEY = "notifications:unread"
    NOTIFICATION_AGGREGATION_KEY = "notification:agg:{type}:{entity_id}"
    
    # TTL padrão para notificações (em segundos)
    DEFAULT_TTL = 24 * 60 * 60  # 24 horas
    
    # Janela de agregação para notificações do mesmo tipo (em segundos)
    AGGREGATION_WINDOW = 10  # 10 segundos
    
    def __init__(self):
        self.redis = redis_client
    
    def _generate_id(self) -> str:
        """Gera um ID único para uma notificação"""
        return str(uuid4())
    
    def _serialize(self, obj: Any) -> str:
        """Serializa um objeto para JSON"""
        return json.dumps(obj, default=str)
    
    def _deserialize(self, json_str: str) -> Dict:
        """Deserializa uma string JSON para um objeto"""
        if not json_str:
            return {}
        return json.loads(json_str)
    
    def create_notification(
        self, 
        notification_type: NotificationType, 
        entity_id: str, 
        content: Dict[str, Any],
        ttl: Optional[int] = None,
        aggregate: bool = False
    ) -> Dict[str, Any]:
        """
        Cria uma nova notificação, com opção de agregação.
        
        Args:
            notification_type: Tipo da notificação
            entity_id: ID da entidade relacionada (mesa, pedido, etc.)
            content: Conteúdo da notificação
            ttl: Tempo de vida da notificação em segundos
            aggregate: Se deve tentar agregar com notificações existentes
            
        Returns:
            Dict: A notificação criada
        """
        timestamp = int(time.time())
        notification_id = None
        notification = None
        is_new = True
        
        # Se a agregação estiver ativada, verificar se existe notificação para agregar
        if aggregate:
            agg_key = self.NOTIFICATION_AGGREGATION_KEY.format(
                type=notification_type.value,
                entity_id=entity_id
            )
            
            # Verificar se existe uma chave de agregação ativa
            agg_data = self.redis.get_key(agg_key)
            if agg_data:
                agg_data = self._deserialize(agg_data)
                notification_id = agg_data.get("notification_id")
                
                if notification_id:
                    # Recuperar a notificação existente
                    notification_key = self.NOTIFICATION_KEY.format(notification_id=notification_id)
                    notif_data = self.redis.get_key(notification_key)
                    
                    if notif_data:
                        notification = self._deserialize(notif_data)
                        is_new = False
                        
                        # Atualizar a notificação existente com o novo item
                        if "items" not in notification:
                            notification["items"] = []
                            notification["count"] = 0
                        
                        notification["items"].append(content)
                        notification["count"] = len(notification["items"])
                        notification["updated_at"] = timestamp
                        
                        # Atualizar o conteúdo principal da notificação
                        if notification_type == NotificationType.ORDER_ITEMS_ADDED:
                            notification["content"] = {
                                "pedido_id": content.get("pedido_id"),
                                "mesa_id": content.get("mesa_id"),
                                "message": f"{notification['count']} itens adicionados ao pedido da mesa {content.get('mesa_id')}"
                            }
        
        # Se não há notificação para agregar, criar uma nova
        if not notification:
            notification_id = self._generate_id()
            notification = {
                "id": notification_id,
                "type": notification_type.value,
                "entity_id": entity_id,
                "content": content,
                "items": [content] if aggregate else None,
                "count": 1 if aggregate else None,
                "created_at": timestamp,
                "updated_at": timestamp,
                "read": False
            }
        
        # Salvar a notificação
        notification_key = self.NOTIFICATION_KEY.format(notification_id=notification_id)
        self.redis.set_key(
            notification_key, 
            self._serialize(notification), 
            ttl or self.DEFAULT_TTL
        )
        
        # Se a agregação estiver ativada, atualizar a chave de agregação
        if aggregate:
            agg_key = self.NOTIFICATION_AGGREGATION_KEY.format(
                type=notification_type.value,
                entity_id=entity_id
            )
            
            agg_data = {
                "notification_id": notification_id,
                "last_update": timestamp
            }
            
            self.redis.set_key(
                agg_key,
                self._serialize(agg_data),
                self.AGGREGATION_WINDOW
            )
        
        # Se for uma nova notificação, adicionar à lista de não lidas
        if is_new:
            self.redis.client.zadd(
                self.NOTIFICATION_LIST_KEY,
                {notification_id: timestamp}
            )
            # Definir TTL na lista de não lidas
            self.redis.client.expire(self.NOTIFICATION_LIST_KEY, ttl or self.DEFAULT_TTL)
        
        return notification
    
    def create_waiter_call_notification(self, mesa_id: str) -> Dict[str, Any]:
        """
        Cria uma notificação de chamada de atendente.
        
        Args:
            mesa_id: ID da mesa que solicitou atendente
            
        Returns:
            Dict: A notificação criada
        """
        content = {
            "mesa_id": mesa_id,
            "message": f"Mesa {mesa_id} solicitou atendente"
        }
        
        return self.create_notification(
            notification_type=NotificationType.WAITER_CALL,
            entity_id=mesa_id,
            content=content
        )
    
    def create_order_items_notification(self, pedido_id: str, mesa_id: str, items: List[Dict]) -> Dict[str, Any]:
        """
        Cria uma notificação de itens adicionados ao pedido.
        
        Args:
            pedido_id: ID do pedido
            mesa_id: ID da mesa
            items: Lista de itens adicionados
            
        Returns:
            Dict: A notificação criada
        """
        content = {
            "pedido_id": pedido_id,
            "mesa_id": mesa_id,
            "items": items,
            "message": f"Novos itens adicionados ao pedido da mesa {mesa_id}"
        }
        
        return self.create_notification(
            notification_type=NotificationType.ORDER_ITEMS_ADDED,
            entity_id=pedido_id,
            content=content,
            aggregate=True  # Ativar agregação para itens de pedidos
        )
    
    def create_order_finalized_notification(self, pedido_id: str, mesa_id: str, total: float) -> Dict[str, Any]:
        """
        Cria uma notificação de pedido finalizado.
        
        Args:
            pedido_id: ID do pedido
            mesa_id: ID da mesa
            total: Valor total do pedido
            
        Returns:
            Dict: A notificação criada
        """
        content = {
            "pedido_id": pedido_id,
            "mesa_id": mesa_id,
            "total": total,
            "message": f"Pedido da mesa {mesa_id} finalizado no valor de R$ {total:.2f}"
        }
        
        return self.create_notification(
            notification_type=NotificationType.ORDER_FINALIZED,
            entity_id=pedido_id,
            content=content
        )
    
    def get_unread_notifications(self, limit: int = 50) -> List[Dict]:
        """
        Recupera notificações não lidas.
        
        Args:
            limit: Número máximo de notificações a retornar
            
        Returns:
            List[Dict]: Lista de notificações não lidas
        """
        # Obter IDs das notificações não lidas, ordenadas por timestamp (mais recentes primeiro)
        notification_ids = self.redis.client.zrevrange(self.NOTIFICATION_LIST_KEY, 0, limit - 1)
        
        notifications = []
        for notification_id in notification_ids:
            notification_key = self.NOTIFICATION_KEY.format(notification_id=notification_id)
            notification_data = self.redis.get_key(notification_key)
            if notification_data:
                notification = self._deserialize(notification_data)
                notifications.append(notification)
        
        return notifications
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        Marca uma notificação como lida.
        
        Args:
            notification_id: ID da notificação
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        notification_key = self.NOTIFICATION_KEY.format(notification_id=notification_id)
        notification_data = self.redis.get_key(notification_key)
        
        if not notification_data:
            return False
        
        notification = self._deserialize(notification_data)
        notification["read"] = True
        
        # Atualizar notificação
        success = self.redis.set_key(
            notification_key, 
            self._serialize(notification), 
            self.DEFAULT_TTL
        )
        
        # Remover da lista de não lidas
        if success:
            self.redis.client.zrem(self.NOTIFICATION_LIST_KEY, notification_id)
        
        return success
    
    def delete_notification(self, notification_id: str) -> bool:
        """
        Remove uma notificação.
        
        Args:
            notification_id: ID da notificação
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        notification_key = self.NOTIFICATION_KEY.format(notification_id=notification_id)
        success = self.redis.delete_key(notification_key)
        
        # Remover da lista de não lidas
        if success:
            self.redis.client.zrem(self.NOTIFICATION_LIST_KEY, notification_id)
        
        return success


# Instância global do serviço de notificações
notification_service = NotificationService() 