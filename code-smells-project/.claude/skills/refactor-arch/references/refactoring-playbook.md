# Referência — Playbook de Refatoração (Fase 3)

Transformações concretas, uma por anti-pattern do catálogo, com exemplo
**antes/depois**. A Fase 3 aplica a transformação correspondente a cada achado
confirmado, preservando o comportamento observável.

<!-- Formato para novas entradas: replicar o bloco abaixo, casando o nome com o do catálogo. -->

---

## print() → logging

**Corrige:** `[LOW] print() como mecanismo de logging`.

**Objetivo:** substituir `print()` de diagnóstico por logging estruturado com níveis,
sem perder a informação registrada.

**Passos:**
1. Configurar logging uma vez, no ponto de entrada da aplicação.
2. Em cada módulo, obter um logger: `logger = logging.getLogger(__name__)`.
3. Trocar cada `print` de log pelo nível adequado: `logger.info` para eventos de
   sucesso/fluxo, `logger.warning` para condições anômalas, `logger.error` (ou
   `logger.exception` dentro de `except`) para falhas.
4. Usar argumentos lazy (`%s`) em vez de concatenar strings.
5. Preservar banners/UX de CLI legítimos, se houver (não são log de runtime).

**Antes** (`controllers.py`):
```python
def criar_produto():
    try:
        ...
        id = models.criar_produto(nome, descricao, preco, estoque, categoria)
        print("Produto criado com ID: " + str(id))
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201
    except Exception as e:
        print("ERRO ao criar produto: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

**Depois** (`controllers.py`):
```python
import logging

logger = logging.getLogger(__name__)

