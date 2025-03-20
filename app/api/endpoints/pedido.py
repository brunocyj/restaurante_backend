"""
Endpoints para gerenciamento de pedidos
"""
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.pedido import StatusPedido
from app.models.usuario import Usuario
from app.repositories.pedido_repository import PedidoRepository
from app.schemas.pedido import (
    Pedido, PedidoCreate, PedidoUpdate, PedidoList,
    ItemPedidoCreate, ItemPedidoUpdate
)
from app.core.notification_service import notification_service

router = APIRouter()

@router.post("/", response_model=Pedido, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido_in: PedidoCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Cria um novo pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        # Converter itens para o formato esperado pelo repository
        itens_data = [item.dict() for item in pedido_in.itens]
        
        pedido = repository.criar_pedido(
            mesa_id=pedido_in.mesa_id,
            itens_data=itens_data,
            observacao_geral=pedido_in.observacao_geral,
            manual=pedido_in.manual
        )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar pedido: {str(e)}"
        )

@router.get("/", response_model=PedidoList)
def listar_pedidos(
    status: Optional[StatusPedido] = None,
    mesa_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Any:
    """
    Lista pedidos com filtros opcionais.
    """
    repository = PedidoRepository(db)
    pedidos, total = repository.listar_pedidos(
        skip=skip,
        limit=limit,
        status=status,
        mesa_id=mesa_id
    )
    
    return {
        "pedidos": pedidos,
        "total": total,
        "pagina": skip // limit + 1
    }

@router.get("/{pedido_id}", response_model=Pedido)
def obter_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Obtém um pedido pelo ID.
    """
    repository = PedidoRepository(db)
    pedido = repository.obter_pedido(pedido_id)
    
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    return pedido

@router.put("/{pedido_id}", response_model=Pedido)
def atualizar_pedido(
    pedido_id: UUID,
    pedido_in: PedidoUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Atualiza um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        pedido_original = repository.obter_pedido(pedido_id)
        if not pedido_original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
            
        pedido = repository.atualizar_pedido(
            pedido_id=pedido_id,
            status=pedido_in.status,
            observacao_geral=pedido_in.observacao_geral,
            mesa_id = pedido_in.mesa_id
        )
        
        status_alterado_para_finalizado = pedido_in.status == StatusPedido.FINALIZADO
        era_outro_status = pedido_original.status != StatusPedido.FINALIZADO
        eh_automatico = pedido.manual == False
        tem_mesa = pedido.mesa_id is not None

        
        deve_notificar = (status_alterado_para_finalizado and  
                          eh_automatico and 
                          tem_mesa)

        
        deve_notificar_teste = (status_alterado_para_finalizado and 
                               eh_automatico and 
                               tem_mesa)
        
        
        if deve_notificar:
            try:
                total = sum(item.quantidade * item.preco_unitario for item in pedido.itens)
                
                notification = notification_service.create_order_finalized_notification(
                    pedido_id=str(pedido_id),
                    mesa_id=str(pedido.mesa_id),
                    total=total
                )
                
                print(f"DEBUG - Notificação criada com sucesso: {notification['id']}")
                
            except Exception as e:
                print(f"Erro ao criar notificação de pedido finalizado: {str(e)}")
        else:
            print(f"DEBUG - Condições para notificação de pedido finalizado não atendidas")
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"DEBUG - Erro não esperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar pedido: {str(e)}"
        )

@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """
    Deleta um pedido.
    """
    repository = PedidoRepository(db)
    sucesso = repository.deletar_pedido(pedido_id)
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )

@router.post("/{pedido_id}/itens", response_model=Pedido)
def adicionar_item(
    pedido_id: UUID,
    item_in: ItemPedidoCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Adiciona um item a um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        # Adicionar item
        repository.adicionar_item(
            pedido_id=pedido_id,
            produto_id=item_in.produto_id,
            quantidade=item_in.quantidade,
            observacoes=item_in.observacoes
        )
        
        # Retornar pedido atualizado
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        # Criar notificação para o item adicionado apenas se o pedido for automático (manual=false)
        if pedido.mesa_id and not pedido.manual:
            try:
                # Criar item simplificado para a notificação
                item_data = {
                    "produto_id": str(item_in.produto_id),
                    "quantidade": item_in.quantidade,
                    "observacoes": item_in.observacoes
                }
                
                notification_service.create_order_items_notification(
                    pedido_id=str(pedido_id),
                    mesa_id=str(pedido.mesa_id),
                    items=[item_data]
                )
            except Exception as e:
                # Não interromper o fluxo se a notificação falhar
                print(f"Erro ao criar notificação: {str(e)}")
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar item: {str(e)}"
        )

@router.put("/{pedido_id}/itens/{item_id}", response_model=Pedido)
def atualizar_item(
    pedido_id: UUID,
    item_id: UUID,
    item_in: ItemPedidoUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Atualiza um item de um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        # Atualizar item
        repository.atualizar_item(
            item_id=item_id,
            quantidade=item_in.quantidade,
            observacoes=item_in.observacoes
        )
        
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar item: {str(e)}"
        )

@router.delete("/{pedido_id}/itens/{item_id}", response_model=Pedido)
def remover_item(
    pedido_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Remove um item de um pedido.
    """
    try:
        repository = PedidoRepository(db)
        
        sucesso = repository.remover_item(item_id)
        
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado"
            )
        
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        return pedido
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover item: {str(e)}"
        )

