# Sistema de Restaurante - Backend

Backend para sistema de gerenciamento de restaurante, com recursos para cardápio, mesas, pedidos e autenticação.

## Funcionalidades

- Gerenciamento de cardápio (produtos, categorias, etc.)
- Gerenciamento de mesas
- Gerenciamento de pedidos
- Autenticação e autorização
- Sistema de notificações em tempo real

## Sistema de Notificações

O sistema de notificações utiliza Redis para armazenar e gerenciar notificações efêmeras, como:

- Chamadas de atendente
- Adição de novos itens a pedidos
- Finalização de pedidos automáticos

### Características do Sistema de Notificações

- Armazenamento em memória usando Redis
- Notificações temporárias com TTL (expiram automaticamente)
- Agregação inteligente de eventos em janelas de tempo
- API REST para gerenciar notificações

### Endpoints para Notificações

- `GET /notificacoes` - Lista todas as notificações não lidas
- `PUT /notificacoes/{id}/read` - Marca uma notificação como lida
- `DELETE /notificacoes/{id}` - Remove uma notificação
- `POST /mesas/{id}/chamar-atendente` - Endpoint para gerar uma chamada de atendente

### Estrutura das Notificações no Redis

As notificações são armazenadas em Redis utilizando os seguintes padrões de chaves:

1. **Notificação individual**:
   ```
   notification:{notification_id} → JSON com dados da notificação
   ```

2. **Lista de notificações não lidas**:
   ```
   notifications:unread → Sorted Set com IDs ordenados por timestamp
   ```

3. **Chaves de agregação temporária**:
   ```
   notification:agg:{tipo}:{entity_id} → Referência à notificação em agregação
   ```

### Como Funciona a Agregação

Quando múltiplos itens são adicionados a um pedido em um curto período de tempo (dentro da janela de agregação de 10 segundos), o sistema:

1. Verifica se existe uma notificação em agregação para aquele pedido
2. Se existir, adiciona os novos itens a essa notificação
3. Se não existir, cria uma nova notificação
4. Define uma chave de agregação temporária com TTL curto

Isso evita a geração de múltiplas notificações separadas quando vários itens são adicionados ao mesmo pedido em sequência.

## Instalação e Execução

### Requisitos

- Python 3.9+
- PostgreSQL
- Redis

### Instalação

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente (veja `.env.example`)
4. Execute as migrações:
   ```
   alembic upgrade head
   ```

### Executando o servidor

```
python run.py
```

### Executando com Docker

```
docker-compose up -d
```

## Testes

```
pytest
``` 