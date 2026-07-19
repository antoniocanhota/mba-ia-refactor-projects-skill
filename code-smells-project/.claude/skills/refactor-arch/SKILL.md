---
name: refactor-arch
description: >-
  Analisa, audita e refatora projetos legados rumo ao padrão MVC, de forma
  agnóstica de tecnologia. Use quando o usuário pedir para refatorar a
  arquitetura, encontrar code smells / anti-patterns, gerar um relatório de
  auditoria de arquitetura, ou modernizar um projeto legado. Detecta a stack,
  classifica achados por severidade (CRITICAL/HIGH/MEDIUM/LOW) com arquivo e
  linha exatos, pede confirmação humana antes de modificar, aplica as
  transformações e valida que a aplicação continua funcionando.
---

# refactor-arch

Skill de refatoração arquitetural em **3 fases sequenciais**: Análise → Auditoria →
Refatoração. Funciona em qualquer linguagem/framework. O `SKILL.md` orquestra o
fluxo; o conhecimento de domínio vive em `references/` e é lido **sob demanda**.

> Estado atual: o catálogo cobre **8 anti-patterns** — 2 CRITICAL (God Class;
> dados sensíveis na resposta), 2 HIGH (regra de negócio no controller; ausência de
> injeção de dependência / estado global mutável), 2 MEDIUM (duplicação de código;
> validação de entrada ausente nas rotas) e 2 LOW (`print()` como logging;
> nomenclatura fraca de variáveis). A estrutura foi desenhada para crescer — novos
> anti-patterns entram em `references/anti-patterns.md` e
> `references/refactoring-playbook.md` sem alterar este fluxo.

## Como executar

Rode as 3 fases em ordem. **Nunca modifique arquivos antes da confirmação na Fase 2.**
Cada bloco de saída deve seguir o formato definido nas referências.

---

## Phase 1 — Project Analysis

Objetivo: entender o projeto antes de julgá-lo. **Read-only.**

1. Leia `references/project-analysis.md` e aplique as heurísticas para detectar:
   linguagem, framework (+ versão), dependências relevantes, domínio, arquitetura
   atual e banco de dados / tabelas.
2. Mapeie os arquivos-fonte (quantidade, camadas presentes/ausentes).
3. Imprima o resumo neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Domain:        <domínio inferido>
Architecture:  <descrição da organização atual>
Source files:  <N> files analyzed
DB tables:     <tabelas, se houver>
================================
```

Não peça confirmação aqui; siga direto para a Fase 2.

---

## Phase 2 — Architecture Audit

Objetivo: cruzar o código contra o catálogo e produzir um relatório revisável.
Ainda **read-only**.

1. Leia `references/anti-patterns.md` (catálogo) e `references/report-template.md`
   (formato de saída).
2. Para cada anti-pattern do catálogo, procure seus **sinais de detecção** no código.
   Registre cada ocorrência com `arquivo:linha` exatos.
3. Classifique por severidade conforme a escala do catálogo.
4. Gere o **ARCHITECTURE AUDIT REPORT** seguindo `references/report-template.md`
   (Summary por severidade + Findings + Total).
5. **Salve o relatório em um arquivo Markdown.** Pergunte ao usuário o **path** e o
   **nome do arquivo** (ex: `Onde salvo o relatório? (path e nome do arquivo .md)`).
   Aplique um default sensato se ele não informar (ex: `./audit-report.md` na raiz do
   projeto analisado) e garanta a extensão `.md`. Escreva o mesmo conteúdo do relatório
   impresso no arquivo e confirme o caminho salvo. Isso é gravação de um relatório novo
   — não conta como "modificar arquivos do projeto"; a regra da Fase 2 continua valendo
   para o código-fonte.
6. **PARE e peça confirmação explícita antes de modificar qualquer arquivo:**

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Só avance para a Fase 3 se a resposta for afirmativa. Se for `n`, encerre sem
alterar nada.

---

## Phase 3 — Refactoring

Objetivo: eliminar os achados confirmados e **validar** que a app continua funcionando.
Só executa após o `y` da Fase 2.

1. Leia `references/architecture-guidelines.md` (regras do padrão MVC alvo) e
   `references/refactoring-playbook.md` (transformações antes/depois).
2. Para cada anti-pattern confirmado, aplique a transformação correspondente do
   playbook. **Adapte-se ao contexto**: um monolito exige restruturação em camadas;
   um projeto já parcialmente organizado exige apenas correções pontuais. Não force
   estrutura que o escopo dos achados não justifica.
3. Preserve o comportamento observável (mesmos endpoints, mesmas respostas). **Nunca
   remova um endpoint ou funcionalidade como forma de corrigir um achado — nem mesmo
   um achado CRITICAL.** Se um endpoint é perigoso (ex: execução de SQL arbitrário,
   ausência de autenticação), a transformação é **proteger** (autenticação/autorização,
   validação, sandboxing), não apagar. Se genuinamente não houver transformação segura
   que preserve o endpoint, **pare e pergunte ao usuário** em vez de decidir remover.
4. **Valide o resultado** (não-destrutivo):
   - A aplicação inicializa sem erros (boot).
   - Os endpoints principais respondem corretamente.
   - Zero ocorrências remanescentes dos anti-patterns corrigidos.
5. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## Changes Applied
<lista das transformações aplicadas>

## Validation
  ✓ Application boots without errors
  ✓ Endpoints respond correctly
  ✓ Zero remaining occurrences of fixed anti-patterns
================================
```

---

## Regras operacionais

- **Confirmação humana obrigatória** entre Fase 2 e Fase 3. Sem `y`, nada muda.
- **Nunca remova funcionalidade.** A Fase 3 corrige anti-patterns, não decide o que a
  API deve ou não expor. Endpoints/rotas originais continuam existindo e respondendo
  após a refatoração — mesmo os que a auditoria classificou como CRITICAL. A correção
  de um endpoint perigoso é protegê-lo (autenticação, validação de entrada, queries
  parametrizadas), nunca eliminá-lo. Dúvida sobre como proteger sem quebrar o
  comportamento → parar e perguntar ao usuário, não decidir sozinho.
- **Sinais de detecção específicos** — reporte "chamada `print()` registrando evento
  de runtime em `controllers.py:57`", nunca "código ruim".
- **Agnóstica de tecnologia** — as heurísticas e o catálogo descrevem sinais, não
  uma stack fixa. Adapte a nomenclatura de camadas ao ecossistema detectado.
- **Portátil** — não dependa de nada específico deste repositório; a skill deve
  funcionar copiada para outro projeto.
