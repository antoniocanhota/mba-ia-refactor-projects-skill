# Criação de Skills — Refatoração Arquitetural Automatizada

**A) Seção "Análise Manual":**

Foram encontrados diversos problemas nos projetos desse desafio. Aqui estão listados os que considerei mais relevantes por projeto:

***code-smells-project***

| Severidade | Problema | Justificativa |
|---|---|---|
| CRITICAL | `app.py:47-57` — endpoint `/admin/reset-db` sem qualquer autenticação, apaga todas as tabelas | Qualquer requisição não autenticada consegue destruir o banco de dados inteiro em produção |
| CRITICAL | `controllers.py:288-289` — `health_check` retorna `secret_key` e `debug` no corpo da resposta pública | Vaza o segredo usado para assinar sessões/tokens, permitindo forjar credenciais válidas |
| CRITICAL | `controllers.py:130-134, 138-144` — `listar_usuarios`/`buscar_usuario` devolvem o campo `senha` na resposta JSON | Expõe a senha (ou hash) de todos os usuários a qualquer cliente que consulte a API |
| HIGH | `controllers.py:5-263` — lógica de negócio, validação e orquestração dentro dos controllers, sem camada de serviço/use case (violação MVC/SRP) | Mistura de responsabilidades no controller torna o código difícil de testar isoladamente e de reaproveitar em outros pontos de entrada |
| HIGH | `models.py:256-262` — regra de negócio (faixas de desconto do relatório) embutida na camada de acesso a dados | Acopla regra de negócio à camada de persistência, dificultando alterar a regra sem mexer em código de acesso a dados |
| MEDIUM | `controllers.py:24-58, 64-96` — duplicação quase idêntica do bloco de validação entre `criar_produto` e `atualizar_produto` | Regras de negócio replicadas em dois lugares tendem a divergir com o tempo, gerando inconsistência de validação |
| MEDIUM | `models.py:194-200, 226-231` — duplicação do bloco de montagem de "itens" entre `get_pedidos_usuario` e `get_todos_pedidos` | Mesma lógica de serialização mantida em dois pontos aumenta o custo e o risco de bugs a cada mudança futura |
| MEDIUM | `database.py:1-86` — `get_db()` mistura conexão, criação de schema e seed de dados em uma única função | Múltiplas responsabilidades na mesma função dificultam testes isolados e reuso |
| LOW | `controllers.py:5-263` — uso de `print()` para logging em vez do módulo `logging` | Impede configuração de níveis de log, rotação e integração com ferramentas de observabilidade em produção |
| LOW | `models.py:187, 191, 219, 223` — nomenclatura fraca de variáveis (`cursor2`, `cursor3`) | Nomes não descritivos dificultam a leitura e manutenção do código |
| LOW | `controllers.py:52` — lista de categorias válidas hardcoded dentro da função | Valores de negócio espalhados no código, em vez de centralizados, dificultam manutenção e geram divergência |

***ecommerce-api-legacy***

| Severidade | Problema | Justificativa |
|---|---|---|
| CRITICAL | `src/AppManager.js:66-75` — fluxo de checkout não autentica o usuário: se o e-mail já existe, o pedido é processado sem validar a senha informada | Permite comprar em nome de qualquer usuário cadastrado apenas sabendo o e-mail dele |
| CRITICAL | `src/AppManager.js:80-129` — endpoint `/api/admin/financial-report` sem qualquer autenticação/autorização | Expõe faturamento e dados de alunos a qualquer visitante, sem controle de acesso |
| CRITICAL | `src/AppManager.js:131-137` — endpoint `DELETE /api/users/:id` sem autenticação e sem integridade referencial | Qualquer um pode apagar usuários, e o próprio código admite que matrículas e pagamentos ficam órfãos |
| CRITICAL | `src/AppManager.js:45` — `console.log` expõe o número completo do cartão (`cc`) e a chave secreta do gateway de pagamento | Dados de cartão e credenciais de pagamento ficam gravados em logs de aplicação, violando PCI-DSS e facilitando vazamento |
| HIGH | `src/AppManager.js:28-78` — rota `/api/checkout` mistura roteamento, validação, regra de pagamento e acesso a dados em callbacks aninhados (pyramid of doom), sem camada de serviço | Fluxo mais crítico da aplicação (pagamento) fica difícil de ler, testar e evoluir sem quebrar algo, já que tudo está entrelaçado em callbacks |
| MEDIUM | `src/AppManager.js:10-23` — `initDb()` mistura definição de schema com inserção de dados de seed na mesma função | Responsabilidades misturadas dificultam reutilizar o schema sem repetir o seed (e vice-versa) |
| MEDIUM | `src/AppManager.js:29-33, 35` — ausência de validação de tipo/formato dos dados de entrada (`c_id` não validado como número, `card` sem validação de formato) | Entradas não validadas podem gerar erros inesperados ou serem exploradas para contornar regras de negócio |
| LOW | `src/AppManager.js:29-33` — nomenclatura pouco descritiva de variáveis (`u`, `e`, `p`, `cid`, `cc`) | Nomes genéricos tornam o fluxo de pagamento/checkout mais difícil de auditar e manter |
| LOW | `src/utils.js:10, 25` — `totalRevenue` é exportado mas nunca é efetivamente atualizado/utilizado | Código morto/enganoso passa a impressão de uma métrica funcional que na prática não reflete a realidade |

