================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  express (^4.18.2), sqlite3 (^5.1.6)
Domain:        E-commerce/LMS — API de checkout de cursos ("Frankenstein LMS": usuários, cursos, matrículas, pagamentos, auditoria)
Architecture:  Monolítica — bootstrap em app.js; toda a lógica (inicialização/seed do banco, definição de rotas, regras de negócio e SQL) concentrada na classe AppManager (God Class) em AppManager.js; utils.js concentra configuração hardcoded, estado global mutável e helpers. Não há camadas separadas de models, controllers, services ou rotas — nenhuma estrutura MVC presente.
Source files:  3 files analyzed (app.js, AppManager.js, utils.js) | ~180 lines of code
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória, schema criado e populado via seed em AppManager.initDb())
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 0 | HIGH: 0 | MEDIUM: 0 | LOW: 2

## Findings

### [LOW] print() como mecanismo de logging
File: src/AppManager.js:45
Description: Dentro do handler `POST /api/checkout`, a chamada `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` registra um evento de runtime (processamento de pagamento) diretamente no stdout, sem nível, timestamp ou destino configurável.
Impact: Logs não podem ser filtrados, roteados ou silenciados em produção; mistura diagnóstico com saída da aplicação. Adicionalmente, expõe dados sensíveis (número do cartão e chave do gateway de pagamento) em texto puro no log — agrava o impacto padrão do anti-pattern, embora a severidade catalogada para esta entrada permaneça LOW.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging". Substituir por um logger estruturado (ex: Winston/Pino) com nível apropriado, e nunca logar dados sensíveis (mascarar/omitir número de cartão e chaves de API).

### [LOW] print() como mecanismo de logging
File: src/utils.js:13
Description: A função utilitária `logAndCache(key, data)` usa `console.log(\`[LOG] Salvando no cache: ${key}\`)` para registrar um evento de runtime (gravação em cache) toda vez que é chamada (ex: a partir de `AppManager.js:59`).
Impact: Logs não têm nível, timestamp nem destino configurável; impossível silenciar, rotear ou filtrar em produção; polui stdout e mistura diagnóstico com saída da aplicação.
Recommendation: Ver `refactoring-playbook.md` → "print() → logging". Substituir por um logger estruturado configurável por ambiente.

================================
Total: 2 findings
================================

## Ocorrência avaliada e excluída (com ressalva)

- `src/app.js:13` — `console.log(\`Frankenstein LMS rodando na porta ${config.port}...\`)` é exibido uma única vez no boot da aplicação, reportando que o servidor subiu com sucesso. Foi tratado como análogo ao caso de exceção do catálogo ("banners de inicialização de CLI e mensagens de UX de linha de comando podem ser print legítimo") e por isso **não** foi contado como ocorrência do anti-pattern.

## Observações fora do catálogo atual (não pontuadas)

O catálogo formal de `anti-patterns.md` cobre atualmente apenas 1 entrada (print()/console.log como logging, LOW). Os itens abaixo são problemas reais identificados no código, mas **não fazem parte do catálogo hoje** e, portanto, não foram somados ao Summary/Total oficial acima. Ficam registrados apenas como observação para eventual expansão futura do catálogo:

- **God Class / ausência de camadas MVC**: `AppManager.js` concentra inicialização de banco, roteamento HTTP, regras de negócio e SQL em uma única classe (todo o arquivo, 141 linhas).
- **Credenciais e chaves hardcoded**: `src/utils.js:2-6` — `dbUser`, `dbPass`, `paymentGatewayKey` e `smtpUser` embutidos no código-fonte em texto puro.
- **Hash de senha inseguro/artesanal**: `src/utils.js:17-23` (`badCrypto`) — usa Base64 repetido como "hash", não é um algoritmo criptográfico de senha (ex: bcrypt/argon2); senha default fraca `"123456"` quando não informada (`AppManager.js:68`).
- **Estado global mutável**: `src/utils.js:9-10` (`globalCache`, `totalRevenue`) — variáveis de módulo mutáveis compartilhadas entre requisições, sem isolamento.
- **Regra de negócio dentro do controller/rota**: validação de pagamento, aprovação/recusa de cartão (`cc.startsWith("4")`) e orquestração de matrícula/pagamento ficam inline dentro do handler `POST /api/checkout` (`AppManager.js:28-78`).
- **Deleção que deixa dados órfãos**: `DELETE /api/users/:id` (`AppManager.js:131-137`) remove o usuário sem tratar `enrollments`/`payments` relacionados — o próprio código documenta isso na resposta ("matrículas e pagamentos ficaram sujos no banco").
- **N+1 queries / callbacks aninhados**: `GET /api/admin/financial-report` (`AppManager.js:80-129`) executa consultas em cascata dentro de `forEach`, com contagem manual de pendências (`coursesPending`/`enrPending`) em vez de `async/await` ou agregação via SQL.
- **Ausência de validação/sanitização de entrada**: `POST /api/checkout` (`AppManager.js:28-35`) só verifica presença de campos, sem validar formato de e-mail, tipo/tamanho de `card`, etc.