def criar_produto():
    try:
        ...
        id = models.criar_produto(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", id)
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201
    except Exception as e:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": str(e)}), 500
```

**Configuração central** (ponto de entrada, ex: `app.py`):
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
```

**Equivalentes por stack:** Node → `console.log/error` para uma lib como `pino`/`winston`;
Java → `System.out.println` para SLF4J/Logback; Go → `fmt.Println` para `log`/`slog`.

**Validação:** `grep -n "print(" <arquivos>` não deve retornar chamadas de logging;
a aplicação sobe e os endpoints seguem respondendo.

---

## God Class → separação em camadas

**Corrige:** `[CRITICAL] God Class / God Module`.

**Objetivo:** quebrar o arquivo/classe monolítico nas camadas da estrutura-alvo
(`architecture-guidelines.md`), sem alterar o comportamento observável (mesmos endpoints,
mesmas respostas). **Adapte ao contexto:** monolito → separar em camadas; achado isolado
não justifica uma nova árvore de diretórios.

**Passos:**
1. Mapear cada responsabilidade da God Class: conexão, schema/seed, rotas, controller,
   regra de negócio, acesso a dados.
2. Extrair o acesso a dados para **models** (um módulo por domínio), com queries
   parametrizadas.
3. Extrair a regra de negócio para **serviços/use-cases**; deixar o **controller** só
   orquestrando (validar → chamar serviço → montar resposta).
4. Mover a definição de rotas para **views/routes**; mover conexão/schema/seed para
   **config** + inicialização.
5. Transformar o arquivo original num **composition root** (`app.py`/`index.js`) que monta
   as camadas e sobe o servidor.

**Antes** (`AppManager.js` — tudo numa classe):
```js
class AppManager {
  constructor() {
    this.db = new sqlite3.Database(":memory:");
    this.db.run("CREATE TABLE users (...)");           // schema
    this.app.post("/api/checkout", (req, res) => {      // rota + controller
      const total = req.body.qty * 100 * 1.1;           // regra de negócio
      this.db.run("INSERT INTO payments ...");          // acesso a dados
    });
  }
}
```

**Depois** (camadas separadas):
```js
// models/paymentModel.js
export function createPayment(db, order) { return db.run("INSERT INTO payments ...", order); }

// services/checkoutService.js
export function checkout(models, input) {
  const total = models.pricing.totalFor(input);         // regra de negócio isolada
  return models.payment.create(input.with(total));
}

// routes/checkout.js
router.post("/api/checkout", (req, res) => res.json(checkoutService.checkout(models, req.body)));

// app.js — composition root: monta db, models, services, routes e sobe o servidor
```

**Equivalentes por stack:** Java → separar `@Controller`/`@Service`/`@Repository`; Python →
`controllers/`, `services/`, `models/`, `config/`; Go → pacotes `handler`, `service`, `store`.

**Validação:** cada arquivo tem uma responsabilidade; a app sobe e os endpoints originais
respondem igual; nenhum arquivo mistura schema + rota + SQL.

---

## DTO/serializer para a resposta

**Corrige:** `[CRITICAL] Dados sensíveis serializados direto na resposta`.

**Objetivo:** interpor uma fronteira Model↔View que expõe apenas campos públicos, nunca
credenciais/hashes.

**Passos:**
1. Definir a **allowlist** de campos públicos da entidade (o que a API pode expor).
2. Criar um serializer/DTO que projeta só esses campos (`public_dict()`), separado de qualquer
   `to_dict()` interno que contenha senha/hash.
3. Trocar as rotas para serializar via o DTO, nunca a entidade crua nem `SELECT *`.
4. Garantir que campos `senha`/`password`/`token` nunca entrem na projeção pública.

**Antes** (`models/user.py` + rota):
```python
class User:
    def to_dict(self):
        return {"id": self.id, "email": self.email, "password": self.password}  # vaza hash

# rota
return jsonify(user.to_dict())
```

**Depois:**
```python
class User:
    PUBLIC_FIELDS = ("id", "email", "role")
    def public_dict(self):
        return {f: getattr(self, f) for f in self.PUBLIC_FIELDS}  # sem password

# rota
return jsonify(user.public_dict())
```

**Equivalentes por stack:** Node → função `toPublic(row)` / `pick(row, [...])`; Java → um
`UserResponseDTO` em vez de serializar a entidade JPA; usar `@JsonIgnore` no campo sensível.

**Validação:** `grep -rniE "senha|password|pass|token" <respostas/serializers>` não retorna
campo sensível na saída pública; os endpoints seguem devolvendo os campos legítimos.

---

## Extrair regra para camada de serviço

**Corrige:** `[HIGH] Regra de negócio presa no controller`.

**Objetivo:** mover regra de negócio e orquestração para um serviço/use-case reutilizável e
testável; o controller só valida entrada, delega e monta a resposta.

**Passos:**
1. Identificar no controller os trechos de regra de negócio (cálculos, decisões de domínio,
   múltiplos passos) e persistência.
2. Criar/usar um módulo de **serviço** que recebe os dados já validados e executa a regra,
   chamando os models.
3. Reduzir o controller a: validar shape da entrada → chamar o serviço → montar response.
4. Se já existe uma camada `services/` órfã, **passar a usá-la** em vez de reimplementar.

**Antes** (`controllers.py`):
```python
def criar_pedido():
    ...  # validação inline
    total = sum(i["preco"] * i["qtd"] for i in itens)      # regra de negócio
    if total > 500: total *= 0.9                            # desconto no controller
    id = db.execute("INSERT INTO pedidos ...")             # persistência
    return jsonify({"id": id, "total": total})
```

**Depois:**
```python
# services/pedido_service.py
def criar_pedido(models, itens):
    total = calcular_total_com_desconto(itens)             # regra isolada e testável
    return models.pedido.criar(itens, total)

# controllers.py
def criar_pedido():
    dados = validar_pedido(request.json)                   # só orquestra
    pedido = pedido_service.criar_pedido(models, dados)
    return jsonify(pedido.public_dict()), 201
```

**Equivalentes por stack:** Node → extrair de `route` handler para `checkoutService`; Java →
mover do `@Controller` para um `@Service`.

**Validação:** controllers sem SQL/regra pesada; a regra de negócio tem teste unitário sem
subir HTTP; endpoints respondem igual.

---

## Injeção de dependência / composition root

**Corrige:** `[HIGH] Ausência de injeção de dependência / estado global mutável`.

**Objetivo:** receber conexões/serviços por parâmetro (montados num composition root) e
eliminar estado global mutável compartilhado entre requisições.

**Passos:**
1. Parar de instanciar a conexão no construtor / como global; passá-la como argumento.
2. Montar as dependências uma vez no **composition root** (`app.py`/`index.js`) e injetá-las
   nas camadas.
3. Substituir estado global mutável (`globalCache`, `totalRevenue`) por estado com escopo de
   requisição ou por um store injetado.
4. Expor um seam para testes (poder passar um fake/mock da dependência).

**Antes** (`AppManager.js` / `utils.js`):
```js
// utils.js
export let globalCache = {};        // estado global mutável entre requisições
export let totalRevenue = 0;

class AppManager {
  constructor() { this.db = new sqlite3.Database(":memory:"); }  // dependência acoplada
}
```

**Depois:**
```js
// app.js — composition root
const db = new sqlite3.Database(process.env.DB_URL);
const manager = new AppManager({ db });            // injeção por parâmetro

// AppManager.js
class AppManager {
  constructor({ db }) { this.db = db; }            // recebe, não instancia
}
// cache com escopo de request/serviço, não módulo global
```

**Equivalentes por stack:** Python → passar `conn`/repositórios ao serviço em vez de global
`get_db()`; Java → `@Autowired`/constructor injection em vez de `static` mutável.

**Validação:** nenhuma conexão instanciada em construtor/global; nenhum estado mutável
exportado de módulo; as camadas aceitam um dublê nos testes.

---

## Extrair / reusar lógica duplicada

**Corrige:** `[MEDIUM] Duplicação de código / lógica reimplementada`.

**Objetivo:** ter uma única fonte de verdade para cada validação/regra, reusando o que já
existe em vez de reimplementar.

**Passos:**
1. Localizar os blocos idênticos (validação copiada entre create/update; cálculo repetido em
   N rotas) e os métodos/constantes já existentes mas não usados.
2. Extrair a lógica duplicada para **uma** função reutilizável (ou passar a chamar o método
   já pronto no model/helper).
3. Substituir todas as cópias pela chamada única.
4. Remover o código morto correlato (método definido e nunca usado depois de reintegrado).

**Antes** (`routes/task_routes.py` — `is_overdue()` existe mas é ignorado):
```python
# repetido em 5 rotas:
overdue = task.due_date is not None and task.due_date < datetime.now() and task.status != "done"
```

**Depois:**
```python
# models/task.py (já existia)
def is_overdue(self): ...

# nas rotas:
overdue = task.is_overdue()   # fonte única
```

**Equivalentes por stack:** Node → extrair para `validators.js` reutilizado; Java → mover para
um método de domínio/`@Service` único.

**Validação:** a lógica aparece em um só lugar; métodos antes órfãos agora são usados; nenhum
bloco duplicado remanescente.

---

## Validar entrada na borda da rota

**Corrige:** `[MEDIUM] Validação de entrada ausente nas rotas`.

**Objetivo:** validar presença/tipo/formato da entrada antes de usá-la, retornando **400**
acionável em vez de deixar estourar 500.

**Passos:**
1. Na borda da rota/controller, checar campos obrigatórios, tipos e formato antes de qualquer
   query/cálculo/persistência.
2. Converter com segurança (ex: parse numérico com tratamento) e responder 400 com mensagem
   clara quando inválido.
3. Centralizar validações comuns num validador reutilizável (casa com o item de DRY acima).

**Antes** (`routes/task_routes.py`):
```python
def search_tasks():
    priority = int(request.args.get("priority"))   # ValueError → 500 não tratado
    user_id = int(request.args.get("user_id"))
    ...
```

**Depois:**
```python
def search_tasks():
    priority, err = parse_int(request.args.get("priority"))
    if err:
        return jsonify({"erro": "priority deve ser inteiro"}), 400
    ...
```

**Equivalentes por stack:** Node → validar `req.body`/`req.query` (ex: `zod`/`joi`) e retornar
400; Java → `@Valid` + `@RequestParam` tipado com handler de `MethodArgumentNotValidException`.

**Validação:** entrada inválida retorna 400 (não 500); nenhum `int(...)`/conversão crua sem
tratamento no caminho da requisição; entrada válida segue funcionando.
