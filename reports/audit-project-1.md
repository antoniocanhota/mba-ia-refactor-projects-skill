================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project — API de E-commerce (Loja)
Stack:   Python 3 / Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Dados sensíveis serializados direto na resposta
File: models.py:83 (propagado por controllers.py:130-132)
Description: `get_todos_usuarios()` faz `SELECT *` e devolve o campo `"senha": row["senha"]` no dict; `listar_usuarios()` repassa esse dict inteiro em `jsonify` sem filtrar campos. `GET /usuarios` retorna a senha (em texto puro, sem hash) de todos os usuários.
Impact: Vaza credenciais de todos os usuários a qualquer consumidor da API — inclusive sem autenticação no endpoint. Agravante: a senha é armazenada e comparada em texto puro (ver `models.py:110`), então o vazamento expõe a senha real, não um hash.
Recommendation: Introduzir DTO/serializer que exclua `senha` da resposta pública (ver playbook → "DTO/serializer para a resposta").

### [CRITICAL] Dados sensíveis serializados direto na resposta
File: models.py:99 (propagado por controllers.py:138-140)
Description: `get_usuario_por_id()` também devolve `"senha": row["senha"]`; `buscar_usuario()` repassa direto ao cliente. `GET /usuarios/<id>` vaza a senha do usuário buscado.
Impact: Mesmo vazamento de credencial do finding anterior, desta vez no endpoint de detalhe individual.
Recommendation: Mesmo DTO/serializer do finding anterior, reaproveitado nos dois endpoints.

### [CRITICAL] Dados sensíveis serializados direto na resposta
File: controllers.py:289
Description: `health_check()` devolve no corpo da resposta `"secret_key": "minha-chave-super-secreta-123"` (hardcoded em `app.py:7`) e `"debug": True`. `GET /health` é um endpoint público sem autenticação.
Impact: Expõe a `SECRET_KEY` do Flask (usada para assinar sessions/cookies) a qualquer cliente — permite forjar sessões/tokens assinados pela aplicação. Também confirma `debug=True` publicamente, o que ajuda um atacante a mapear o ambiente.
Recommendation: Remover `secret_key` e `debug` do payload de `/health`; expor só o necessário para verificação de liveness (status, conectividade com o banco).

### [CRITICAL] God Class / God Module
File: app.py:47-57
Description: A rota `/admin/reset-db` é definida direto em `app.py` e, na mesma função, abre a conexão (`get_db()`), monta e executa 4 `DELETE` e faz o commit — roteamento, controller e acesso a dados no mesmo lugar, sem passar por `controllers.py`/`models.py`.
Impact: Quebra a fronteira de camadas que o resto do projeto já estabelece; essa rota é intestável isoladamente, e destrói dados de produção (`DELETE FROM` em 4 tabelas) sem nenhuma autenticação/autorização.
Recommendation: Extrair para um controller + model dedicados (ex: `controllers.reset_database()` / `models.reset_database()`) e proteger com autenticação/autorização de admin — nunca remover a rota (ver playbook → "God Class → separação em camadas").

### [CRITICAL] God Class / God Module
File: app.py:59-78
Description: A rota `/admin/query` também está embutida em `app.py`: lê `sql` do corpo da requisição e executa via `cursor.execute(query)` sem nenhuma sanitização, autenticação ou allowlist — roteamento, controller e acesso a dados concentrados na mesma função, fora da estrutura de camadas do projeto.
Impact: Além de violar a separação de camadas (mesmo problema do finding anterior), permite execução de **SQL arbitrário** definido pelo cliente sem autenticação — o achado mais grave do projeto.
Recommendation: Extrair para camadas de controller/service dedicadas **e** proteger o endpoint (autenticação forte + allowlist de operações ou remoção do acesso irrestrito a SQL livre) — nunca remover a rota; se não houver forma segura de manter SQL livre, restrinja fortemente o que pode ser executado (ver playbook → "God Class → separação em camadas").

### [HIGH] Regra de negócio presa no controller
File: controllers.py:188-220
Description: `criar_pedido()` orquestra a criação do pedido via `models.criar_pedido` e, na sequência, "envia" notificações (`print("ENVIANDO EMAIL...")`, SMS, PUSH) diretamente no controller — decisão de quais canais notificar e quando é regra de negócio embutida no handler HTTP.
Impact: Orquestração de side-effects de negócio não é reutilizável nem testável fora do ciclo HTTP; qualquer canal de notificação real (e-mail/SMS de verdade) exigiria reescrever o controller em vez de estender um serviço.
Recommendation: Extrair para uma camada de serviço/use-case (`services.criar_pedido()`) que orquestra persistência + notificação; controller só valida shape e delega (ver playbook → "extrair regra para camada de serviço").

### [HIGH] Regra de negócio presa no controller
File: controllers.py:237-255
Description: `atualizar_status_pedido()` decide, com `if novo_status == "aprovado"` / `"cancelado"`, qual notificação disparar — regra de negócio condicional ao estado do pedido vive no controller, sem serviço intermediário.
Impact: A regra "o que fazer quando o pedido muda de status" fica acoplada ao transporte HTTP; extensões futuras (ex: reverter estoque no cancelamento, que hoje só é logado) tendem a crescer direto no controller.
Recommendation: Mover a decisão para um serviço de pedidos que reage à mudança de status (ver playbook → "extrair regra para camada de serviço").

