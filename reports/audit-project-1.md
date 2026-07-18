================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1 (+ flask-cors 5.0.1)
Dependencies:  flask (web framework), flask-cors (CORS), sqlite3 (stdlib, driver de banco)
Domain:        API de E-commerce (produtos, usuários/clientes, pedidos, login, relatório de vendas)
Architecture:  Separação nominal em 4 arquivos na raiz — app.py (definição de rotas via
               add_url_rule + 2 endpoints inline de admin), controllers.py (handlers HTTP com
               validação de entrada misturada à lógica de resposta), models.py (acesso a dados
               via SQL cru montado por concatenação de string, sem ORM), database.py (conexão
               global single-instance + criação de schema + seed). Não há camada de service,
               nem de configuração externa (secrets e flags ficam hardcoded em app.py).
Source files:  4 files analyzed (app.py, controllers.py, database.py, models.py) | ~780 lines
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite, loja.db)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project (API de E-commerce)
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 13

## Findings

### [LOW] print() como mecanismo de logging
File: controllers.py:8
Description: `print("Listando " + str(len(produtos)) + " produtos")` registra evento de runtime (sucesso da listagem) dentro do handler `listar_produtos`.
Impact: Log sem nível, timestamp ou destino configurável; não pode ser filtrado/roteado em produção; mistura diagnóstico com stdout.
Recommendation: Substituir por logger configurável (ex: módulo `logging`) — ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: controllers.py:11
Description: `print("ERRO: " + str(e))` no bloco `except` de `listar_produtos` reporta falha via stdout.
Impact: Erros não têm nível (ex: ERROR) nem stack trace estruturado; impossível monitorar/alertar em produção.
Recommendation: Substituir por `logger.error(...)`, idealmente com `exc_info=True`.

### [LOW] print() como mecanismo de logging
File: controllers.py:57
Description: `print("Produto criado com ID: " + str(id))` registra sucesso da criação de produto em `criar_produto`.
Impact: Mesmo problema de ausência de nível/roteamento/timestamp.
Recommendation: Substituir por `logger.info(...)`.

### [LOW] print() como mecanismo de logging
File: controllers.py:61
Description: `print("ERRO ao criar produto: " + str(e))` no bloco `except` de `criar_produto`.
Impact: Falha de criação de produto não é rastreável de forma estruturada em produção.
Recommendation: Substituir por `logger.error(...)`.

### [LOW] print() como mecanismo de logging
File: controllers.py:106
Description: `print("Produto " + str(id) + " deletado")` registra sucesso da exclusão em `deletar_produto`.
Impact: Mesmo problema de ausência de nível/roteamento/timestamp.
Recommendation: Substituir por `logger.info(...)`.

### [LOW] print() como mecanismo de logging
File: controllers.py:161
Description: `print("Usuário criado: " + email)` registra sucesso da criação de usuário em `criar_usuario`, incluindo o e-mail do usuário no stdout.
Impact: Além da ausência de nível/roteamento, expõe dado pessoal (e-mail) em log não controlado.
Recommendation: Substituir por `logger.info(...)`, evitando logar PII em texto claro ou mascarando o dado.

### [LOW] print() como mecanismo de logging
File: controllers.py:179
Description: `print("Login bem-sucedido: " + email)` registra sucesso de autenticação em `login`.
Impact: Mesmo problema de ausência de nível/roteamento; expõe e-mail em stdout.
Recommendation: Substituir por `logger.info(...)`.

### [LOW] print() como mecanismo de logging
File: controllers.py:182
Description: `print("Login falhou: " + email)` registra tentativa de login inválida em `login`.
Impact: Mesmo problema de ausência de nível/roteamento; expõe e-mail em stdout mesmo em falha de autenticação.
Recommendation: Substituir por `logger.warning(...)`.

### [LOW] print() como mecanismo de logging
File: controllers.py:208-210
Description: Três chamadas `print(...)` contíguas em `criar_pedido` simulando envio de notificações ("ENVIANDO EMAIL", "ENVIANDO SMS", "ENVIANDO PUSH") após a criação do pedido.
Impact: Simulação de efeitos colaterais via stdout, sem nível, timestamp ou possibilidade de desabilitar em produção.
Recommendation: Substituir por `logger.info(...)` (ou, se for lógica de notificação real futura, extrair para um service dedicado).