***task-manager-api***

| Severidade | Problema | Justificativa |
|---|---|---|
| CRITICAL | `models/user.py:16-25` — `to_dict()` inclui o campo `password` (hash) na resposta pública do usuário | Vaza o hash da senha de todo usuário em qualquer resposta que serialize o model, facilitando ataques offline de quebra de hash |
| CRITICAL | `routes/user_routes.py:33, 85-86` — `get_user` e `create_user` devolvem `user.to_dict()` completo, expondo o hash da senha na API | Reforça o vazamento do model diretamente nos endpoints mais usados da API |
| CRITICAL | `routes/user_routes.py:119-122` — `update_user` permite que qualquer requisição altere o `role` para `admin` sem autenticação/autorização | Escalonamento de privilégio trivial: qualquer cliente pode se tornar administrador do sistema |
| CRITICAL | `routes/user_routes.py:210` — login retorna um "token" fake (`'fake-jwt-token-' + id`), previsível e sem assinatura | Não há autenticação real; um atacante pode forjar tokens válidos apenas conhecendo o ID do usuário |
| HIGH | `routes/task_routes.py, routes/user_routes.py, routes/report_routes.py` (toda a extensão) — validação, regra de negócio e serialização ficam nas rotas; a camada `services/` existe mas não é usada pelos controllers (violação de MVC/SRP) | O projeto já tem uma camada de serviço pronta para isolar regra de negócio, mas ela é ignorada — todo o código fica acoplado ao roteamento, dificultando testes e reuso |
| MEDIUM | `models/task.py:38-48` — `validate_status()` e `validate_priority()` definidos no model mas nunca usados | As rotas reimplementam a mesma validação inline, criando duas fontes de verdade que podem divergir |
| MEDIUM | `routes/task_routes.py:261, 264` — `int(priority)` / `int(user_id)` em `search_tasks` sem tratamento de erro | Uma entrada inválida gera `ValueError` não tratado, retornando erro 500 em vez de uma resposta de validação adequada |
| LOW | `routes/task_routes.py`, `routes/user_routes.py` — uso de `print()` para logging de eventos de negócio em vez do módulo `logging` | Impede configuração de níveis de log e integração com ferramentas de observabilidade em produção |
| LOW | `utils/helpers.py:1-7` — imports não utilizados no módulo (`os`, `sys`, `json`, `math`) | Poluição do código com dependências mortas, sem valor funcional |


**B) Seção "Construção da Skill":**

> **Estado atual:** a skill foi construída de forma incremental. Esta versão trata
> **9 anti-patterns cobrindo as 4 severidades** — 2 CRITICAL, 2 HIGH, 3 MEDIUM e
> 2 LOW — percorrendo as 3 fases ponta-a-ponta, e continua projetada para crescer
> (novos anti-patterns entram nos arquivos de referência sem alterar o fluxo).
> Ferramenta escolhida: **Claude Code**.

**Decisões de design — SKILL.md e arquivos de referência**

- `SKILL.md` curto (~145 linhas, bem abaixo do teto de ~300/500), atuando só como
  **orquestrador** das 3 fases sequenciais (Análise → Auditoria → Refatoração). O
  conhecimento de domínio fica em `references/`, lido **sob demanda** (progressive
  disclosure), reduzindo tokens e ruído de contexto.
- 5 arquivos de referência, um por área de conhecimento exigida pela spec:
  `project-analysis.md` (heurísticas de detecção da Fase 1), `anti-patterns.md`
  (catálogo com sinais + severidade), `report-template.md` (formato do relatório da
  Fase 2), `architecture-guidelines.md` (regras do padrão MVC alvo) e
  `refactoring-playbook.md` (transformações antes/depois da Fase 3).
- `description` do front matter escrita como mecanismo de descoberta (o quê + quando
  usar + como ajuda).
- Regras operacionais no corpo: confirmação humana obrigatória entre Fase 2 e Fase 3,
  sinais de detecção específicos e acionáveis, validação não-destrutiva na Fase 3.
- Incremento posterior: a Fase 2 passou a **salvar o relatório de auditoria em `.md`**,
  perguntando path e nome do arquivo ao usuário, antes da confirmação.

**Anti-patterns no catálogo e por quê**

O catálogo cobre **9 anti-patterns nas 4 severidades**, priorizando os que são
recorrentes nos 3 projetos e mais relevantes para **MVC/SOLID**, e alinhados de forma
estrita à escala de severidade da própria skill. Cada entrada de `anti-patterns.md` tem
uma transformação antes/depois correspondente em `refactoring-playbook.md` (relação 1:1,
casada pelo nome).

