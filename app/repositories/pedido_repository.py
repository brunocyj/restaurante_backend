"""
Repositorio para pedidos
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy import desc
from decimal import Decimal

from app.models.pedido import Pedido, ItemPedido, StatusPedido
from app.models.cardapio import Produto
from app.models.mesa import Mesa

class PedidoRepository:
    """
    Repository para operações com pedidos
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def criar_pedido(self, mesa_id: str, itens_data: List[Dict[str, Any]], 
                    observacao_geral: Optional[str] = None, manual: bool = False) -> Pedido:
        """
        Cria um novo pedido com seus itens
        
        Args:
            mesa_id: ID da mesa
            itens_data: Lista de dicionários com dados dos itens
            observacao_geral: Observação geral do pedido
            manual: Se o pedido foi criado manualmente
            
        Returns:
            Pedido criado
        """
        mesa = self.db.query(Mesa).filter(Mesa.id == mesa_id).first()
        if not mesa:
            raise ValueError(f"Mesa com ID {mesa_id} não encontrada")
        
        valor_total = Decimal('0.00')
        
        pedido = Pedido(
            mesa_id=mesa_id,
            status=StatusPedido.ABERTO,
            valor_total=valor_total,
            observacao_geral=observacao_geral,
            manual=manual
        )
        
        self.db.add(pedido)
        self.db.flush()
        
        for item_data in itens_data:
            produto_id = item_data["produto_id"]
            quantidade = item_data["quantidade"]
            observacoes = item_data.get("observacoes")
            
            produto = self.db.query(Produto).filter(Produto.id == produto_id).first()
            if not produto:
                raise ValueError(f"Produto com ID {produto_id} não encontrado")
            
            item = ItemPedido(
                pedido_id=pedido.id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=produto.preco,
                observacoes=observacoes
            )
            
            self.db.add(item)
            
            valor_total += produto.preco * Decimal(str(quantidade))
        
        pedido.valor_total = valor_total
        
        self.db.commit()
        self.db.refresh(pedido)
        
        return pedido
    
    def obter_pedido(self, pedido_id: UUID) -> Optional[Pedido]:
        """
        Obtém um pedido pelo ID
        
        Args:
            pedido_id: ID do pedido
            
        Returns:
            Pedido encontrado ou None
        """
        return self.db.query(Pedido).filter(Pedido.id == pedido_id).first()
    
    def listar_pedidos(self, 
                      skip: int = 0, 
                      limit: int = 100, 
                      status: Optional[StatusPedido] = None,
                      mesa_id: Optional[str] = None) -> Tuple[List[Pedido], int]:
        """
        Lista pedidos com filtros opcionais
        
        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            status: Filtro por status
            mesa_id: Filtro por mesa
            
        Returns:
            Tupla com lista de pedidos e total de registros
        """
        query = self.db.query(Pedido)
        
        if status:
            query = query.filter(Pedido.status == status)
        
        if mesa_id:
            query = query.filter(Pedido.mesa_id == mesa_id)
        
        query = query.order_by(desc(Pedido.criado_em))
        
        total = query.count()
        
        pedidos = query.offset(skip).limit(limit).all()
        
        return pedidos, total
    
    def atualizar_pedido(self, pedido_id: UUID, 
                        status: Optional[StatusPedido] = None,
                        observacao_geral: Optional[str] = None,
                        mesa_id: Optional[str] = None) -> Optional[Pedido]:
        """
        Atualiza um pedido
        
        Args:
            pedido_id: ID do pedido
            status: Novo status
            observacao_geral: Nova observação geral
            
        Returns:
            Pedido atualizado ou None
        """
        pedido = self.obter_pedido(pedido_id)
        if not pedido:
            return None
        
        if status is not None:
            pedido.status = status
        
        if observacao_geral is not None:
            pedido.observacao_geral = observacao_geral

        if mesa_id is not None:
            pedido.mesa_id = mesa_id
        
        self.db.commit()
        self.db.refresh(pedido)
        
        return pedido
    
    def deletar_pedido(self, pedido_id: UUID) -> bool:
        """
        Deleta um pedido
        
        Args:
            pedido_id: ID do pedido
            
        Returns:
            True se o pedido foi deletado, False caso contrário
        """
        pedido = self.obter_pedido(pedido_id)
        if not pedido:
            return False
        
        self.db.delete(pedido)
        self.db.commit()
        
        return True
    
    def adicionar_item(self, pedido_id: UUID, produto_id: UUID, 
                      quantidade: int, observacoes: Optional[str] = None) -> Optional[ItemPedido]:
        """
        Adiciona um item a um pedido
        
        Args:
            pedido_id: ID do pedido
            produto_id: ID do produto
            quantidade: Quantidade
            observacoes: Observações
            
        Returns:
            Item adicionado ou None
        """
        pedido = self.obter_pedido(pedido_id)
        if not pedido:
            return None
        
        if pedido.status not in [StatusPedido.ABERTO, StatusPedido.EM_ANDAMENTO]:
            raise ValueError(f"Não é possível adicionar itens a um pedido com status {pedido.status}")
        
        produto = self.db.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")
        
        # Verificar se o produto já existe no pedido
        item_existente = self.db.query(ItemPedido).filter(
            ItemPedido.pedido_id == pedido_id,
            ItemPedido.produto_id == produto_id,
            # Considerar observações iguais ou ambas nulas para considerar como mesmo item
            ((ItemPedido.observacoes == observacoes) | 
             (ItemPedido.observacoes.is_(None) & (observacoes is None)))
        ).first()
        
        if item_existente:
            # Atualizar a quantidade do item existente
            valor_antigo = item_existente.preco_unitario * Decimal(str(item_existente.quantidade))
            
            # Adicionar a nova quantidade
            item_existente.quantidade += quantidade
            
            # Atualizar o valor total do pedido
            valor_novo = item_existente.preco_unitario * Decimal(str(item_existente.quantidade))
            pedido.valor_total = pedido.valor_total - valor_antigo + valor_novo
            
            self.db.commit()
            self.db.refresh(item_existente)
            
            return item_existente
        else:
            # Criar um novo item se não existir
            item = ItemPedido(
                pedido_id=pedido_id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=produto.preco,
                observacoes=observacoes
            )
            
            self.db.add(item)
            
            pedido.valor_total += produto.preco * Decimal(str(quantidade))
            
            self.db.commit()
            self.db.refresh(item)
            
            return item
    
    def atualizar_item(self, item_id: UUID, 
                      quantidade: Optional[int] = None,
                      observacoes: Optional[str] = None) -> Optional[ItemPedido]:
        """
        Atualiza um item de pedido
        
        Args:
            item_id: ID do item
            quantidade: Nova quantidade
            observacoes: Novas observações
            
        Returns:
            Item atualizado ou None
        """
        item = self.db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
        if not item:
            return None
        
        pedido = self.obter_pedido(item.pedido_id)
        
        if pedido.status not in [StatusPedido.ABERTO, StatusPedido.EM_ANDAMENTO]:
            raise ValueError(f"Não é possível alterar itens de um pedido com status {pedido.status}")
        
        valor_antigo = item.preco_unitario * Decimal(str(item.quantidade))
        
        if quantidade is not None:
            item.quantidade = quantidade
        
        if observacoes is not None:
            item.observacoes = observacoes
        
        valor_novo = item.preco_unitario * Decimal(str(item.quantidade))
        pedido.valor_total = pedido.valor_total - valor_antigo + valor_novo
        
        self.db.commit()
        self.db.refresh(item)
        
        return item
    
    def remover_item(self, item_id: UUID) -> bool:
        """
        Remove um item de pedido
        
        Args:
            item_id: ID do item
            
        Returns:
            True se o item foi removido, False caso contrário
        """
        item = self.db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
        if not item:
            return False
        
        pedido = self.obter_pedido(item.pedido_id)
        
        if pedido.status not in [StatusPedido.ABERTO, StatusPedido.EM_ANDAMENTO]:
            raise ValueError(f"Não é possível remover itens de um pedido com status {pedido.status}")
        
        valor_item = item.preco_unitario * Decimal(str(item.quantidade))
        pedido.valor_total -= valor_item
        

        itens_restantes = self.db.query(ItemPedido).filter(
            ItemPedido.pedido_id == pedido.id,
            ItemPedido.id != item_id
        ).count()
        
        if itens_restantes == 0:
            raise ValueError("Não é possível remover o último item do pedido. Delete o pedido inteiro.")
        

        self.db.delete(item)
        self.db.commit()
        
        return True