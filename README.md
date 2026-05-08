# API Livraria - Sistema de Gerenciamento de Biblioteca Digital

API REST para gerenciar uma biblioteca digital moderna, cobrindo cadastro de usuarios, autores, livros e todo o ciclo de emprestimos. O projeto foi desenhado como um monolito modular em camadas, com foco em separacao de responsabilidades, observabilidade e evolucao incremental.

## Sumario

- [Visao geral](#visao-geral)
- [Decisoes arquiteturais](#decisoes-arquiteturais)
- [Stack e tecnologias](#stack-e-tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Regras de negocio](#regras-de-negocio)
- [Requisitos do case e cobertura](#requisitos-do-case-e-cobertura)
- [Documentacao da API](#documentacao-da-api)
- [Postman](#postman)
- [Observabilidade](#observabilidade)
- [Como rodar com Docker Compose](#como-rodar-com-docker-compose)
- [Configuracao de ambiente](#configuracao-de-ambiente)
- [Testes](#testes)
- [Roadmap](#roadmap)
- [Contato](#contato)

## Visao geral

Este sistema foi desenvolvido para atender o desafio de uma biblioteca digital, implementando as entidades e fluxos centrais de emprestimos, com recursos adicionais como reservas, notificacoes, cache, rate limiting, relatorios e metricas. A API expoe endpoints REST documentados via Swagger/OpenAPI e conta com colecao do Postman para facilitar o uso.

## Decisoes arquiteturais

**Monolito modular em camadas**
- Mantem deploy simples e rapido, com transacoes consistentes e baixa friccao operacional.
- Organizacao modular por dominios (users, authors, books, loans, reservations, notifications, reports), permitindo evoluir para microservicos no futuro.
- Separacao em camadas (controllers -> services -> repositories), reduzindo acoplamento e facilitando testes.

**Bus de eventos local**
- Um Event Bus in-process permite desacoplar o fluxo principal de efeitos colaterais (ex: notificacoes).
- O design prepara a migracao futura para fila externa (Kafka/RabbitMQ) sem reescrita ampla das regras de negocio.

**Cron jobs e tarefas assincronas**
- APScheduler executa jobs de notificacoes de vencimento em horarios definidos (ex: 08:00).
- O job analisa emprestimos a vencer e gera notificacoes automaticas.

**Cache com Redis**
- Redis armazena resultados de consultas frequentes, reduzindo carga de banco.
- O cache eh invalidado em operacoes de escrita relevantes.

## Stack e tecnologias

- Python 3.12
- FastAPI + Pydantic (validacao e OpenAPI)
- SQLAlchemy async + Alembic (ORM e migracoes)
- PostgreSQL (persistencia)
- Redis (cache)
- APScheduler (cron jobs)
- Prometheus + Grafana (metricas)
- Structlog (logging estruturado)
- SlowAPI (rate limiting)
- Pytest + HTTPX (testes)

## Estrutura do projeto

```
app/
	config/          # settings, seguranca e observabilidade
	domain/          # dominios (controllers, services, repositories, models, schemas)
	events/          # eventos e handlers
	infra/           # database, middlewares e observabilidade
	schedule/        # scheduler e jobs
docs/
	endpoints.md     # lista de endpoints e acesso
```

## Regras de negocio

- Prazo padrao de emprestimo: 14 dias
- Multa: R$ 2,00 por dia de atraso
- Maximo de 3 emprestimos ativos por usuario
- Renovacao: 7 dias adicionais, ate 2 renovacoes
- Reserva somente quando nao ha copias disponiveis

## Requisitos do case e cobertura

**Entidades obrigatorias**
- Usuario: implementado com autenticacao via JWT
- Livro: implementado com disponibilidade e autor vinculado
- Emprestimo: implementado com ciclo completo e multa

**Funcionalidades principais**
- Gestao de usuarios (CRUD admin + login + perfil)
- Catalogo de livros e autores com paginacao e filtros
- Emprestimos com devolucao, multa, renovacao e cancelamento
- Historico de emprestimos por usuario

**Extras implementados**
- Paginacao em listagens
- Documentacao automatica (Swagger/OpenAPI)
- Validacao robusta com Pydantic
- Logging estruturado
- Autenticacao JWT
- Reservas de livros
- Cache Redis
- Rate limiting
- Testes unitarios e de integracao
- Notificacoes de vencimento (job agendado)
- Renovacao de emprestimos
- Exportacao de relatorios (CSV/PDF)
- Observabilidade (health check + metricas)

## Documentacao da API

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Endpoints detalhados: [docs/endpoints.md](docs/endpoints.md)

### Print do Swagger

![Swagger UI](docs/assets/swagger-ui.svg)

## Postman

- Colecao: [docs/postman/api-livraria.postman_collection.json](docs/postman/api-livraria.postman_collection.json)
- Variaveis sugeridas:
	- `base_url`: http://localhost:8000
	- `admin_token`: JWT de admin
	- `user_token`: JWT de usuario comum

## Observabilidade

- Health check: `GET /health`
- Metricas Prometheus: `GET /metrics`
- Logging estruturado com Structlog (JSON)
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Como rodar com Docker Compose

Pre-requisitos:
- Docker e Docker Compose

Subir a stack:

```bash
docker compose up --build
```

Servicos principais:
- API: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379

Observacao: as migracoes sao executadas automaticamente no startup do container da API.

## Configuracao de ambiente

Variaveis no .env:

| Variavel | Descricao | Exemplo |
| --- | --- | --- |
| DATABASE_URL | URL do Postgres | postgresql+asyncpg://admin:admin@postgres:5432/library |
| REDIS_URL | URL do Redis | redis://redis:6379 |
| JWT_SECRET | Segredo do JWT | supersecret |
| JWT_EXPIRE_MINUTES | Expiracao do token | 60 |
| ENVIRONMENT | Ambiente | development |

## Testes

Os testes usam um Postgres de teste na porta 5433 (service `postgres_test`).

1. Suba apenas o banco de teste:

```bash
docker compose up -d postgres_test
```

2. Rode os testes na maquina local (Python 3.12):

```bash
uv run pytest
```

## Roadmap

- Extrair o Event Bus local para um broker (Kafka/RabbitMQ)
- Melhorar jobs com fila e retentativa
- Adicionar front-end web
- Colecoes adicionais (Insomnia)

## Contato

Em caso de duvidas sobre requisitos ou especificacoes, entre em contato.
