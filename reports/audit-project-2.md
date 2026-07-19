================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy (Frankenstein LMS)
Stack:   JavaScript (Node.js) + Express ^4.18.2 + sqlite3 ^5.1.6
Files:   3 analyzed | ~166 lines of code

## Summary
CRITICAL: 1 | HIGH: 4 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] God Class / God Module
File: src/AppManager.js:4-141
Description: A classe `AppManager` concentra, no mesmo arquivo/classe: abertura de conexão do banco (`this.db = new sqlite3.Database(':memory:')`, linha 7), definição de schema via `CREATE TABLE` (linhas 12-16), seed de dados (linhas 18-21), roteamento (`app.post`/`app.get`/`app.delete`, linhas 28, 80, 131), tratamento de request/response, regra de negócio (ex: decisão de status de pagamento) e acesso a dados (SQL cru embutido nos handlers).
Impact: Viola completamente SRP e o padrão MVC — a classe tem múltiplas razões para mudar, é impossível testar isoladamente regra de negócio, acesso a dados ou schema, e qualquer alteração local arrisca efeitos colaterais em responsabilidades não relacionadas.
Recommendation: Separar em camadas — `playbook: God Class → separação em camadas` (routes/controllers, services, repositories, config de banco/schema em módulos próprios).

### [HIGH] Regra de negócio presa no controller (checkout)
File: src/AppManager.js:28-78
Description: O handler `POST /api/checkout` mistura validação de entrada (linha 35), lógica de negócio (decisão de aprovação/recusa de pagamento por prefixo do cartão, linha 46; geração de hash de senha, linha 68) e persistência (inserts encadeados em `users`, `enrollments`, `payments`, `audit_logs`) no mesmo callback aninhado. Não existe camada de serviço/use-case.
Impact: A regra de checkout não é reutilizável nem testável fora do ciclo HTTP; qualquer mudança de regra de negócio exige tocar diretamente no controller e arrisca quebrar a orquestração de request/response.
Recommendation: Extrair para uma camada de serviço (`CheckoutService`) — `playbook: Extrair regra para camada de serviço`.

### [HIGH] Regra de negócio presa no controller (relatório financeiro)
File: src/AppManager.js:80-129
Description: O handler `GET /api/admin/financial-report` combina orquestração manual de múltiplas queries aninhadas (cursos → matrículas → usuários → pagamentos) com regra de negócio (acumular receita por curso, linhas 108-109) e controle de fluxo assíncrono via contadores manuais (`coursesPending`, `enrPending`), tudo dentro do controller.
Impact: Lógica de agregação financeira não é reutilizável nem testável isoladamente; o controle manual de callbacks aninhados é frágil e difícil de manter (risco de condição de corrida/erro silencioso ao adicionar novos passos).
Recommendation: Extrair para uma camada de serviço/repositório com queries mais diretas (ex: JOIN ou `Promise.all`) — `playbook: Extrair regra para camada de serviço`.

### [HIGH] Ausência de injeção de dependência (conexão de banco no construtor)
File: src/AppManager.js:7
Description: `this.db = new sqlite3.Database(':memory:')` é instanciado diretamente dentro do construtor de `AppManager`, em vez de recebido por parâmetro/injeção.
Impact: Acoplamento forte à implementação concreta do driver SQLite — impossível substituir por um dublê/mocks em teste, e qualquer troca de banco exige alterar a classe.
Recommendation: Injetar a conexão via construtor a partir de um composition root — `playbook: Injeção de dependência / composition root`.

### [HIGH] Estado global mutável
File: src/utils.js:9-10,14
Description: `globalCache = {}` e `totalRevenue = 0` (linhas 9-10) são variáveis de módulo mutáveis, compartilhadas entre todas as requisições; `logAndCache` (linha 14) escreve nesse objeto global a cada checkout (`AppManager.js:59`).
Impact: Estado compartilhado entre requisições concorrentes gera condições de corrida e vazamento de dados entre usuários (o cache de "último checkout" de um usuário pode ser sobrescrito/lido por outra requisição concorrente); impossível isolar em testes.
Recommendation: Substituir por uma dependência injetada (cache real com escopo por requisição/usuário) — `playbook: Injeção de dependência / composition root`.

