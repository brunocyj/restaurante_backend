import time
import pytest
from unittest.mock import MagicMock, patch
from app.core.notification_service import NotificationService, NotificationType

@pytest.fixture
def mock_redis():
    redis_mock = MagicMock()
    redis_mock.set_key.return_value = True
    redis_mock.get_key.return_value = None
    redis_mock.delete_key.return_value = True
    redis_mock.client.zadd.return_value = 1
    redis_mock.client.zrevrange.return_value = []
    redis_mock.client.expire.return_value = True
    redis_mock.client.zrem.return_value = 1
    return redis_mock

@pytest.fixture
def notification_service(mock_redis):
    service = NotificationService()
    service.redis = mock_redis
    return service

def test_create_notification_basic(notification_service):
    """Teste de criação de notificação básica"""
    # Arrange
    notification_type = NotificationType.WAITER_CALL
    entity_id = "test-entity"
    content = {"test": "content"}
    
    # Act
    result = notification_service.create_notification(
        notification_type=notification_type,
        entity_id=entity_id,
        content=content
    )
    
    # Assert
    assert result["type"] == notification_type.value
    assert result["entity_id"] == entity_id
    assert result["content"] == content
    assert result["read"] == False
    
    # Verificar se o Redis foi chamado corretamente
    notification_service.redis.set_key.assert_called()
    notification_service.redis.client.zadd.assert_called_once()
    notification_service.redis.client.expire.assert_called_once()

def test_create_notification_with_aggregation(notification_service, mock_redis):
    """Teste de criação de notificação com agregação"""
    # Arrange
    notification_type = NotificationType.ORDER_ITEMS_ADDED
    entity_id = "test-pedido"
    content1 = {
        "pedido_id": entity_id,
        "mesa_id": "test-mesa",
        "items": [{"id": "item1"}],
        "message": "Mensagem 1"
    }
    content2 = {
        "pedido_id": entity_id,
        "mesa_id": "test-mesa",
        "items": [{"id": "item2"}],
        "message": "Mensagem 2"
    }
    
    # Primeira notificação
    result1 = notification_service.create_notification(
        notification_type=notification_type,
        entity_id=entity_id,
        content=content1,
        aggregate=True
    )
    
    # Simular que a chave de agregação foi encontrada
    mock_redis.get_key.side_effect = lambda key: (
        notification_service._serialize({
            "notification_id": result1["id"],
            "last_update": int(time.time())
        }) 
        if "notification:agg:" in key
        else notification_service._serialize(result1) 
        if f"notification:{result1['id']}" in key 
        else None
    )
    
    # Segunda notificação (deve ser agregada)
    result2 = notification_service.create_notification(
        notification_type=notification_type,
        entity_id=entity_id,
        content=content2,
        aggregate=True
    )
    
    # Assert
    assert result2["id"] == result1["id"]  # Mesmo ID (agregado)
    assert len(result2["items"]) == 2  # Dois itens na lista
    assert result2["count"] == 2  # Contador atualizado
    assert "updated_at" in result2  # Timestamp atualizado
    
    # Verificar se o Redis foi chamado corretamente para agregação
    assert mock_redis.set_key.call_count >= 3  # 1 para primeira notificação, 1+ para agregação

def test_create_waiter_call_notification(notification_service):
    """Teste da função auxiliar para criar notificação de chamada de atendente"""
    # Arrange
    mesa_id = "test-mesa"
    
    # Act
    with patch.object(notification_service, 'create_notification') as mock_create:
        mock_create.return_value = {"id": "test-id"}
        result = notification_service.create_waiter_call_notification(mesa_id)
    
    # Assert
    assert result == {"id": "test-id"}
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    assert kwargs["notification_type"] == NotificationType.WAITER_CALL
    assert kwargs["entity_id"] == mesa_id
    assert "mesa_id" in kwargs["content"]
    assert "message" in kwargs["content"]