| Severidade | Anti-pattern | Por quê entrou |
|---|---|---|
| CRITICAL | God Class / God Module | Violação total de SRP/MVC — casa literalmente com a definição de CRITICAL ("God Class contendo banco, lógicas e roteamento no mesmo arquivo") |
| CRITICAL | Dados sensíveis serializados direto na resposta | Expõe credenciais/hashes (senha/`password`) por falta de fronteira Model↔View (DTO) — "expõe dados sensíveis" |
| HIGH | Regra de negócio presa no controller | Violação de MVC/SRP mais recorrente dos 3 projetos; a camada `services/` às vezes existe mas é ignorada |
| HIGH | Ausência de injeção de dependência / estado global mutável | Viola DIP: conexão no construtor/global e estado compartilhado entre requisições, impedindo teste isolado |
| MEDIUM | Duplicação de código / lógica reimplementada | Viola DRY: validação copiada entre create/update e métodos de model já existentes reimplementados inline |
| MEDIUM | Uso de API deprecated | Requisito obrigatório do enunciado ("detecção de APIs deprecated + recomendar o equivalente moderno"); usa a versão detectada na Fase 1 para cruzar cada símbolo obsoleto contra seu substituto moderno |
| MEDIUM | Tratamento de erro espalhado / não centralizado | Realiza o item "Error handling centralizado" do checklist da Fase 3; `except` genérico repetido vazando `str(e)` encaixa em "uso inadequado de middlewares" (MEDIUM) e transforma para um error-handler global |
| LOW | `print()` como mecanismo de logging | Primeiro caso construído: detecção inequívoca (`grep 'print('`) e transformação segura (troca por logging com níveis); validou o pipeline inteiro com baixo risco |
| LOW | Nomenclatura fraca de variáveis | Casa literalmente com a definição de LOW ("nomenclatura de variáveis ruins"); recorrente em 2 projetos (`cursor2`/`cursor3`, `u`/`e`/`p`/`cc`); 100% agnóstico e de transformação segura (renomeação pura) |

- **Detecção de APIs deprecated (requisito obrigatório) como MEDIUM:** a "detecção de APIs
  deprecated" exigida pelo enunciado entrou como **MEDIUM**. O enunciado não fixa uma
  severidade para ela, então usamos a definição da própria escala: uso de API obsoleta é um
  problema de **padronização/manutenção** (a API funciona hoje, mas quebra em upgrade futuro
  e diverge do padrão atual), que é exatamente o balde MEDIUM. Não é HIGH (HIGH é reservado a
  violações de MVC/SOLID, e API obsoleta é ortogonal à arquitetura) nem LOW (tem consequência
  funcional, não é só cosmético). Consideramos ainda um bucket `OTHER`/categoria separada,
  mas descartamos: quebraria o `## Summary` de 4 níveis do relatório e a ordenação por
  severidade, além de esconder a urgência — o **nome** do anti-pattern ("Uso de API
  deprecated") já cumpre o papel de categoria, com a severidade no colchete.
- **Escopo do catálogo — o que escolhi implementar (arquitetura/SOLID), e o que deixei de
  fora:** o enunciado fixa apenas um **piso** para o catálogo — "≥8 anti-patterns com
  severidade distribuída" + "detecção de APIs deprecated" — e dá **liberdade sobre quais**
  anti-patterns entram além disso. A escolha foi manter o catálogo alinhado à lente que a
  própria escala de severidade do enunciado usa (*"baseada em problemas de MVC e SOLID"*):
  anti-patterns **estruturais** (God Class, regra no controller, ausência de DI/estado
  global, duplicação, erro não centralizado etc.). A **Análise Manual (seção A)** — que é um
  inventário dos problemas *existentes* nos projetos, independente do que a skill cobre —
  levanta também vulnerabilidades de segurança *puras* (segredos/credenciais hardcoded, SQL
  Injection, autenticação/autorização ausente, hash fraco). Essas **não entraram no catálogo
  por decisão de escopo**: no enunciado elas aparecem como exemplos que *ilustram o nível
  CRITICAL*, não como detecções exigidas. Consequência assumida: o catálogo só sinaliza essas
  vulnerabilidades **quando coincidem com um sinal arquitetural** (`SECRET_KEY` ecoado em
  `/health` → "dados sensíveis na resposta"; endpoint de SQL arbitrário → "God Class"), e a
  Fase 3 acabou blindando vários deles onde houve essa sobreposição (autenticação nas rotas
  admin do `code-smells-project`; MD5 → `pbkdf2:sha256` no `task-manager-api`). O que a skill
  **não** faz por escolha é atuar como scanner de segurança genérico: manter o catálogo
  estritamente arquitetural preserva a consistência da classificação por severidade (ver
  também o desafio da "escala de severidade genérica" mais abaixo).

**Como se garante que a skill é agnóstica de tecnologia**

- As heurísticas e o catálogo descrevem **sinais**, não uma stack fixa: detecção de
  linguagem por extensão + manifesto (Python, Node, Ruby, Go, Java, PHP...) e de
  framework por dependências/imports.
- Cada anti-pattern/transformação lista **equivalentes por stack** (ex: `print` /
  `console.log` / `System.out.println` / `fmt.Println` / `puts`).
- As guidelines de arquitetura instruem a **adaptar a nomenclatura de camadas** ao
  ecossistema detectado.

**Desafios encontrados e como resolvi**

- **`skill-creator` da Anthropic: custo alto e resultado difícil de auditar:** a primeira
  tentativa foi usar a skill oficial `skill-creator` para gerar a `refactor-arch` de uma vez.
  Esbarrei em dois problemas: **custo elevado** — a execução esgotou minha quota em cerca de
  1 hora — e um **resultado difícil de analisar**, gerado em bloco, no qual eu não conseguia
  entender nem validar cada decisão de forma incremental. Foi quando decidi **construir a
  skill manualmente e de forma incremental**: um anti-pattern por vez, testando o pipeline
  ponta-a-ponta a cada adição, o que deu controle sobre custo e sobre a qualidade de cada
  parte (ver o "Estado atual" no início desta seção).
- **Validar sem sujar o fixture:** a Fase 3 foi testada de verdade (boot + endpoints)
  e depois **revertida via git**, preservando o `code-smells-project` no estado
  original de entrada do desafio.
- **Fase 3 removeu um endpoint em vez de protegê-lo:** ao rodar a Fase 3 em
  `code-smells-project`, o endpoint `/admin/query` (executa SQL arbitrário vindo do
  cliente, achado CRITICAL) foi **removido** por ter sido interpretado como "sem fix
  seguro possível". O usuário corrigiu: o checklist de validação já exige "Endpoints
  originais respondem corretamente" — a correção certa é **proteger** (autenticação),
  nunca **apagar** funcionalidade. `SKILL.md` ganhou uma regra operacional explícita
  proibindo remoção de endpoints/funcionalidade na Fase 3, mesmo para achados CRITICAL
  sem correção óbvia; o endpoint foi restaurado atrás de autenticação por token.

**C) Seção "Resultados":**