@router.post("/{pedido_id}/test-finalize-notification", status_code=status.HTTP_200_OK)
def testar_notificacao_pedido_finalizado(
    pedido_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Endpoint de teste para forçar a geração de notificação de pedido finalizado.
    Útil para depuração.
    """
    try:
        repository = PedidoRepository(db)
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        print(f"TESTE - Pedido ID: {pedido_id}")
        print(f"TESTE - Status: {pedido.status}")
        print(f"TESTE - Manual: {pedido.manual}")
        print(f"TESTE - Mesa ID: {pedido.mesa_id}")
        
        if not pedido.mesa_id:
            return {
                "success": False,
                "message": "Pedido não está associado a uma mesa"
            }
        
        try:
            # Calcular o total do pedido
            total = sum(item.quantidade * item.preco_unitario for item in pedido.itens)
            print(f"TESTE - Total do pedido calculado: {total}")
            
            # Forçar a criação da notificação independente das condições normais
            notification = notification_service.create_order_finalized_notification(
                pedido_id=str(pedido_id),
                mesa_id=str(pedido.mesa_id),
                total=total
            )
            
            print(f"TESTE - Notificação criada com sucesso: {notification['id']}")
            
            return {
                "success": True,
                "message": "Notificação de teste gerada com sucesso",
                "notification_id": notification["id"],
                "total": total
            }
            
        except Exception as e:
            print(f"TESTE - Erro ao criar notificação: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao criar notificação: {str(e)}"
            }
            
    except Exception as e:
        print(f"TESTE - Erro não esperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao testar notificação: {str(e)}"
        )

@router.post("/{pedido_id}/test-items-notification", status_code=status.HTTP_200_OK)
def testar_notificacao_itens_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    Endpoint de teste para testar o mecanismo de agregação de notificações de itens.
    Envia várias notificações de itens e verifica o comportamento de agregação no Redis.
    """
    try:
        repository = PedidoRepository(db)
        pedido = repository.obter_pedido(pedido_id)
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        
        print(f"TESTE AGREGAÇÃO - Pedido ID: {pedido_id}")
        print(f"TESTE AGREGAÇÃO - Mesa ID: {pedido.mesa_id}")
        
        if not pedido.mesa_id:
            return {
                "success": False,
                "message": "Pedido não está associado a uma mesa"
            }
        
        # Preparar itens de teste
        item_test_1 = {
            "produto_id": "item-teste-1",
            "quantidade": 1,
            "observacoes": "Teste de agregação 1"
        }
        
        item_test_2 = {
            "produto_id": "item-teste-2",
            "quantidade": 2,
            "observacoes": "Teste de agregação 2"
        }
        
        item_test_3 = {
            "produto_id": "item-teste-3",
            "quantidade": 3,
            "observacoes": "Teste de agregação 3"
        }
        
        notifications = []
        
        try:
            # Enviar 3 notificações sequenciais para testar agregação
            print("TESTE AGREGAÇÃO - Enviando notificação 1")
            notification1 = notification_service.create_order_items_notification(
                pedido_id=str(pedido_id),
                mesa_id=str(pedido.mesa_id),
                items=[item_test_1]
            )
            notifications.append(notification1)
            print(f"TESTE AGREGAÇÃO - Notificação 1 criada: {notification1['id']}")
            
            # Aguardar um instante para simular intervalo entre chamadas
            import time
            time.sleep(0.5)
            
            print("TESTE AGREGAÇÃO - Enviando notificação 2")
            notification2 = notification_service.create_order_items_notification(
                pedido_id=str(pedido_id),
                mesa_id=str(pedido.mesa_id),
                items=[item_test_2]
            )
            notifications.append(notification2)
            print(f"TESTE AGREGAÇÃO - Notificação 2 criada: {notification2['id']}")
            
            time.sleep(0.5)
            
            print("TESTE AGREGAÇÃO - Enviando notificação 3")
            notification3 = notification_service.create_order_items_notification(
                pedido_id=str(pedido_id),
                mesa_id=str(pedido.mesa_id),
                items=[item_test_3]
            )
            notifications.append(notification3)
            print(f"TESTE AGREGAÇÃO - Notificação 3 criada: {notification3['id']}")
            
            # Verificar se as notificações foram agregadas (terão o mesmo ID)
            ids_unicos = set([n['id'] for n in notifications])
            foram_agregadas = len(ids_unicos) < len(notifications)
            
            # Contar itens na última notificação
            ultimo_count = notifications[-1].get('count', 0)
            
            return {
                "success": True,
                "message": "Teste de agregação concluído",
                "notification_ids": [n['id'] for n in notifications],
                "foram_agregadas": foram_agregadas,
                "ids_unicos": list(ids_unicos),
                "num_itens_ultima_notificacao": ultimo_count,
                "janela_agregacao_segundos": notification_service.AGGREGATION_WINDOW
            }
            
        except Exception as e:
            print(f"TESTE AGREGAÇÃO - Erro: {str(e)}")
            return {
                "success": False,
                "message": f"Erro durante teste de agregação: {str(e)}"
            }
            
    except Exception as e:
        print(f"TESTE AGREGAÇÃO - Erro não esperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao testar agregação de notificações: {str(e)}"
        )