def test_create_order_items_notification(notification_service):
    """Teste da função auxiliar para criar notificação de itens adicionados"""
    # Arrange
    pedido_id = "test-pedido"
    mesa_id = "test-mesa"
    items = [{"id": "item1", "quantidade": 2}]
    
    # Act
    with patch.object(notification_service, 'create_notification') as mock_create:
        mock_create.return_value = {"id": "test-id"}
        result = notification_service.create_order_items_notification(pedido_id, mesa_id, items)
    
    # Assert
    assert result == {"id": "test-id"}
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    assert kwargs["notification_type"] == NotificationType.ORDER_ITEMS_ADDED
    assert kwargs["entity_id"] == pedido_id
    assert kwargs["content"]["mesa_id"] == mesa_id
    assert kwargs["content"]["items"] == items
    assert kwargs["aggregate"] == True  # Verificar se a agregação está ativada

def test_create_order_finalized_notification(notification_service):
    """Teste da função auxiliar para criar notificação de pedido finalizado"""
    # Arrange
    pedido_id = "test-pedido"
    mesa_id = "test-mesa"
    total = 123.45
    
    # Act
    with patch.object(notification_service, 'create_notification') as mock_create:
        mock_create.return_value = {"id": "test-id"}
        result = notification_service.create_order_finalized_notification(pedido_id, mesa_id, total)
    
    # Assert
    assert result == {"id": "test-id"}
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    assert kwargs["notification_type"] == NotificationType.ORDER_FINALIZED
    assert kwargs["entity_id"] == pedido_id
    assert kwargs["content"]["mesa_id"] == mesa_id
    assert kwargs["content"]["total"] == total
    assert "message" in kwargs["content"]

def test_get_unread_notifications(notification_service, mock_redis):
    """Teste para recuperar notificações não lidas"""
    # Arrange
    mock_redis.client.zrevrange.return_value = ["notif1", "notif2"]
    
    mock_redis.get_key.side_effect = lambda key: (
        '{"id": "notif1", "content": {"message": "Test 1"}}' if "notif1" in key 
        else '{"id": "notif2", "content": {"message": "Test 2"}}' if "notif2" in key 
        else None
    )
    
    # Act
    results = notification_service.get_unread_notifications(limit=10)
    
    # Assert
    assert len(results) == 2
    assert results[0]["id"] == "notif1"
    assert results[1]["id"] == "notif2"
    mock_redis.client.zrevrange.assert_called_once_with(
        notification_service.NOTIFICATION_LIST_KEY, 0, 9
    )

def test_mark_as_read(notification_service, mock_redis):
    """Teste para marcar notificação como lida"""
    # Arrange
    notification_id = "test-notification"
    mock_notification = {
        "id": notification_id,
        "type": NotificationType.WAITER_CALL.value,
        "content": {"message": "Test"},
        "read": False
    }
    
    mock_redis.get_key.return_value = notification_service._serialize(mock_notification)
    
    # Act
    result = notification_service.mark_as_read(notification_id)
    
    # Assert
    assert result == True
    
    # Verificar se o Redis foi chamado corretamente
    mock_redis.set_key.assert_called_once()
    args, kwargs = mock_redis.set_key.call_args
    updated_notification = notification_service._deserialize(args[1])
    assert updated_notification["read"] == True  # Verificar se foi marcado como lido
    
    mock_redis.client.zrem.assert_called_once_with(
        notification_service.NOTIFICATION_LIST_KEY, notification_id
    )

def test_delete_notification(notification_service, mock_redis):
    """Teste para remover notificação"""
    # Arrange
    notification_id = "test-notification"
    
    # Act
    result = notification_service.delete_notification(notification_id)
    
    # Assert
    assert result == True
    mock_redis.delete_key.assert_called_once()
    mock_redis.client.zrem.assert_called_once_with(
        notification_service.NOTIFICATION_LIST_KEY, notification_id
    ) 