### [MEDIUM] Código morto correlato a lógica reimplementada (`totalRevenue`)
File: src/utils.js:10,25
Description: `totalRevenue` é definida e exportada (linhas 10 e 25) mas nunca é referenciada em nenhum lugar do código; o relatório financeiro (`AppManager.js:108-109`) reimplementa o acúmulo de receita manualmente por curso, ignorando por completo essa variável utilitária.
Impact: A existência de uma variável utilitária não usada engana quem lê o código (parece ser a fonte de verdade para receita total, mas não é) e mascara que a lógica de soma de receita foi duplicada/reimplementada ad-hoc no controller.
Recommendation: Remover a variável morta ou centralizar o cálculo de receita nela via um serviço dedicado — `playbook: Extrair / reusar lógica duplicada`.

### [MEDIUM] Tratamento de erro espalhado / sem middleware central
File: src/app.js:1-15, src/AppManager.js:41,51,55,70,84
Description: `app.js` não registra nenhum middleware de erro (`app.use((err, req, res, next) => ...)`). Cada handler de `AppManager.js` repete manualmente o mesmo padrão `if (err) return res.status(500).send("Erro ...")` (linhas 41, 51, 55, 70, 84), cada um com uma mensagem de texto solto e sem estrutura (não é JSON, não distingue tipos de erro).
Impact: Boilerplate de erro duplicado em cada handler (viola DRY), respostas de erro inconsistentes entre endpoints (texto puro vs. o restante da API que usa JSON), e ausência de um ponto único dificulta padronizar logging/monitoramento de falhas.
Recommendation: Centralizar em um middleware de erro do Express — `playbook: Error handler centralizado / middleware`.

### [MEDIUM] Erros de callback silenciosamente ignorados
File: src/AppManager.js:92,104,106
Description: Nos callbacks de `this.db.all("SELECT * FROM enrollments...", ...)` (linha 92) e `this.db.get(...)` (linhas 104 e 106) dentro do relatório financeiro, o parâmetro `err` é recebido mas nunca verificado — se a query falhar, o código segue tentando usar `enrollments`/`user`/`payment` possivelmente indefinidos.
Impact: Falha de banco nesses pontos não é tratada nem reportada ao cliente — o handler pode travar (nunca responder, pois os contadores `enrPending`/`coursesPending` não decrementam) ou lançar exceção não capturada, gerando um erro 500 genérico do Express sem diagnóstico.
Recommendation: Tratar cada `err` explicitamente dentro do handler de erro central — `playbook: Error handler centralizado / middleware`.

### [LOW] print() como logging (vaza segredo de pagamento e dado de cartão)
File: src/AppManager.js:45
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` registra, via `console.log`, tanto o número completo do cartão informado pelo cliente quanto a chave secreta do gateway de pagamento (`config.paymentGatewayKey`, hardcoded em `utils.js:4`).
Impact: Além de não ter nível/timestamp/destino configurável (log não roteável/filtrável em produção), esse `console.log` específico grava dado sensível de cartão e uma credencial de produção em texto plano no stdout/logs.
Recommendation: Substituir por logger estruturado com mascaramento de dados sensíveis — `playbook: print() → logging`.

### [LOW] print() como logging
File: src/utils.js:13
Description: `console.log(`[LOG] Salvando no cache: ${key}`)` dentro de `logAndCache` registra um evento de runtime via `console.log`, sem nível, timestamp estruturado ou destino configurável.
Impact: Impossível silenciar, rotear ou filtrar esse log em produção; mistura diagnóstico com saída padrão da aplicação.
Recommendation: Substituir por logger estruturado — `playbook: print() → logging`.

### [LOW] Nomenclatura fraca de variáveis
File: src/AppManager.js:29-33
Description: No handler de checkout, os campos do corpo da requisição são atribuídos a identificadores de uma/duas letras sem significado próprio: `u` (nome do usuário), `e` (email), `p` (senha), `cid` (id do curso), `cc` (número do cartão).
Impact: Reduz a legibilidade — quem lê precisa reconstruir o papel de cada variável pelo uso posterior (`u`, `e`, `p`, `cid`, `cc` não comunicam intenção), aumentando o custo de manutenção e o risco de troca acidental entre variáveis parecidas.
Recommendation: Renomear para nomes intencionais (`username`, `email`, `password`, `courseId`, `cardNumber`) — `playbook: Renomear para nomes intencionais`.

================================
Total: 11 findings
================================
