================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0 (+ Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0)
Dependencies:  flask-sqlalchemy (ORM), flask-cors (CORS), marshmallow (declarada em
               requirements.txt, mas não utilizada no código-fonte), requests,
               python-dotenv
Domain:        Task Manager API — gestão de usuários, tasks (com status/prioridade/
               due date/tags) e categorias, com relatórios de produtividade
Architecture:  Parcialmente em camadas — `models/` (Task, User, Category via
               SQLAlchemy), `routes/` (Blueprints Flask: task_routes, user_routes,
               report_routes), `services/` (NotificationService), `utils/`
               (helpers.py). Não há camada de serviço para as regras de negócio de
               tasks/users/categories: validação, formatação de resposta e acesso a
               dados estão concentrados diretamente nos arquivos de rotas
               (`routes/*.py`), que fazem queries SQLAlchemy diretamente e montam
               os dicionários de resposta manualmente. `services/` existe mas só
               contém envio de notificação por e-mail; `utils/helpers.py` define
               funções utilitárias (`process_task_data`, `parse_date`, etc.) que
               não são usadas pelas rotas atuais (lógica duplicada em vez de
               reaproveitada). Não há camada de configuração dedicada — segredos e
               config do Flask ficam hardcoded em `app.py`.
Source files:  15 files analyzed (~1158 lines of code)
DB tables:     tasks, users, categories (SQLite, arquivo `tasks.db`, via
               Flask-SQLAlchemy)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy, Flask-CORS)
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 11

## Findings

### [LOW] print() como mecanismo de logging
File: routes/task_routes.py:149
Description: Dentro de `create_task`, após o commit bem-sucedido, `print(f"Task criada: {task.id} - {task.title}")` registra o evento de sucesso via stdout.
Impact: Log de sucesso sem nível, timestamp ou destino configurável; não pode ser roteado/filtrado em produção.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: routes/task_routes.py:153
Description: No bloco `except Exception as e` de `create_task`, `print(f"Erro ao criar task: {str(e)}")` reporta a falha via stdout em vez de um logger.
Impact: Erros de runtime não ficam registrados de forma estruturada; impossível diferenciar severidade ou persistir o log.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: routes/task_routes.py:219
Description: Em `update_task`, após o commit, `print(f"Task atualizada: {task.id}")` registra o evento de sucesso via stdout.
Impact: Mesma limitação de observabilidade — sem nível/timestamp/destino configurável.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: routes/task_routes.py:234
Description: Em `delete_task`, após o commit, `print(f"Task deletada: {task_id}")` registra o evento via stdout.
Impact: Mesma limitação de observabilidade.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: routes/user_routes.py:83
Description: Em `create_user`, após o commit, `print(f"Usuário criado: {user.id} - {user.name}")` registra o evento de sucesso via stdout.
Impact: Mesma limitação de observabilidade.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: routes/user_routes.py:89
Description: No bloco `except Exception as e` de `create_user`, `print(f"ERRO: {str(e)}")` reporta a falha via stdout.
Impact: Erros de runtime não ficam registrados de forma estruturada.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: routes/user_routes.py:147
Description: Em `delete_user`, após o commit, `print(f"Usuário deletado: {user_id}")` registra o evento via stdout.
Impact: Mesma limitação de observabilidade.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: services/notification_service.py:21
Description: Em `send_email`, após o envio bem-sucedido, `print(f"Email enviado para {to}")` registra o evento via stdout.
Impact: Mesma limitação de observabilidade; num serviço de notificação isso dificulta auditar falhas de entrega em produção.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: services/notification_service.py:24
Description: No bloco `except Exception as e` de `send_email`, `print(f"Erro ao enviar email: {str(e)}")` reporta a falha via stdout.
Impact: Falhas de envio de e-mail (ex: SMTP fora do ar) não ficam registradas de forma estruturada nem alertável.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: utils/helpers.py:39
Description: A função utilitária `log_action(action, details=None)` usa `print(f"[{timestamp}] ACTION: {action}")` como sua implementação de log — ou seja, o próprio helper "de log" do projeto é baseado em `print()`.
Impact: Sinaliza a ausência de um logger real na base: mesmo a função pensada para centralizar logging usa stdout puro, sem nível/timestamp estruturado/destino configurável.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

### [LOW] print() como mecanismo de logging
File: utils/helpers.py:41
Description: Mesma função `log_action`, linha seguinte: `print(f"  DETAILS: {details}")` quando `details` é informado.
Impact: Mesma limitação de observabilidade do finding anterior (mesmo bloco contíguo de uma única função).
Recommendation: Ver `refactoring-playbook.md` → "print() → logging".

================================
Total: 11 findings
================================

## Observação sobre ocorrências excluídas

`seed.py:93-96` contém `print("Seed concluído com sucesso!")` e três `print(f"...")`
subsequentes reportando contagens de usuários/categorias/tasks. Foram avaliados e
**não contabilizados** como ocorrência: o catálogo define explicitamente que
"banners de inicialização de CLI e mensagens de UX de linha de comando podem ser
`print` legítimo" — `seed.py` é executado como script standalone (`python seed.py`)
e essas chamadas são mensagens de status de UX de linha de comando, não logging de
runtime de um handler/serviço da aplicação web.

## Observações fora do catálogo atual (não pontuadas)

Estes pontos não fazem parte do catálogo formal (que hoje cobre apenas
print()-como-logging) e por isso **não entram no Summary/Total oficial acima**.
Registrados apenas como observação para eventual expansão futura do catálogo:

- `app.py:13` — `SECRET_KEY` hardcoded no código-fonte (`'super-secret-key-123'`).
- `models/user.py:29,32` — senha de usuário com hash MD5 (`hashlib.md5`), algoritmo
  criptograficamente quebrado para senhas.
- `services/notification_service.py:9-10` — credenciais de e-mail (usuário/senha
  SMTP) hardcoded na classe.
- `routes/user_routes.py:210` — token de login fake/estático
  (`'fake-jwt-token-' + str(user.id)`), sem autenticação real.
- `routes/task_routes.py:11-63,240-271` / `routes/report_routes.py` — regra de
  negócio (cálculo de overdue, montagem de payload, agregações de relatório)
  escrita diretamente nas rotas, sem camada de serviço, com bastante duplicação de
  lógica (o cálculo de "overdue" é repetido quase identicamente em pelo menos 4
  lugares: `task_routes.py:30-39`, `task_routes.py:71-80`, `task_routes.py:283-287`,
  `user_routes.py:171-180`, `report_routes.py:33-37`, `report_routes.py:132-135`).
- `utils/helpers.py` — várias funções (`process_task_data`, `validate_email`,
  `sanitize_string`, `parse_date`) parecem ter sido criadas para centralizar
  validação/parsing, mas não são chamadas por nenhuma rota — as rotas reimplementam
  a mesma validação inline.
- `app.py:62` (bloco `except:` genérico em `task_routes.py:62`, `user_routes.py:130`,
  `user_routes.py:150`, `report_routes.py:186`, `report_routes.py:207`,
  `report_routes.py:221`) — `except:` sem tipo captura qualquer exceção
  indiscriminadamente.