### [LOW] print() como mecanismo de logging
File: controllers.py:219
Description: `print("ERRO CRITICO ao criar pedido: " + str(e))` no bloco `except` de `criar_pedido`.
Impact: Erro crítico de negócio não é rastreável de forma estruturada em produção.
Recommendation: Substituir por `logger.error(...)`, idealmente com `exc_info=True`.

### [LOW] print() como mecanismo de logging
File: controllers.py:248
Description: `print("NOTIFICAÇÃO: Pedido " + ... + " foi aprovado! Preparar envio.")` em `atualizar_status_pedido`, ramo `status == "aprovado"`.
Impact: Mesmo problema de ausência de nível/roteamento/timestamp.
Recommendation: Substituir por `logger.info(...)`.

### [LOW] print() como mecanismo de logging
File: controllers.py:250
Description: `print("NOTIFICAÇÃO: Pedido " + ... + " cancelado. Devolver estoque.")` em `atualizar_status_pedido`, ramo `status == "cancelado"`.
Impact: Mesmo problema de ausência de nível/roteamento/timestamp.
Recommendation: Substituir por `logger.info(...)`.

### [LOW] print() como mecanismo de logging
File: app.py:56
Description: `print("!!! BANCO DE DADOS RESETADO !!!")` dentro do handler HTTP `reset_database` reporta um evento de runtime (reset de dados) via stdout.
Impact: Ação destrutiva relevante fica registrada apenas em stdout, sem nível, timestamp ou possibilidade de auditoria/roteamento.
Recommendation: Substituir por `logger.warning(...)` ou `logger.critical(...)`, dado o caráter destrutivo da ação.

================================
Total: 13 findings
================================

## Observações fora do catálogo atual (não pontuadas)

O catálogo formal desta skill cobre hoje apenas o anti-pattern "print() como logging"
(severidade LOW). Durante a leitura do código foram notados outros problemas reais que
**não têm entrada formal no catálogo** e por isso não entram no Summary/Total acima. Ficam
registrados aqui apenas como observação, sem severidade atribuída:

- **SQL Injection por concatenação de string**: praticamente todas as queries em
  `models.py` são montadas concatenando entrada do usuário diretamente na string SQL
  (ex: `models.py:28,48-49,58-60,68,92,110,127-128,140,149-150,155,158-160,163-165,174,
  188,192,220,224,280,291-297`), incluindo o endpoint `/admin/query` (`app.py:59-78`), que
  executa qualquer SQL arbitrário recebido no corpo da requisição.
- **Credenciais/segredos hardcoded**: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`
  (`app.py:7`), e o mesmo valor é retornado na resposta pública de `/health`
  (`controllers.py:289`); senhas de usuários são armazenadas e comparadas em texto plano em
  `models.py` (`login_usuario`, `criar_usuario`).
- **Endpoints administrativos sem autenticação/autorização**: `/admin/reset-db` (`app.py:47-57`)
  e `/admin/query` (`app.py:59-78`) não exigem nenhuma credencial e ficam expostos como
  qualquer outra rota pública.
- **Configuração insegura em produção**: `app.config["DEBUG"] = True` e `app.run(..., debug=True)`
  (`app.py:8,88`), combinado com `"ambiente": "producao"` retornado por `/health`
  (`controllers.py:286`).
- **N+1 queries**: `models.get_pedidos_usuario` e `models.get_todos_pedidos`
  (`models.py:171-233`) abrem um novo cursor e executam uma query por item de pedido dentro
  de um laço aninhado por pedido.
- **Regra de negócio presa nos controllers**: validações de domínio (limites de preço,
  tamanho de nome, categorias válidas, etc.) ficam em `controllers.py` em vez de uma camada
  de serviço/domínio dedicada.

Essas observações são apresentadas apenas para contexto; conforme instruído, não alteram o
Summary/Total oficial deste relatório, que reflete estritamente o catálogo formal vigente.
