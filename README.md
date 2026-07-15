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

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou