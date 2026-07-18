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
> **7 anti-patterns cobrindo as 4 severidades** — 2 CRITICAL, 2 HIGH, 2 MEDIUM e
> 1 LOW — percorrendo as 3 fases ponta-a-ponta, e continua projetada para crescer
> (novos anti-patterns entram nos arquivos de referência sem alterar o fluxo).
> Ferramenta escolhida: **Claude Code**.

**Decisões de design — SKILL.md e arquivos de referência**

- `SKILL.md` curto (~133 linhas, bem abaixo do teto de ~300/500), atuando só como
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

O catálogo cobre **7 anti-patterns nas 4 severidades**, priorizando os que são
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
| MEDIUM | Validação de entrada ausente nas rotas | Entrada usada sem checagem de tipo/formato vira 500 em vez de 400 — citado nominalmente na definição de MEDIUM |
| LOW | `print()` como mecanismo de logging | Primeiro caso construído: detecção inequívoca (`grep 'print('`) e transformação segura (troca por logging com níveis); validou o pipeline inteiro com baixo risco |

- **Critério de seleção e alinhamento à escala:** um candidato inicial de MEDIUM ("God
  _function_ de inicialização" misturando conexão + schema + seed) foi descartado por ser,
  na verdade, uma violação de separação de responsabilidades — conceito que a escala coloca
  em CRITICAL (God Class), não em MEDIUM. Foi substituído por "validação de entrada ausente
  nas rotas", que a definição de MEDIUM cita nominalmente. Isso mantém o catálogo coerente
  com a própria taxonomia de severidade.
- **Sem catálogo-fantasma:** o antigo bloco-comentário com transformações "previstas" foi
  removido do `refactoring-playbook.md` agora que estão de fato implementadas — o catálogo
  reflete só o que a skill realmente detecta e corrige, evitando inflar relatórios de
  auditoria com achados sem sinais de detecção definidos.

**Como se garante que a skill é agnóstica de tecnologia**

- As heurísticas e o catálogo descrevem **sinais**, não uma stack fixa: detecção de
  linguagem por extensão + manifesto (Python, Node, Ruby, Go, Java, PHP...) e de
  framework por dependências/imports.
- Cada anti-pattern/transformação lista **equivalentes por stack** (ex: `print` /
  `console.log` / `System.out.println` / `fmt.Println` / `puts`).
- As guidelines de arquitetura instruem a **adaptar a nomenclatura de camadas** ao
  ecossistema detectado.

**Desafios encontrados e como resolvi**

- **Validar sem sujar o fixture:** a Fase 3 foi testada de verdade (boot + endpoints)
  e depois **revertida via git**, preservando o `code-smells-project` no estado
  original de entrada do desafio.
- **Escala de severidade genérica interferindo na classificação:** `anti-patterns.md`
  tinha uma seção "Escala de severidade" no topo do arquivo, além da severidade já
  anotada em cada entrada do catálogo. Essa seção citava exemplos soltos (ex: "SQL
  Injection" como CRITICAL) que acabaram sendo usados para elevar achados além da
  severidade definida na entrada específica do catálogo, tornando a classificação
  inconsistente entre auditorias. Removida a pedido do usuário — a severidade de um
  finding vem só da entrada correspondente do catálogo, nunca de uma escala geral solta.
- **Fase 3 removeu um endpoint em vez de protegê-lo:** ao rodar a Fase 3 em
  `code-smells-project`, o endpoint `/admin/query` (executa SQL arbitrário vindo do
  cliente, achado CRITICAL) foi **removido** por ter sido interpretado como "sem fix
  seguro possível". O usuário corrigiu: o checklist de validação já exige "Endpoints
  originais respondem corretamente" — a correção certa é **proteger** (autenticação),
  nunca **apagar** funcionalidade. `SKILL.md` ganhou uma regra operacional explícita
  proibindo remoção de endpoints/funcionalidade na Fase 3, mesmo para achados CRITICAL
  sem correção óbvia; o endpoint foi restaurado atrás de autenticação por token.

**C) Seção "Resultados":**

> A skill foi executada ponta-a-ponta (Fase 1 → Fase 2 → Fase 3) nos **3 projetos**.
> Os números abaixo refletem o **catálogo MVP (1 anti-pattern: `print()`/`console.log`
> como logging, LOW)** — de propósito menor que a análise manual mais ampla da seção A,
> que cobre categorias (SQL Injection, credenciais hardcoded, God Class, endpoints sem
> auth etc.) ainda não formalizadas no catálogo desta versão da skill.

Resumo consolidado dos relatórios de auditoria (Fase 2, `reports/audit-project-{1,2,3}.md`):

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project | 0 | 0 | 0 | 13 | 13 |
| ecommerce-api-legacy | 0 | 0 | 0 | 2 | 2 |
| task-manager-api | 0 | 0 | 0 | 11 | 11 |

Todos os findings são a mesma categoria (`print()`/`console.log` como logging); cada
relatório também documenta, em seção separada e **não pontuada** no total acima,
achados reais fora do catálogo atual (SQL Injection, credenciais hardcoded, God Class,
endpoints sem auth, hash de senha caseiro, N+1, etc.) — mantidos como roteiro para
incrementos futuros do catálogo, sem serem tratados como confirmados nesta versão MVP.

***code-smells-project*** (Python/Flask) — *processado pela skill*

Stack detectada na Fase 1: Python + Flask 3.1.1 + flask-cors, SQLite (tabelas
`produtos`, `usuarios`, `pedidos`, `itens_pedido`), domínio E-commerce, 4 arquivos
(~780 linhas), arquitetura monolítica.

Antes / depois da estrutura: não houve restruturação de diretórios (achados LOW
isolados não a justificam). Mudança in-place em `app.py` e `controllers.py`:
`import logging` + `logging.basicConfig` central em `app.py`; `logger =
logging.getLogger(__name__)` por módulo; os 13 `print()` de runtime (sucesso/erro em
CRUD de produtos, usuários, login e pedidos, e o reset destrutivo do banco) viraram
`logger.info` / `logger.warning` / `logger.exception` com argumentos lazy (`%s`).
Banner de CLI em `app.py` (bloco `__main__`) preservado. Estrutura de arquivos
inalterada (`app.py`, `controllers.py`, `models.py`, `database.py`).

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
- [x] Mínimo de 5 findings identificados (13)
- [ ] Detecção de APIs deprecated incluída *(não implementada nesta versão do catálogo)*
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC *(fora de escopo: único achado é LOW e isolado, guideline de "adaptação ao contexto" não exige restruturação)*
- [ ] Configuração extraída para módulo de config *(fora de escopo do único anti-pattern do catálogo)*
- [ ] Models criados para abstrair dados *(já existiam; não é objeto desta transformação)*
- [ ] Views/Routes separadas *(fora de escopo)*
- [ ] Controllers concentram o fluxo da aplicação *(fora de escopo)*
- [ ] Error handling centralizado *(fora de escopo)*
- [x] Entry point claro (`app.py`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

Log da aplicação rodando após a refatoração (Fase 3):

```
2026-07-17 23:26:57,139 INFO controllers: Listando 10 produtos
2026-07-17 23:26:57,140 INFO werkzeug: 127.0.0.1 - - "GET /produtos HTTP/1.1" 200 -
2026-07-17 23:26:58,004 INFO controllers: Produto criado com ID: 11
2026-07-17 23:26:58,005 INFO werkzeug: 127.0.0.1 - - "POST /produtos HTTP/1.1" 201 -
```

***ecommerce-api-legacy*** (Node/Express) — *processado pela skill*

Stack detectada na Fase 1: Node.js + Express, SQLite (via `sqlite3`), domínio
E-commerce/checkout, 3 arquivos-fonte (~180 linhas), God Class `AppManager.js`.

Antes / depois da estrutura: não houve restruturação de diretórios (achados LOW
isolados não a justificam). Único arquivo novo: `src/logger.js` — logger mínimo com
níveis (`error/warn/info/debug`), timestamp ISO e nome do módulo de origem, nível
configurável via `LOG_LEVEL`. `src/app.js` chama `configureLogger(...)` uma única vez
no boot; `src/AppManager.js` e `src/utils.js` trocaram os 2 `console.log` de runtime
(log do processamento de pagamento e do `logAndCache`) por `logger.info(...)`. Banner
de boot em `src/app.js` (`"Frankenstein LMS rodando na porta..."`) preservado — é UX
de inicialização, não log de runtime.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express)
- [x] Domínio da aplicação descrito corretamente (checkout/pagamentos)
- [x] Número de arquivos analisados condiz com a realidade (3 arquivos, ~180 linhas)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados *(apenas 2 — projeto pequeno, catálogo MVP cobre só 1 categoria; ≥5 exigiria os anti-patterns ainda não formalizados, ver seção "observações fora do catálogo" do relatório)*
- [ ] Detecção de APIs deprecated incluída *(não implementada nesta versão do catálogo)*
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC *(fora de escopo: único achado é LOW e isolado)*
- [ ] Configuração extraída para módulo de config *(fora de escopo do único anti-pattern do catálogo)*
- [ ] Models criados para abstrair dados *(fora de escopo)*
- [ ] Views/Routes separadas *(fora de escopo)*
- [ ] Controllers concentram o fluxo da aplicação *(fora de escopo — `AppManager.js` continua God Class)*
- [ ] Error handling centralizado *(fora de escopo)*
- [x] Entry point claro (`src/app.js`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

Formato de log emitido por `src/logger.js` (determinístico a partir da implementação:
timestamp ISO + nível + nome do módulo):

```
2026-07-17T23:41:12.558Z INFO [AppManager]: Processando cartão 4111... na chave sk_test_...
2026-07-17T23:41:12.560Z INFO [utils]: Salvando no cache: pedido_123
```

***task-manager-api*** (Python/Flask) — *processado pela skill*

Stack detectada na Fase 1: Python + Flask 3.0.0, SQLAlchemy + SQLite, domínio gestão
de tarefas, 16 arquivos (~1177 linhas), já possui camada `services/` (mas ignorada
pelos controllers — ver seção A).

Antes / depois da estrutura: não houve restruturação de diretórios (achados LOW
isolados não a justificam). `app.py` ganhou `logging.basicConfig` central; `logger =
logging.getLogger(__name__)` adicionado em `utils/helpers.py`,
`services/notification_service.py`, `routes/task_routes.py` e `routes/user_routes.py`;
os 11 `print()` de runtime (log de ações, envio de e-mail, CRUD de tasks/usuários)
viraram `logger.info` / `logger.exception`. Banners de CLI em `seed.py` preservados
(script standalone). Estrutura de arquivos inalterada.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0 + SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (gestão de tarefas)
- [x] Número de arquivos analisados condiz com a realidade (16 arquivos, ~1177 linhas)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11)
- [ ] Detecção de APIs deprecated incluída *(não implementada nesta versão do catálogo)*
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC *(já parcialmente organizado; camada `services/` existente não foi ligada aos controllers — fora de escopo do único anti-pattern do catálogo)*
- [ ] Configuração extraída para módulo de config *(fora de escopo)*
- [ ] Models criados para abstrair dados *(já existiam; não é objeto desta transformação)*
- [ ] Views/Routes separadas *(já existiam; não é objeto desta transformação)*
- [ ] Controllers concentram o fluxo da aplicação *(fora de escopo)*
- [ ] Error handling centralizado *(fora de escopo)*
- [x] Entry point claro (`app.py`)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

Log da aplicação rodando após a refatoração (Fase 3):

```
2026-07-17 ... INFO routes.user_routes: Usuário criado: 1 - Ana
```

**Observações sobre stacks diferentes**

A skill se comportou de forma agnóstica nas duas stacks testadas (Python/Flask e
Node/Express):

- A heurística de detecção de stack (Fase 1) funcionou sem ajuste manual nos 3
  projetos, incluindo a leitura de `package.json` vs. `requirements.txt`.
- A mesma transformação conceitual (`print()`/`console.log` → logging estruturado com
  níveis) foi aplicada com implementações diferentes por ecossistema: módulo
  `logging` nativo do Python vs. um logger mínimo escrito à mão em `logger.js`
  (o projeto Node não tinha nenhuma dependência de logging instalada — optou-se por
  não adicionar uma lib externa nova só para isso, mantendo o princípio de menor
  alteração possível).
- A exceção de "banner de CLI legítimo" do catálogo se mostrou necessária nas 3
  stacks (bloco `__main__` do Flask, script `seed.py`, listener do Express) — sem
  ela, o critério teria sinalizado falso-positivo em todas.
- Nenhum dos 3 projetos exigiu reestruturação de diretórios nesta rodada, já que o
  único anti-pattern confirmado é LOW e isolado — a regra de "adaptação ao contexto"
  das guidelines evitou impor uma árvore MVC completa sem necessidade. Isso também
  explica por que a checklist de Fase 3 acima tem vários itens de arquitetura MVC
  não marcados: eles pertencem ao alvo final da skill, não ao escopo do catálogo
  MVP atual.

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