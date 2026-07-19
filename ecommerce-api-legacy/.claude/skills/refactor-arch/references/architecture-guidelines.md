# Referência — Guidelines de Arquitetura (padrão MVC alvo)

Regras do alvo para o qual a Fase 3 refatora. São **instruções afirmativas**: dizem
qual padrão seguir. Adapte a nomenclatura ao ecossistema (ex: em Django, "views"
fazem papel de controllers; em Express, "routes" + "controllers").

## Camadas e responsabilidades

| Camada | Responsabilidade | NÃO deve conter |
|---|---|---|
| **Config** | Configuração e constantes centralizadas (chaves, flags, listas de valores válidos), lidas de ambiente. | Segredos hardcoded, lógica. |
| **Models** | Acesso a dados e representação de entidades; queries parametrizadas. | Regra de negócio, roteamento, formatação de resposta. |
| **Views / Routes** | Definição de rotas e mapeamento HTTP → controller; serialização de entrada/saída. | Regra de negócio, SQL. |
| **Controllers** | Orquestração da requisição: validar entrada, chamar model/serviço, montar resposta. | SQL direto, regra de negócio pesada (extrair para serviço/use case). |
| **Middlewares** | Preocupações transversais: tratamento de erro, autenticação, logging. | Regra de domínio. |

## Estrutura alvo (referência, adaptar por stack)

```
src/
├── config/settings.py          # configuração + constantes
├── models/                     # um módulo por domínio
├── views/routes.py             # definição de rotas
├── controllers/                # um módulo por domínio
├── middlewares/error_handler.py
└── app.py                      # composition root (monta tudo)
```

## Princípios

- **Separação de responsabilidades (SRP):** cada arquivo tem uma razão para mudar.
- **Injeção de dependência:** conexões/serviços recebidos, não globais mutáveis.
- **Sem segredos no código:** configuração vem do ambiente.
- **Queries parametrizadas:** nunca concatenar entrada em SQL.
- **Logging estruturado:** via biblioteca de logging com níveis, não `print`.

## Regra de adaptação ao contexto

O grau de restruturação depende dos achados da auditoria, não de um molde fixo:
- **Monolito** (tudo misturado) → separar em camadas conforme a estrutura acima.
- **Projeto parcialmente organizado** → apenas as correções pontuais que os findings
  exigem, sem reorganizar o que já respeita as camadas.
- **Achado isolado de baixa severidade** (ex: só `print()` como logging) → correção
  in-place, **sem** criar nova árvore de diretórios.