> A skill foi executada ponta-a-ponta (Fase 1 → Fase 2 → Fase 3) nos **3 projetos**,
> auditando cada um contra as **9 categorias do catálogo (4 severidades)** — ver
> detalhes abaixo.

Resumo consolidado dos relatórios de auditoria (Fase 2, `reports/audit-project-{1,2,3}.md`):

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project | 5 | 3 | 4 | 3 | 15 |
| ecommerce-api-legacy | 1 | 4 | 3 | 3 | 11 |
| task-manager-api | 1 | 4 | 7 | 2 | 14 |

`code-smells-project` foi auditado contra as 9 categorias do catálogo — os 15
findings cobrem God Class (rotas administrativas embutidas em `app.py`, fora de
controllers/models), dados sensíveis serializados na resposta (`senha` vazada em
`/usuarios` e `secret_key`/`debug` vazados no health check), regra de negócio no
controller (notificações de pedido), ausência de injeção de dependência/estado global
mutável, duplicação de código, tratamento de erro espalhado/não centralizado, `print()`
como logging e nomenclatura fraca de variáveis — a única categoria do catálogo sem
ocorrência nesta base foi "uso de API deprecated". `ecommerce-api-legacy` também foi
auditado contra as 9 categorias — os 11 findings cobrem God Class (`AppManager.js`
concentrando conexão, schema, rotas, controller e SQL), regra de negócio presa no
controller (checkout e relatório financeiro), ausência de injeção de dependência
(conexão instanciada no construtor) e estado global mutável (`globalCache`/
`totalRevenue`), código morto correlato a lógica reimplementada, tratamento de erro
espalhado/não centralizado (incluindo erros de callback silenciosamente ignorados no
relatório financeiro), `print()` como logging (um deles vazando dado de cartão e a
chave do gateway de pagamento) e nomenclatura fraca de variáveis — as categorias sem
ocorrência nesta base foram "dados sensíveis serializados direto na resposta" (nenhum
endpoint devolve a coluna `pass`) e "uso de API deprecated" (dependências e APIs usadas
já são as atuais). `task-manager-api` foi auditado contra as 9 categorias — os 14
findings cobrem dados sensíveis serializados na resposta (hash de senha vazado em
`User.to_dict()` e devolvido por 4 endpoints, incluindo o login), regra de negócio
presa no controller (validação e agregação de relatório dentro das rotas, com a
camada `services/` órfã — nunca instanciada por nenhuma rota), ausência de injeção de
dependência (credenciais SMTP hardcoded no construtor de `NotificationService`),
duplicação de código (cálculo de "atrasado" reimplementado 5 vezes ignorando
`Task.is_overdue()`; validação de status/prioridade e de e-mail reimplementadas
ignorando helpers já existentes e nunca chamados), uso de API deprecated
(`datetime.utcnow()` e `Query.get(id)`, API legacy do SQLAlchemy 2.x), tratamento de
erro espalhado (13 blocos `try/except` genéricos, sem `@app.errorhandler`), `print()`
como logging e nomenclatura fraca (`p1`..`p5`, variáveis de uma letra para entidades
de domínio) — a única categoria do catálogo sem ocorrência nesta base foi "God Class",
já que o projeto chegava com `models/`/`routes/`/`services/`/`utils/` separados em
arquivos.

