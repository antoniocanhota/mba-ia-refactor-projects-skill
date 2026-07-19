# Referência — Template do Relatório de Auditoria (Fase 2)

Formato padronizado da saída da Fase 2. Preencha com os achados reais; mantenha os
cabeçalhos e a estrutura exatos.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<linhas> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [SEVERITY] <Nome do anti-pattern>
File: <arquivo:linha ou arquivo:início-fim>
Description: <o que foi encontrado, concreto>
Impact: <por que é um problema>
Recommendation: <o que fazer — aponta para a transformação do playbook>

<repita um bloco ### por ocorrência, ordenado por severidade (CRITICAL primeiro)>

================================
Total: <N> findings
================================
```

Depois de imprimir o relatório, a Fase 2 **salva o mesmo conteúdo em um arquivo `.md`**,
perguntando ao usuário o path e o nome do arquivo (default sugerido: `./audit-report.md`
na raiz do projeto analisado; sempre com extensão `.md`). Em seguida **pausa** e pergunta:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

- **Sempre** inclua `arquivo:linha` — sem isso o finding não é acionável.
- Ordene os Findings da maior para a menor severidade.
- O `Total` deve bater com a soma do `## Summary`.
- Uma ocorrência por bloco `###` (não agrupe várias linhas distintas num só finding,
  salvo quando forem literalmente o mesmo trecho contíguo).
