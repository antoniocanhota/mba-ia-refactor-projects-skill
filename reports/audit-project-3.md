================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 / Flask-SQLAlchemy 3.1.1 / Flask-CORS 4.0.0
Files:   14 analyzed | ~1059 lines of code

## Summary
CRITICAL: 1 | HIGH: 4 | MEDIUM: 7 | LOW: 2

## Findings

### [CRITICAL] Dados sensíveis serializados direto na resposta
File: models/user.py:21 (raiz); consumido em routes/user_routes.py:33, 85-86, 129, 209
Description: `User.to_dict()` inclui o campo `password` (hash MD5) na serialização
(models/user.py:16-25). Esse método é devolvido cru pela API em quatro endpoints:
`GET /users/<id>` (user_routes.py:33), `POST /users` (user_routes.py:85-86),
`PUT /users/<id>` (user_routes.py:129) e `POST /login` (user_routes.py:209 —
que também devolve um token fake `'fake-jwt-token-' + str(user.id)`, previsível e
sem valor de segurança real).
Impact: qualquer cliente da API recebe o hash da senha do usuário. Como o hash é
MD5 (models/user.py:29, sem salt), é trivialmente quebrável por rainbow table,
tornando o vazamento equivalente a expor a senha em texto claro. Acopla também a
resposta pública ao schema interno do model.
Recommendation: introduzir um DTO/serializer de resposta que exclua `password`
(e demais campos internos) — ver playbook "DTO/serializer para a resposta". Ao
aplicar, também trocar o hash para um algoritmo com salt adequado a senha
(ex: `werkzeug.security.generate_password_hash`, já disponível via Flask) —
ajuste incremental que acompanha a correção do vazamento sem remover o endpoint.

