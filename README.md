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

> **Estado atual (MVP):** a skill foi construída de forma incremental. Esta versão
> trata **1 anti-pattern LOW** (`print()` como logging) percorrendo as 3 fases
> ponta-a-ponta, e foi projetada para crescer (novos anti-patterns entram nos
> arquivos de referência sem alterar o fluxo). Ferramenta escolhida: **Claude Code**.

**Decisões de design — SKILL.md e arquivos de referência**

- `SKILL.md` curto (~130 linhas, bem abaixo do teto de ~300/500), atuando só como
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

- Hoje: **`print()` como mecanismo de logging (LOW)** — escolhido como primeiro caso
  por ser simples, de detecção inequívoca (`grep 'print('`) e transformação segura
  (troca por `logging` com níveis), permitindo validar o pipeline inteiro com baixo
  risco. Serve de "esqueleto de crescimento".
- `refactoring-playbook.md` ainda traz, em bloco-comentário, o mapa das
  transformações previstas para atingir os mínimos da spec (≥8 anti-patterns,
  ≥8 transformações, incluindo detecção de APIs deprecated): credenciais hardcoded,
  SQL Injection, God Class, endpoint sem auth, regra de negócio no controller, estado
  global mutável, N+1, try/except vazando erro, magic values, etc. O bloco equivalente
  foi removido de `anti-patterns.md` depois que execuções da skill passaram a tratar
  esses rascunhos como catálogo formal, inflando relatórios de auditoria com achados
  sem sinais de detecção definidos — o catálogo agora reflete só o que está de fato
  implementado (1 anti-pattern LOW).

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

**C) Seção "Resultados":**

> Nesta sessão a skill foi executada **apenas no `code-smells-project`** (Python/Flask).
> `ecommerce-api-legacy` (Node/Express) e `task-manager-api` (Python/Flask) têm, até
> aqui, **somente a análise manual** da seção A — ainda não foram processados pela
> skill. Os números abaixo refletem o **catálogo MVP (1 anti-pattern)**, e por isso
> diferem — de propósito — da análise manual mais ampla da seção A.

***code-smells-project*** (Python/Flask) — *processado pela skill*

Stack detectada na Fase 1: Python + Flask 3.1.1 + flask-cors, SQLite (tabelas
`produtos`, `usuarios`, `pedidos`, `itens_pedido`), domínio E-commerce, 4 arquivos
(~780 linhas), arquitetura monolítica.

Resumo do relatório de auditoria (Fase 2):

| CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| 0 | 0 | 0 | 1 | 1 |

Único finding: `[LOW] print() como mecanismo de logging` em `controllers.py`
(14 ocorrências) e `app.py:56` — banners de startup de CLI preservados.

Antes / depois da estrutura: não houve restruturação de diretórios (o único achado
LOW não a justifica). A mudança foi in-place: `import logging` + `logger` por módulo;
`print(...)` → `logger.info / warning / exception`; `logging.basicConfig` central em
`app.py`. Estrutura de arquivos inalterada (`app.py`, `controllers.py`, `models.py`,
`database.py`).

Checklist de validação:

- [x] Aplicação inicializa sem erros (`python app.py` / runner em porta 5055)
- [x] Endpoints respondem: `GET /health` → 200, `GET /produtos` → 200, `POST /produtos` → 201
- [x] Zero ocorrências remanescentes do anti-pattern corrigido (só banners CLI)
- [x] Fixture revertido ao estado original após o teste

Log da aplicação rodando após a refatoração (Fase 3):

```
2026-... INFO werkzeug:  * Running on http://127.0.0.1:5055
2026-... INFO werkzeug: 127.0.0.1 - - "GET /health HTTP/1.1" 200 -
2026-... INFO controllers: Listando 10 produtos
2026-... INFO werkzeug: 127.0.0.1 - - "GET /produtos HTTP/1.1" 200 -
2026-... INFO controllers: Produto criado com ID: 11
2026-... INFO werkzeug: 127.0.0.1 - - "POST /produtos HTTP/1.1" 201 -
```

Os `print()` viraram logging estruturado (timestamp + nível + logger), confirmando a
transformação.

***ecommerce-api-legacy*** (Node/Express) — *skill ainda não executada*

- Auditoria (Fase 2): não executada nesta sessão.
- Refatoração (Fase 3): não executada.
- Checklist de validação: não aplicável ainda.
- Situação atual: existe apenas a **análise manual** da seção A. Rodar a skill aqui é
  o próximo passo para exercitar a natureza agnóstica numa stack Node/Express.

***task-manager-api*** (Python/Flask) — *skill ainda não executada*

- Auditoria (Fase 2): não executada nesta sessão.
- Refatoração (Fase 3): não executada.
- Checklist de validação: não aplicável ainda.
- Situação atual: existe apenas a **análise manual** da seção A. Diferencial deste
  projeto: já possui uma camada `services/` (ignorada pelos controllers), o que muda o
  tipo de refatoração esperada na Fase 3.

**Observações sobre stacks diferentes**

Ainda não aplicável: nesta sessão a skill só rodou em Python/Flask
(`code-smells-project`). Executá-la no `ecommerce-api-legacy` (Node/Express) e no
`task-manager-api` fecha as lacunas acima e valida o comportamento agnóstico na prática.

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