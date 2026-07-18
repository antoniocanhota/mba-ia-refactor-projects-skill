# Referência — Catálogo de Anti-Patterns (Fase 2)

Cada entrada tem: **sinais de detecção** acionáveis (o que procurar no código),
**severidade** e **impacto**. A Fase 2 cruza cada anti-pattern contra a codebase e
registra ocorrências com `arquivo:linha`.

## Escala de severidade

- **CRITICAL** — falhas graves de arquitetura/segurança; impedem o funcionamento
  correto, expõem dados sensíveis (credenciais hardcoded, SQL Injection) ou violam
  totalmente a separação de responsabilidades (God Class).
- **HIGH** — fortes violações de MVC/SOLID que dificultam muito manutenção e testes
  (regra de negócio presa em controllers, acoplamento sem injeção de dependência,
  estado global mutável).
- **MEDIUM** — padronização, duplicação ou performance moderada (queries N+1, uso
  inadequado de middlewares, validações ausentes).
- **LOW** — legibilidade, nomenclatura ruim, magic numbers soltos.

---

## Catálogo

<!-- Formato para novas entradas: replicar o bloco abaixo. Manter agrupado por severidade. -->

### [CRITICAL] God Class / God Module

- **Sinais de detecção:**
  - Um único arquivo/classe concentra responsabilidades de camadas distintas ao mesmo
    tempo: **abertura de conexão** de banco, **definição de schema** (`CREATE TABLE`),
    **seed** de dados, **roteamento** (registro de rotas/endpoints), **controller**
    (tratamento de request/response), **regra de negócio** e **acesso a dados** (queries).
  - Sintomas mensuráveis: arquivo com centenas de linhas fazendo "tudo"; nome genérico
    como `AppManager`, `Main`, `Manager`, `Helper`, `App`; construtor que instancia
    banco e já registra rotas.
  - Equivalentes por stack: uma classe Node/Express que faz `new sqlite3()`, `app.get(...)`
    e o SQL no mesmo lugar; um `@RestController` Java com JDBC e `CREATE TABLE` embutidos;
    um único `main.go` com `http.HandleFunc` + queries.
- **Impacto:** viola completamente SRP e o padrão MVC — o arquivo tem N razões para mudar,
  é impossível testar unidades isoladas, e qualquer alteração arrisca efeitos colaterais
  em responsabilidades não relacionadas.
- **Não é ocorrência:** um `app.py`/`main` que atua só como **composition root** (monta
  camadas já separadas e sobe o servidor) é legítimo — o problema é acumular a lógica das
  camadas, não orquestrar a inicialização.
- **Transformação:** ver `refactoring-playbook.md` → "God Class → separação em camadas".

### [CRITICAL] Dados sensíveis serializados direto na resposta

- **Sinais de detecção:**
  - Entidade do model devolvida crua na API incluindo campos sensíveis — campo
    `senha`/`password`/`pass`/`token`/`secret` presente no dict/JSON de resposta.
  - `to_dict()`/serializer da entidade que inclui o hash/senha e é usado direto pela rota
    (ex: `return jsonify(user.to_dict())` onde `to_dict` contém `password`).
  - Listagens/detalhes que fazem `SELECT *` e repassam todas as colunas ao cliente.
  - Equivalentes por stack: `res.json(userRow)` em Node com a coluna `pass`; `return user;`
    num controller Java serializando a entidade JPA inteira.
- **Impacto:** expõe dados sensíveis a qualquer consumidor da API (vazamento de credenciais/
  hashes), e acopla a camada de apresentação ao formato interno do model — sem uma fronteira
  Model↔View (DTO/serializer), toda mudança de schema vaza para a resposta pública.
- **Não é ocorrência:** endpoint estritamente interno/administrativo **já protegido por
  autenticação** e destinado a uso operacional pode expor mais campos — avalie o contexto e
  reporte com ressalva.
- **Transformação:** ver `refactoring-playbook.md` → "DTO/serializer para a resposta".

### [HIGH] Regra de negócio presa no controller

- **Sinais de detecção:**
  - Handlers de rota/controller que concentram validação de entrada, regra de negócio
    (cálculos, decisões de domínio, orquestração de múltiplos passos) e persistência no
    mesmo corpo de função.
  - Ausência de camada de serviço/use-case: nenhum `services/`, `usecases/` ou equivalente
    é chamado — ou ela **existe mas está órfã** (definida e nunca instanciada/invocada).
  - Sintomas: controllers longos com SQL/queries diretos, `if` de regra de negócio
    misturado a montagem de response, blocos de validação inline repetidos.
  - Equivalentes por stack: `route.post(...)` Express com toda a lógica no callback; método
    de `@Controller` Java com regra de negócio e chamadas ao repositório inline.
- **Impacto:** viola MVC/SRP — o controller passa a ter múltiplas razões para mudar,
  a regra de negócio não é reutilizável nem testável fora do ciclo HTTP, e a manutenção
  fica arriscada.