***code-smells-project*** (Python/Flask) — *processado pela skill*

Stack detectada na Fase 1: Python + Flask 3.1.1 + flask-cors, SQLite (tabelas
`produtos`, `usuarios`, `pedidos`, `itens_pedido`), domínio E-commerce, 4 arquivos
(~780 linhas), arquitetura com módulos separados por responsabilidade
(`app.py`/`controllers.py`/`models.py`/`database.py`), mas sem camada de serviço nem
de config — **parcialmente organizada**.

Antes / depois da estrutura: o projeto já chegava **parcialmente organizado**
(`app.py` = rotas, `controllers.py` = handlers, `models.py` = acesso a dados,
`database.py` = conexão/schema) — pela regra de "adaptação ao contexto" das
guidelines, isso pede **correções pontuais**, não uma árvore nova de diretórios.
Único arquivo novo: `services.py` (extrai a orquestração de notificação de pedido
que estava presa no controller). Mudanças aplicadas dentro dos arquivos existentes:
`senha` removida das queries/dicts de `get_todos_usuarios`/`get_usuario_por_id`
(nunca mais sai em `/usuarios`); `health_check` não expõe mais `secret_key`/`debug`;
`SECRET_KEY` passa a vir de `os.environ` (fallback só de dev); as rotas
`/admin/reset-db` e `/admin/query` saíram de `app.py` para `controllers.py`/
`models.py` e passaram a exigir o header `X-Admin-Key` (sem a env `ADMIN_API_KEY`
configurada, respondem 503 em vez de ficarem abertas) — nenhum endpoint foi
removido, ver seção B; `database.py` trocou o singleton global `db_connection` por
conexão por requisição via `flask.g` (injeção de dependência, sem estado mutável
compartilhado entre requisições); validação de produto e montagem de dict/pedido
deduplicadas em helpers reaproveitados; todas as queries em `models.py` passaram a
ser parametrizadas (eliminando a concatenação de string em SQL); os ~16
`try/except` genéricos dos controllers foram removidos e centralizados em
`@app.errorhandler(Exception)`/`@app.errorhandler(404)` em `app.py`; todo `print()`
de runtime virou `logging`; `cursor2`/`cursor3` renomeados para `cursor_itens`/
`cursor_produto`.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1 + flask-cors)
- [x] Domínio da aplicação descrito corretamente (e-commerce: produtos/usuários/pedidos)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos, ~780 linhas)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (15)
- [x] Detecção de APIs deprecated incluída *(categoria verificada; nenhuma ocorrência encontrada nesta base — documentado no relatório)*
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC *(mantida a separação já existente — `app.py`/`controllers.py`/`models.py`/`database.py` — mais `services.py` novo; sem árvore de diretórios nova, por já estar "parcialmente organizado")*
- [x] Configuração extraída para módulo de config *(sem hardcoded: `SECRET_KEY`/`ADMIN_API_KEY` lidos de `os.environ` no composition root `app.py`; não há um `config/` dedicado, por não ter sido exigido pelos achados)*
- [x] Models criados para abstrair dados (já existiam; queries agora parametrizadas + helpers de serialização deduplicados)
- [x] Views/Routes separadas (já existiam em `app.py`; rotas administrativas que antes tinham lógica embutida agora só registram e delegam)
- [x] Controllers concentram o fluxo da aplicação (`controllers.py`: validam, delegam a `models`/`services`, montam a resposta)
- [x] Error handling centralizado (`@app.errorhandler(Exception)` + `@app.errorhandler(404)` em `app.py`; `try/except` genéricos removidos dos controllers)
- [x] Entry point claro (`app.py` como composition root)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (todos os 19, incluindo `/admin/reset-db` e `/admin/query` — agora atrás de `X-Admin-Key`, nunca removidos)

Log da aplicação rodando após a refatoração (Fase 3):

```
2026-07-18 22:35:09 INFO __main__: SERVIDOR INICIADO
2026-07-18 22:35:09 INFO __main__: Rodando em http://localhost:5000
2026-07-19 01:36:12 INFO controllers: Listando 10 produtos
2026-07-19 01:36:12 INFO controllers: Login bem-sucedido: admin@loja.com
2026-07-19 01:36:12 INFO controllers: Login falhou: admin@loja.com
2026-07-19 01:36:12 INFO controllers: Produto criado com ID: 11
2026-07-19 01:36:12 INFO services: Enviando e-mail: pedido 1 criado para usuario 1
2026-07-19 01:36:12 INFO services: Enviando SMS: seu pedido foi recebido!
2026-07-19 01:36:12 INFO services: Enviando push: novo pedido recebido pelo sistema
2026-07-19 01:36:12 INFO services: Notificação: pedido 1 foi aprovado! Preparar envio.
```

