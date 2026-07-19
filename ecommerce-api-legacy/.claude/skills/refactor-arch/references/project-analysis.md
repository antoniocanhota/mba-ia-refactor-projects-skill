# Referência — Análise de Projeto (Fase 1)

Heurísticas **acionáveis e agnósticas** para caracterizar um projeto antes da auditoria.
Tudo aqui é read-only: ler manifests, extensões e imports; nunca executar código.

## 1. Linguagem

Infira pela combinação de extensões dominantes + arquivo de manifesto:

| Sinal | Linguagem |
|---|---|
| `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py` | Python |
| `*.js`/`*.ts`, `package.json` | JavaScript / TypeScript |
| `*.rb`, `Gemfile` | Ruby |
| `*.go`, `go.mod` | Go |
| `*.java`, `pom.xml`/`build.gradle` | Java |
| `*.php`, `composer.json` | PHP |

Regra: conte as extensões dos arquivos-fonte; a linguagem é a mais frequente,
confirmada pelo manifesto presente.

## 2. Framework (+ versão)

Leia o manifesto de dependências e procure o framework web/aplicação:

- **Python** — `requirements.txt` / `pyproject.toml`: `flask`, `fastapi`, `django`.
  Versão vem da constraint (ex: `Flask==3.1.1`) ou de `pip show`/`import flask; flask.__version__`.
- **Node** — `package.json` → `dependencies`: `express`, `koa`, `next`, `nestjs`.
- Confirme por imports no código-fonte (`from flask import ...`, `require('express')`).

## 3. Dependências relevantes

Liste apenas as que afetam arquitetura/segurança (ex: `flask-cors`, ORMs, drivers
de banco, libs de auth). Ignore utilitários triviais.

## 4. Banco de dados / tabelas

Sinais de detecção:
- Import de driver: `sqlite3`, `psycopg2`, `mysql.connector`, `pymongo`.
- Connection string / arquivo `.db`, `DATABASE_URL`, `get_db()`.
- Tabelas: procure `CREATE TABLE <nome>` e nomes referenciados em queries
  (`FROM <tabela>`, `INSERT INTO <tabela>`).

## 5. Domínio

Infira pelos nomes de rotas, tabelas e entidades (ex: tabelas `produtos`, `pedidos`,
`usuarios` + rotas `/produtos`, `/login` ⇒ *E-commerce API*). Uma frase é suficiente.

## 6. Arquitetura atual

Descreva a organização **como ela é hoje**, não como deveria ser:
- Conte os arquivos-fonte e o total aproximado de linhas.
- Identifique quais camadas MVC existem de fato (há pasta/arquivo separando
  models, views/routes, controllers, config?) e quais estão ausentes ou misturadas.
- Sinais de monolito: toda a lógica (rotas + regras + SQL) concentrada em poucos
  arquivos; ausência de diretórios de camadas.

Exemplo de conclusão: *"Monolítica — rotas em `app.py`, regras e queries misturadas
em `controllers.py`/`models.py`, sem camada de serviço nem de configuração."*

## Saída

Alimente o bloco `PHASE 1: PROJECT ANALYSIS` do `SKILL.md` com o resultado de cada
item acima. Se algum item não se aplicar (ex: projeto sem banco), escreva `n/a`.