- **Não é ocorrência:** controller que apenas valida o shape da entrada, delega a um
  serviço e monta a resposta está correto — orquestração leve é papel do controller.
- **Transformação:** ver `refactoring-playbook.md` → "extrair regra para camada de serviço".

### [HIGH] Ausência de injeção de dependência / estado global mutável

- **Sinais de detecção:**
  - Conexão de banco (ou cliente HTTP, cache, etc.) instanciada **dentro do construtor** da
    classe ou como **variável global/de módulo mutável**, em vez de recebida por parâmetro.
  - Estado compartilhado entre requisições exportado do módulo (ex: `globalCache = {}`,
    `totalRevenue = 0`, singleton manual de conexão).
  - Código que referencia a dependência por um símbolo global fixo, impossível de substituir
    em teste (sem seam para mock/fake).
  - Equivalentes por stack: `this.db = new sqlite3(...)` no construtor (Node); `static`
    mutável compartilhado (Java); variável de pacote global (Go).
- **Impacto:** viola o princípio de inversão de dependência (DIP) — forte acoplamento à
  implementação concreta, impossibilidade de testar com dublês, e estado global mutável
  gera condições de corrida e vazamento de dados entre requisições.
- **Não é ocorrência:** constantes imutáveis de configuração e clientes verdadeiramente
  stateless podem ser de módulo — o problema é dependência concreta acoplada **ou** estado
  mutável compartilhado.
- **Transformação:** ver `refactoring-playbook.md` → "injeção de dependência / composition root".

### [MEDIUM] Duplicação de código / lógica reimplementada

- **Sinais de detecção:**
  - Blocos de validação ou de montagem de dados praticamente idênticos copiados entre
    funções (ex: mesma validação em `criar_*` e `atualizar_*`).
  - Regra reimplementada inline em vários lugares apesar de já existir um método pronto no
    model/helper (ex: cálculo de "atrasado" repetido nas rotas enquanto `Task.is_overdue()`
    existe e nunca é chamado; `validate_status()`/`VALID_STATUSES` definidos mas ignorados).
  - Código morto correlato: método/constante utilitária definido e nunca referenciado,
    enquanto sua lógica aparece duplicada à mão.
  - Equivalentes por stack: mesma checagem repetida em vários `route` handlers (Node); lógica
    duplicada entre métodos de service (Java).
- **Impacto:** viola DRY — correções precisam ser aplicadas em N lugares, divergências
  silenciosas surgem entre as cópias, e a existência de métodos não usados engana quem lê.
- **Não é ocorrência:** trechos superficialmente parecidos mas com regras genuinamente
  distintas não são duplicação — não force uma abstração que acople o que deveria variar.
- **Transformação:** ver `refactoring-playbook.md` → "extrair/reusar lógica duplicada".

### [MEDIUM] Validação de entrada ausente nas rotas

- **Sinais de detecção:**
  - Dados vindos do request (body/params/query) usados direto em query, cálculo ou
    persistência **sem checagem prévia** de presença, tipo ou formato.
  - Conversões sem tratamento que estouram 500 para entrada inválida (ex: `int(user_id)` /
    `int(priority)` sem `try`/validação → `ValueError` não tratado).
  - Campos obrigatórios não verificados; ids/números aceitos como string arbitrária; formato
    (e-mail, cartão, datas) nunca validado antes do uso.
  - Equivalentes por stack: `req.body.x` usado sem validar (Node); `@RequestParam` consumido
    sem `@Valid`/checagem (Java).
- **Impacto:** entrada inválida vira erro 500 (vazando stack/detalhes internos) em vez de 400
  acionável; abre espaço para dados corrompidos persistidos e comportamento imprevisível.
- **Não é ocorrência:** rota que só repassa um valor opaco sem interpretá-lo/persistí-lo, ou
  entrada já validada por um middleware/esquema anterior na cadeia.
- **Transformação:** ver `refactoring-playbook.md` → "validar entrada na borda da rota".

### [LOW] print() como mecanismo de logging

- **Sinais de detecção:**
  - Chamadas `print(...)` que registram eventos de runtime, sucesso ou **erro**
    dentro de handlers/serviços (ex: `print("ERRO ao criar produto: " + str(e))`,
    `print("Produto criado com ID: " + str(id))`).
  - Uso em blocos `except` para reportar falhas.
  - Equivalentes em outras stacks: `console.log`/`console.error` (Node),
    `System.out.println` (Java), `fmt.Println` para log (Go), `puts` (Ruby).
- **Impacto:** logs não têm nível, timestamp, nem destino configurável; impossível
  silenciar, rotear ou filtrar em produção; polui stdout e mistura diagnóstico com
  saída da aplicação.
- **Não é ocorrência:** banners de inicialização de CLI e mensagens de UX de linha
  de comando podem ser `print` legítimo — avalie o contexto e reporte com ressalva.
- **Transformação:** ver `refactoring-playbook.md` → "print() → logging".