***ecommerce-api-legacy*** (Node/Express) — *processado pela skill*

Stack detectada na Fase 1: Node.js + Express ^4.18.2, SQLite (via `sqlite3` ^5.1.6,
em memória), domínio LMS com checkout de cursos, 3 arquivos-fonte (~166 linhas), God
Class `AppManager.js` concentrando conexão, schema, seed, rotas, controller e SQL.

Antes / depois da estrutura: era um **monolito** (toda a lógica em `AppManager.js`),
então a Fase 3 aplicou a restruturação em camadas completa prevista nas guidelines,
proporcional ao achado CRITICAL de God Class. `AppManager.js` e `utils.js` foram
removidos e a lógica redistribuída em `src/config/` (config lida de env vars, com
fallback de dev — sem segredo hardcoded fixo), `src/db/` (conexão + `CREATE TABLE`/seed
promisificados, sem `db.serialize` implícito), `src/models/` (um módulo por entidade —
`userModel`, `courseModel`, `enrollmentModel`, `paymentModel`, `auditLogModel` — todas
as queries já eram parametrizadas e assim permaneceram), `src/services/`
(`checkoutService` e `financialReportService`, extraindo a regra de negócio antes presa
nos handlers), `src/controllers/` (só validam shape, chamam o serviço e montam a
resposta), `src/routes/` (mapeamento HTTP → controller) e `src/middlewares/errorHandler.js`
(error handler centralizado do Express, registrado por último em `app.js`, usando uma
classe `AppError` para preservar exatamente os mesmos status/mensagens da versão
legada). O `globalCache` mutável virou `src/cache/inMemoryCache.js`, instanciado uma
vez no composition root e injetado no serviço; `totalRevenue` (código morto, nunca
referenciado) foi removido. O `console.log` que vazava o número completo do cartão e a
chave do gateway de pagamento foi substituído por `src/utils/logger.js` (logger mínimo
com timestamp e níveis `info/warn/error`) com o número do cartão mascarado (só os
últimos 4 dígitos) e a chave do gateway removida do log. `src/app.js` virou o
composition root: monta conexão, schema, cache, rotas e error handler, e sobe o
servidor. Nenhum endpoint foi removido — inclusive `DELETE /api/users/:id` manteve o
comportamento legado de deixar matrículas/pagamentos órfãos, já que esse achado
específico não constava no relatório de auditoria.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express ^4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout de cursos)
- [x] Número de arquivos analisados condiz com a realidade (3 arquivos, ~166 linhas)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11)
- [x] Detecção de APIs deprecated incluída *(categoria verificada; nenhuma ocorrência encontrada nesta base — documentado no relatório)*
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (`config/`, `db/`, `models/`, `services/`, `controllers/`, `routes/`, `middlewares/`, `cache/`, `errors/`, `utils/`)
- [x] Configuração extraída para módulo de config (`src/config/config.js`, lida de env vars com fallback de dev)
- [x] Models criados para abstrair dados (`src/models/*Model.js`, queries parametrizadas)
- [x] Views/Routes separadas (`src/routes/index.js`)
- [x] Controllers concentram o fluxo da aplicação (`src/controllers/*Controller.js`: validam, delegam ao serviço, montam a resposta)
- [x] Error handling centralizado (`src/middlewares/errorHandler.js`, registrado por último em `app.js`, via classe `AppError`)
- [x] Entry point claro (`src/app.js` como composition root)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (checkout sucesso/recusado/curso inexistente/bad request, financial-report, delete user — nenhum removido)

Log da aplicação rodando após a refatoração (Fase 3):

```
2026-07-19T03:03:07.194Z INFO: Frankenstein LMS rodando na porta 3000...
2026-07-19T03:03:07.764Z INFO: Processando cartão ************4444
2026-07-19T03:03:07.766Z INFO: Cache atualizado para last_checkout_2
```

***task-manager-api*** (Python/Flask) — *processado pela skill*

Stack detectada na Fase 1: Python 3 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1,
Flask-CORS 4.0.0), SQLite via SQLAlchemy, domínio gestão de tarefas
(tasks/users/categories), 14 arquivos (~1059 linhas), já possui camada `services/`
(mas ignorada pelos controllers — ver seção A).