### [HIGH] Regra de negócio e montagem de resposta presas no controller (listagem/detalhe de tasks)
File: routes/task_routes.py:11-83
Description: `get_tasks` (11-63) e `get_task` (65-83) constroem o dicionário de
resposta manualmente campo a campo e recalculam a regra de "atrasado" inline
(30-39, 71-80) dentro do handler HTTP, em vez de delegar a `Task.to_dict()` /
`Task.is_overdue()` (já existentes em models/task.py:23-36 e 50-60).
Impact: o controller acumula responsabilidade de regra de negócio e apresentação;
qualquer mudança na regra de "atrasado" ou no formato do dado precisa ser
replicada manualmente em cada handler, sem cobertura de teste unitário isolada.
Recommendation: delegar para os métodos já existentes no model (extrair regra
para camada de serviço/model, conforme playbook "extrair regra para camada de
serviço").

### [HIGH] Validação de entrada duplicada e regra de negócio no controller (criação/atualização de task)
File: routes/task_routes.py:85-154 (create_task), 156-223 (update_task)
Description: as duas funções reimplementam lado a lado a mesma validação de
título (96-100 e 167-170), status (110-111 e 177-179) e prioridade (113-114 e
182-184) diretamente no handler, com regra de negócio (limites, enums) misturada
à montagem de request/response — em vez de delegar a uma camada de
validação/serviço única.
Impact: viola SRP/MVC — a regra de negócio não é testável fora do ciclo HTTP;
divergências entre `create_task` e `update_task` podem surgir silenciosamente
se uma das cópias for atualizada e a outra não.
Recommendation: extrair a validação para uma camada de serviço/model única e
reutilizá-la nos dois handlers (playbook "extrair regra para camada de serviço").

### [HIGH] Agregação de relatório como lógica de negócio dentro do controller
File: routes/report_routes.py:12-155 (summary_report 12-101, user_report 103-155)
Description: os handlers de relatório concentram consultas, laços de agregação
(contagem por status/prioridade, cálculo de atraso, produtividade por usuário) e
montagem de resposta inteiramente dentro da rota, sem nenhuma camada de
serviço/repositório intermediária.
Impact: lógica de agregação de negócio não reutilizável nem testável
isoladamente do Flask; qualquer novo relatório tende a copiar o mesmo padrão,
aumentando a duplicação.
Recommendation: extrair a lógica de agregação para uma camada de serviço
(ex: `services/report_service.py`), mantendo o controller apenas como
orquestrador (playbook "extrair regra para camada de serviço").

### [HIGH] Estado/configuração acoplada sem injeção de dependência
File: services/notification_service.py:5-10
Description: `NotificationService.__init__` hardcoda host, porta, usuário e senha
do SMTP como atributos fixos da instância (`self.email_password = 'senha123'`),
em vez de recebê-los por injeção (parâmetro/config). Adicionalmente, a classe
nunca é instanciada em nenhuma rota (confirmado por busca no repositório) — é
código órfão, sem nenhum caminho de chamada real.
Impact: credenciais de acesso ao SMTP ficam hardcoded no código-fonte (exposição
em qualquer leitura do repositório/versionamento); a dependência concreta
impede testes com dublê/mocks; o serviço órfão engana quem lê o código supondo
que notificações estão ativas.
Recommendation: injetar as credenciais via configuração (env vars/`app.config`)
no construtor (composition root), e decidir com o usuário se o serviço deve ser
integrado a algum fluxo real (ex: ao atribuir uma task) ou removido — não decidir
isso unilateralmente na Fase 3 (playbook "injeção de dependência / composition root").

### [MEDIUM] Duplicação — cálculo de "atrasado" reimplementado 5 vezes
File: routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180;
routes/report_routes.py:33-43, 132-135
Description: o mesmo bloco condicional (`due_date < utcnow() and status not in
('done','cancelled')`) é reimplementado à mão em 5 locais diferentes, enquanto
`Task.is_overdue()` (models/task.py:50-60) já existe pronto e nunca é chamado em
lugar nenhum (confirmado por busca no repositório).
Impact: correções à regra de "atrasado" exigem editar 5 lugares; risco de
divergência silenciosa entre as cópias.
Recommendation: substituir todas as ocorrências por chamadas a
`task.is_overdue()` (playbook "extrair/reusar lógica duplicada").

### [MEDIUM] Duplicação — validação de status/prioridade ignorando model e helper existentes
File: routes/task_routes.py:110-114, 182-184 (status/prioridade); models/task.py:38-48
(`validate_status`/`validate_priority`, nunca chamados); utils/helpers.py:57-108
(`process_task_data`, nunca importado/chamado)
Description: existem três implementações da mesma validação de status/prioridade
de task — os métodos do model, a função utilitária `process_task_data` e a
validação inline duplicada em `create_task`/`update_task` — mas só a versão
inline é de fato usada; as outras duas são código morto.
Impact: três fontes de verdade para a mesma regra, sem garantia de que
permaneçam consistentes; o código morto confunde a leitura, sugerindo um
padrão de validação que não é seguido.
Recommendation: escolher uma única fonte de verdade (o helper `process_task_data`
é o mais completo) e remover as reimplementações redundantes ou fazer as rotas
chamarem-no (playbook "extrair/reusar lógica duplicada").

### [MEDIUM] Duplicação — validação de email ignorando utils.helpers.validate_email
File: routes/user_routes.py:61, 106; utils/helpers.py:19-23 (`validate_email`,
nunca chamado)
Description: a mesma regex de validação de email (`^[a-zA-Z0-9+_.-]+@...`) é
reescrita inline em `create_user` e `update_user`, idêntica à função
`validate_email` já definida em utils/helpers.py e nunca referenciada.
Impact: duplicação de regra que pode divergir silenciosamente se uma cópia for
ajustada e a outra não; função utilitária existente vira código morto.
Recommendation: substituir as duas ocorrências por chamadas a
`validate_email(email)` (playbook "extrair/reusar lógica duplicada").

### [MEDIUM] Uso de API deprecated — datetime.utcnow()
File: 18 ocorrências, entre elas models/user.py:14, models/task.py:15-16,
routes/task_routes.py:31, 136, 203, 215, routes/user_routes.py:172, 215,
routes/report_routes.py:35, 42, 45, 46, 50, utils/helpers.py:38,
services/notification_service.py:35
Description: `datetime.utcnow()` está marcado como deprecated desde Python 3.12
em favor de `datetime.now(datetime.UTC)` (retorna datetime naive vs. aware).
Impact: comportamento naive de fuso horário já é fonte de bugs sutis em
comparação/serialização, e o símbolo será removido em versão futura do Python —
dívida técnica que cresce a cada upgrade de runtime.
Recommendation: substituir todas as ocorrências por
`datetime.now(datetime.UTC)` (playbook "substituir API deprecated pelo
equivalente moderno").

### [MEDIUM] Uso de API deprecated — SQLAlchemy Query.get(id)
File: 16 ocorrências, entre elas routes/task_routes.py:42, 51, 67, 117, 122, 158,
188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105
Description: `Model.query.get(id)` é a API legacy do SQLAlchemy 1.x, marcada
como legacy na migração para SQLAlchemy 2.0 (a versão usada por
flask-sqlalchemy 3.1.1) em favor de `db.session.get(Model, id)`.
Impact: código preso ao estilo de query legacy, perdendo o caminho de migração
recomendado pelo próprio SQLAlchemy 2.0 e a consistência com a API moderna de
`Session`.
Recommendation: substituir por `db.session.get(Model, id)` (playbook
"substituir API deprecated pelo equivalente moderno").

### [MEDIUM] Tratamento de erro espalhado / não centralizado
File: routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87,
130, 149; routes/report_routes.py:186, 207, 221; services/notification_service.py:23
— nenhum `@app.errorhandler` registrado em app.py
Description: 13 blocos `try/except` (vários com `except:` nu) repetem o mesmo
padrão de rollback + resposta de erro genérica, cada handler montando sua
própria mensagem. Não existe nenhum error handler central registrado em app.py.
Impact: boilerplate duplicado em quase todo endpoint; risco de inconsistência
nas respostas de erro; captura genérica demais esconde a causa raiz de falhas
inesperadas.
Recommendation: registrar handlers centrais com `@app.errorhandler` para as
classes de exceção relevantes (ex: `SQLAlchemyError`, `ValueError`) e remover o
try/except repetido dos handlers (playbook "error handler centralizado /
middleware").

### [LOW] print() como mecanismo de logging
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147;
services/notification_service.py:21, 24; utils/helpers.py:39, 41 (`log_action`,
nunca chamado)
Description: eventos de sucesso/erro de runtime (criação/atualização/remoção de
task e usuário, envio de email) são registrados via `print()` em vez de um
logger configurável. A própria função utilitária `log_action` existe para esse
fim e nunca é chamada.
Impact: sem nível, timestamp estruturado ou destino configurável; impossível
filtrar/rotear em produção; mistura diagnóstico com stdout da aplicação.
Recommendation: substituir por `logging` padrão do Python configurado no
composition root (playbook "print() → logging").

### [LOW] Nomenclatura fraca de variáveis
File: routes/report_routes.py:24-28 (`p1`..`p5`); routes/task_routes.py (loop
`for t in tasks`/`for t in all_tasks`, ex: 16, 268, 283); routes/user_routes.py
(loop `for u in users`, `for t in tasks`, ex: 14, 37); routes/report_routes.py
(`for t in ...`, `for u in users`, `for c in categories`, ex: 33, 55, 161)
Description: os buckets de prioridade em `summary_report` usam sufixos
numéricos (`p1`, `p2`, `p3`, `p4`, `p5`) em vez de nomear o papel de cada um
(o mapeamento real — `critical`/`high`/`medium`/`low`/`minimal` — só aparece
depois, no dict de resposta). Além disso, variáveis de laço de escopo não
trivial usam uma letra para entidades de domínio inteiras (`t` para Task,
`u` para User, `c`/`cc` para Category) em vários arquivos.
Impact: quem lê `p1`..`p5` precisa pular para o dict de resposta para entender
o que cada variável representa; `t`/`u`/`c` de uma letra para entidades de
domínio (não índices triviais) obriga reconstruir o significado pelo uso.
Recommendation: renomear `p1..p5` para `critical_count`/`high_count`/etc., e os
loops para `task`/`user`/`category` (playbook "renomear para nomes
intencionais").

================================
Total: 14 findings
================================
