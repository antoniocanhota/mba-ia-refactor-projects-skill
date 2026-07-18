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

<!--
## <próxima transformação>
**Corrige:** [SEVERITY] <anti-pattern>.
**Passos:** ...
**Antes / Depois:** <exemplos de código>
**Validação:** ...

Incrementos previstos (spec exige ≥8 transformações): extrair SQL para models
parametrizados, extrair config/segredos para settings, quebrar God Class por domínio,
extrair regra de negócio do controller para serviço, injeção de dependência da
conexão, corrigir N+1 com JOIN, error-handler middleware, substituir API deprecated.
-->