Antes / depois da estrutura: o projeto já chegava **parcialmente organizado**
(`models/`, `routes/`, `services/`, `utils/` em pastas separadas), então — pela regra
de "adaptação ao contexto" das guidelines — a Fase 3 aplicou **correções pontuais
dentro dos arquivos existentes**, sem criar uma árvore de diretórios nova. Mudanças
aplicadas: `User.to_dict()` deixou de incluir `password` (hash de senha migrado de
MD5 para `werkzeug.security` com `pbkdf2:sha256` — o algoritmo padrão do Werkzeug,
`scrypt`, não estava disponível no `hashlib` do ambiente de teste, um bug real só
descoberto ao validar o boot de verdade); `Task.is_overdue()` passou a ser
reaproveitado por todas as rotas no lugar do cálculo de "atrasado" reimplementado 5
vezes; `create_task`/`update_task` passaram a usar `utils.helpers.process_task_data`
(já existente, nunca chamado) como fonte única de validação; `create_user`/
`update_user` passaram a usar `utils.helpers.validate_email` pelo mesmo motivo;
`Task.validate_status`/`validate_priority` (código morto, redundante com
`process_task_data`) foram removidos; `Model.query.get(id)` (API legacy do
SQLAlchemy) virou `db.session.get(Model, id)` em toda a base; `datetime.utcnow()`
(deprecated) virou um helper `utcnow()` equivalente e não-deprecated, usado em
`models/`, `routes/`, `services/` e `seed.py`; `NotificationService` passou a
receber as credenciais SMTP por injeção (parâmetro/env var) em vez de hardcoded no
construtor — o serviço continua órfão (nenhuma rota o instancia), decisão registrada
no relatório para o usuário avaliar, sem alterar comportamento observável; `app.py`
ganhou `logging.basicConfig` central e `@app.errorhandler(Exception)` (com
passthrough de `HTTPException`, preservando 404/405 nativos do Flask) — os ~13
`try/except` genéricos das rotas de escrita foram removidos, mantendo só o `except`
específico e legítimo de `send_email` (recupera de falha de SMTP); `SECRET_KEY`
passou a vir de `os.environ` via `load_dotenv()` (dependência `python-dotenv`, antes
listada no `requirements.txt` mas nunca usada); `print()` de runtime virou
`logging`; `p1`..`p5` em `reports/summary` renomeados para
`critical_count`/.../`minimal_count`; variáveis de laço `t`/`u`/`c` renomeadas para
`task`/`user`/`category`. Nenhum endpoint foi removido — inclusive o "token" fake de
login (`fake-jwt-token-<id>`) foi mantido, por não constar no relatório de auditoria
como achado do catálogo.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0 + Flask-SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (gestão de tarefas)
- [x] Número de arquivos analisados condiz com a realidade (14 arquivos, ~1059 linhas)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (14)
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()` e `Query.get(id)`, legacy do SQLAlchemy)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC *(mantida a separação já existente — `models/`/`routes/`/`services/`/`utils/` — sem árvore nova, por já estar "parcialmente organizado")*
- [x] Configuração extraída para módulo de config *(sem hardcoded: `SECRET_KEY` e credenciais SMTP lidas de `os.environ`/`load_dotenv()`; sem um `config/` dedicado, por não ter sido exigido pelos achados)*
- [x] Models criados para abstrair dados (já existiam; `to_dict()` do `User` corrigido para não vazar `password`; `validate_status`/`validate_priority` mortos removidos)
- [x] Views/Routes separadas (já existiam; sem mudança estrutural)
- [x] Controllers concentram o fluxo da aplicação *(validação/regra de negócio consolidada reaproveitando `process_task_data`/`validate_email`/`Task.is_overdue()` já existentes, em vez da reimplementação duplicada; a agregação de `reports/summary`/`reports/user/<id>` permanece nos controllers, sem extração para um módulo `services/` dedicado — correção pontual, não a reestruturação completa que um monolito exigiria)*
- [x] Error handling centralizado (`@app.errorhandler(Exception)` em `app.py`, com passthrough de `HTTPException`; `try/except` genéricos removidos das rotas de escrita)
- [x] Entry point claro (`app.py` como composition root)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (todos os 23 endpoints testados manualmente, incluindo `/login`, `/tasks/search`, `/tasks/stats`, `/reports/summary`)

Log da aplicação rodando após a refatoração (Fase 3):

```
2026-07-19 01:21:10,483 INFO routes.user_routes: Usuário criado: 4 - Ana
2026-07-19 01:21:10,547 INFO routes.task_routes: Task criada: 11 - Escrever testes
2026-07-19 01:21:10,576 INFO routes.task_routes: Task atualizada: 1
```

**Observações sobre stacks diferentes**

A skill se comportou de forma agnóstica nas duas stacks testadas (Python/Flask e
Node/Express):

- A heurística de detecção de stack (Fase 1) funcionou sem ajuste manual nos 3
  projetos, incluindo a leitura de `package.json` vs. `requirements.txt`.
- Com o catálogo (9 anti-patterns, 4 severidades), a regra de "adaptação ao
  contexto" das guidelines levou a graus de restruturação bem diferentes conforme o
  estado real de cada projeto. `code-smells-project` e `task-manager-api` tiveram
  achados que vão de CRITICAL/HIGH a LOW, mas os dois já chegavam com as camadas
  separadas em arquivos/pastas (`app.py`/`controllers.py`/`models.py`/`database.py`
  no primeiro; `models/`/`routes/`/`services/`/`utils/` no segundo) — a Fase 3
  aplicou correções pontuais dentro dessa estrutura (um `services.py` novo no
  primeiro; reaproveitamento de helpers/métodos já existentes e nunca chamados no
  segundo) em vez de criar uma árvore MVC do zero. `ecommerce-api-legacy`, ao
  contrário, era um monolito de fato (God Class `AppManager.js` concentrando tudo) —
  o mesmo achado CRITICAL levou, dessa vez, à restruturação completa em camadas
  (`config/`, `db/`, `models/`, `services/`, `controllers/`, `routes/`,
  `middlewares/`), confirmando que a regra reage ao estado real do código, não a um
  molde fixo.
- A mesma transformação conceitual (`print()`/`console.log` → logging estruturado com
  níveis) foi aplicada com implementações diferentes por ecossistema: módulo
  `logging` nativo do Python vs. um logger mínimo escrito à mão em `logger.js`
  (o projeto Node não tinha nenhuma dependência de logging instalada — optou-se por
  não adicionar uma lib externa nova só para isso, mantendo o princípio de menor
  alteração possível).
- A exceção de "banner de CLI legítimo" do catálogo se mostrou necessária nas 3
  stacks (bloco `__main__` do Flask, script `seed.py`, listener do Express) — sem
  ela, o critério teria sinalizado falso-positivo em todas.

**D) Seção "Como Executar":**

**Pré-requisitos**

- **Claude Code** instalado e autenticado (ferramenta escolhida).
- Runtime do projeto alvo para validar o boot na Fase 3:
  - Python/Flask (`code-smells-project`, `task-manager-api`): Python 3 + `pip`.
  - Node/Express (`ecommerce-api-legacy`): Node.js + `npm`.

**Executar a skill (por projeto)**

A skill vive em `code-smells-project/.claude/skills/refactor-arch/`. Entre na pasta do
projeto e invoque o comando:

```bash
cd code-smells-project      # ou o projeto alvo
claude "/refactor-arch"
```

A skill roda em ordem: Fase 1 (análise, imprime o resumo da stack) → Fase 2 (auditoria,
gera o relatório, **salva em `.md` no path/nome que você informar** e pausa em
`[y/n]`) → Fase 3, só após `y` (aplica as transformações e valida).

**Validar que a refatoração funcionou**

- Boot: `pip install -r requirements.txt && python app.py` (ou `npm install && npm start`).
- Endpoints: `curl` nos principais (ex: `GET /health`, `GET /produtos`).
- `code-smells-project` (pós Fase 3): `SECRET_KEY` é opcional (fallback de dev em
  `app.py` se não setada); `ADMIN_API_KEY` é **obrigatória** para os endpoints
  administrativos — sem ela, `/admin/*` responde 503 em vez de ficar aberto. Os
  endpoints administrativos exigem o header `X-Admin-Key`:
  ```bash
  export ADMIN_API_KEY="troque-por-uma-chave-forte"
  curl -X POST http://localhost:5000/admin/reset-db -H "X-Admin-Key: $ADMIN_API_KEY"
  curl -X POST http://localhost:5000/admin/query -H "X-Admin-Key: $ADMIN_API_KEY" \
       -H "Content-Type: application/json" -d '{"sql":"SELECT * FROM produtos"}'
  ```
- `ecommerce-api-legacy` (pós Fase 3): sobe sem nenhuma variável de ambiente
  obrigatória — `DB_USER`, `DB_PASS`, `PAYMENT_GATEWAY_KEY`, `SMTP_USER` e `PORT`
  têm fallback de dev em `src/config/config.js`, sobrescrevíveis via env vars em
  produção. O banco é SQLite em memória com seed automático (mesmo comportamento de
  antes). Endpoints principais:
  ```bash
  curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
       -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
  curl http://localhost:3000/api/admin/financial-report
  curl -X DELETE http://localhost:3000/api/users/1
  ```
- `task-manager-api` (pós Fase 3): sobe sem nenhuma variável de ambiente obrigatória —
  `SECRET_KEY` e as credenciais SMTP de `NotificationService` (usadas só se o serviço
  for instanciado manualmente; nenhuma rota o chama) têm fallback de dev via
  `os.environ`/`load_dotenv()`. Rode `python seed.py` antes do primeiro boot para
  popular usuários/categorias/tasks de exemplo (senhas agora com hash
  `pbkdf2:sha256`, não mais MD5). A resposta de `/login`/`/users/*` não inclui mais o
  campo `password` — era o achado CRITICAL corrigido. Endpoints principais:
  ```bash
  python seed.py
  curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
       -d '{"email":"joao@email.com","password":"1234"}'
  curl http://localhost:5000/tasks
  curl http://localhost:5000/reports/summary
  ```