### [HIGH] Ausência de injeção de dependência / estado global mutável
File: database.py:4-11
Description: `db_connection` é uma variável global de módulo (`global db_connection`) que guarda um singleton de conexão SQLite, lida/escrita por `get_db()` e referenciada diretamente (via import) por `controllers.py`/`models.py`/`app.py`.
Impact: Acoplamento forte à implementação concreta de conexão — impossível substituir por um dublê em teste sem manipular estado de módulo; conexão compartilhada mutável entre requisições concorrentes (SQLite com `check_same_thread=False`) é fonte de condição de corrida.
Recommendation: Injetar a conexão/factory via parâmetro (composition root em `app.py` que constrói e passa a dependência) em vez de acessar o global (ver playbook → "injeção de dependência / composition root").

### [MEDIUM] Duplicação de código / lógica reimplementada
File: controllers.py:24-62 (criar_produto) e controllers.py:64-96 (atualizar_produto)
Description: Os blocos de validação (`dados` obrigatório, `nome`/`preco`/`estoque` obrigatórios, `preco`/`estoque` não-negativos) são copiados quase palavra por palavra entre as duas funções.
Impact: Uma correção de regra (ex: novo limite de preço) precisa ser replicada nos dois lugares; já há divergência sutil — `atualizar_produto` não repete as checagens de tamanho do nome (linhas 47-50 de `criar_produto`) nem a validação de `categoria` (linha 52-54), que `criar_produto` tem.
Recommendation: Extrair um validador único (`validar_produto(dados, obrigatorio_todos=True)`) reusado pelas duas rotas (ver playbook → "extrair/reusar lógica duplicada").

### [MEDIUM] Duplicação de código / lógica reimplementada
File: models.py:171-201 (get_pedidos_usuario) e models.py:203-233 (get_todos_pedidos)
Description: As duas funções montam pedido + itens da mesma forma (mesmos 3 cursores aninhados, mesma estrutura de dict), diferindo apenas na cláusula `WHERE usuario_id = ...` de uma delas.
Impact: Qualquer ajuste no formato de resposta de "pedido com itens" precisa ser feito em dois lugares; o código já mostra sinais de cópia mecânica (mesmos nomes `cursor2`/`cursor3` repetidos).
Recommendation: Extrair um helper `_montar_pedidos(rows)` reusado por ambas (ver playbook → "extrair/reusar lógica duplicada").

### [MEDIUM] Duplicação de código / lógica reimplementada
File: models.py:12-21, models.py:31-40, models.py:304-313
Description: A construção do dict de produto (`id`, `nome`, `descricao`, `preco`, `estoque`, `categoria`, `ativo`, `criado_em`) a partir de `row` é copiada idêntica em `get_todos_produtos`, `get_produto_por_id` e `buscar_produtos`.
Impact: Alterar o shape de "produto" (ex: adicionar campo) exige lembrar de editar três funções; divergência silenciosa é fácil de introduzir.
Recommendation: Extrair `_produto_to_dict(row)` reusado pelas três funções (ver playbook → "extrair/reusar lógica duplicada").

### [MEDIUM] Tratamento de erro espalhado / não centralizado
File: controllers.py (16 handlers, ex: linhas 6-12, 15-22, 25-62, 65-96, 98-109, 112-126, 137-144, 147-165, 168-186, 189-220, 238-255, 265-292) e app.py:68-78
Description: Praticamente todo handler repete `try/except Exception as e: return jsonify({"erro": str(e)}), 500` — captura genérica local, sem nenhum `@app.errorhandler` registrado em `app.py`. `str(e)` (detalhe interno da exceção) vaza no corpo da resposta em todos os casos.
Impact: O mesmo boilerplate de erro está duplicado em ~16 lugares; qualquer padronização de formato de erro (código, campo, i18n) exige editar todos; e o vazamento de `str(e)` ajuda um atacante a mapear estrutura interna/mensagens de exceção do sistema.
Recommendation: Registrar um `@app.errorhandler(Exception)` (e handlers específicos para 400/404) central em `app.py`, remover os `try/except` genéricos dos controllers e deixar exceções subirem (ver playbook → "error handler centralizado / middleware").

### [LOW] print() como mecanismo de logging
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Chamadas `print(...)` registram eventos de runtime (criação/deleção de entidades, login, notificações "enviadas", erros) dentro dos handlers — inclusive em blocos `except` para reportar falha (ex: linha 11, 61, 219).
Impact: Sem nível, timestamp ou destino configurável — impossível silenciar/filtrar em produção; mistura diagnóstico com stdout da aplicação.
Recommendation: Substituir por `logging` configurado (nível, formato, destino) — ver playbook → "print() → logging".

### [LOW] print() como mecanismo de logging
File: app.py:56
Description: `print("!!! BANCO DE DADOS RESETADO !!!")` registra, via `print`, um evento de runtime crítico (reset destrutivo do banco) dentro da rota `/admin/reset-db`.
Impact: Mesmo impacto do finding anterior — evento sensível (reset de dados) sem log estruturado/nível/timestamp.
Recommendation: Substituir por `logging.warning(...)` (ver playbook → "print() → logging").

### [LOW] Nomenclatura fraca de variáveis
File: models.py:187, 191 (get_pedidos_usuario) e models.py:219, 223 (get_todos_pedidos)
Description: Cursores adicionais são nomeados por sufixo numérico (`cursor2`, `cursor3`) em vez de um nome que revele o papel (ex: `cursor_itens`, `cursor_produto`).
Impact: Esconde que são cursores de queries distintas (itens do pedido vs. nome do produto), facilitando trocas acidentais entre eles ao editar o código.
Recommendation: Renomear para nomes intencionais (ver playbook → "renomear para nomes intencionais").

================================
Total: 15 findings
================================
