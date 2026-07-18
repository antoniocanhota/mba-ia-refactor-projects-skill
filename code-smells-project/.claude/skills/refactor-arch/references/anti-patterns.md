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

<!--
### [SEVERITY] <próximo anti-pattern>
- **Sinais de detecção:** ...
- **Impacto:** ...
- **Transformação:** ver refactoring-playbook.md → "<nome>".

Incrementos previstos (spec exige ≥8 no total, com deprecated APIs):
CRITICAL — credenciais hardcoded, SQL Injection, God Class, endpoint sem auth.
HIGH     — regra de negócio no controller, estado global mutável, acoplamento sem DI.
MEDIUM   — queries N+1, duplicação de validação, try/except genérico vazando erro.
LOW      — nomenclatura fraca, magic values / config hardcoded.
DEPRECATED — uso de API obsoleta + recomendação do equivalente moderno.
-->
