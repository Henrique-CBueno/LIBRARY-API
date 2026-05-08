# Endpoints e controle de acesso

Legenda de acesso:

- Admin: requer usuario autenticado com role ADMIN
- Logado: requer autenticacao (inclui regras de dono/admin quando aplicavel)
- Aberto: sem autenticacao

## Sistema

| Metodo | Rota     | Acesso | Observacoes                            |
| ------ | -------- | ------ | -------------------------------------- |
| GET    | /        | Aberto | Health basico da API                   |
| GET    | /health  | Aberto | Verifica Postgres e Redis              |
| GET    | /metrics | Aberto | Exposto pelo Prometheus Instrumentator |

## Usuarios

| Metodo | Rota                  | Acesso | Observacoes             |
| ------ | --------------------- | ------ | ----------------------- |
| POST   | /users                | Aberto | Cadastro de usuario     |
| POST   | /users/login          | Aberto | Autenticacao (JWT)      |
| GET    | /users/me             | Logado | Perfil do usuario atual |
| GET    | /users                | Admin  | Lista paginada          |
| GET    | /users/{user_id}      | Admin  | Busca por id            |
| PUT    | /users/{user_id}      | Admin  | Atualiza usuario        |
| DELETE | /users/{user_id}      | Admin  | Remove usuario          |
| PUT    | /users/{user_id}/role | Admin  | Atualiza role           |

## Autores

| Metodo | Rota                 | Acesso | Observacoes       |
| ------ | -------------------- | ------ | ----------------- |
| POST   | /authors             | Admin  | Cria autor        |
| GET    | /authors             | Aberto | Lista paginada    |
| GET    | /authors/{author_id} | Aberto | Detalhes do autor |
| PUT    | /authors/{author_id} | Admin  | Atualiza autor    |
| DELETE | /authors/{author_id} | Admin  | Remove autor      |

## Livros

| Metodo | Rota             | Acesso | Observacoes              |
| ------ | ---------------- | ------ | ------------------------ |
| POST   | /books           | Admin  | Cria livro               |
| GET    | /books           | Aberto | Lista paginada e filtros |
| GET    | /books/{book_id} | Aberto | Detalhes do livro        |
| PUT    | /books/{book_id} | Admin  | Atualiza livro           |
| DELETE | /books/{book_id} | Admin  | Remove livro             |

## Emprestimos

| Metodo | Rota                      | Acesso | Observacoes                |
| ------ | ------------------------- | ------ | -------------------------- |
| POST   | /loans                    | Admin  | Cria emprestimo            |
| GET    | /loans                    | Admin  | Lista paginada e filtros   |
| GET    | /loans/active             | Admin  | Lista emprestimos ativos   |
| GET    | /loans/overdue            | Admin  | Lista emprestimos vencidos |
| GET    | /loans/{loan_id}          | Logado | Dono ou admin              |
| GET    | /loans/users/{user_id}    | Logado | Dono ou admin              |
| PUT    | /loans/{loan_id}          | Admin  | Atualiza emprestimo        |
| POST   | /loans/{loan_id}/return   | Logado | Dono ou admin              |
| POST   | /loans/{loan_id}/renew    | Logado | Dono ou admin              |
| POST   | /loans/{loan_id}/cancel   | Logado | Dono ou admin              |
| POST   | /loans/{loan_id}/pay-fine | Logado | Dono ou admin              |

## Reservas

| Metodo | Rota                                  | Acesso | Observacoes               |
| ------ | ------------------------------------- | ------ | ------------------------- |
| POST   | /reservations                         | Logado | Cria reserva              |
| GET    | /reservations                         | Logado | Lista do usuario ou admin |
| GET    | /reservations/{reservation_id}        | Logado | Dono ou admin             |
| POST   | /reservations/{reservation_id}/cancel | Logado | Dono ou admin             |

## Notificacoes

| Metodo | Rota                              | Acesso | Observacoes              |
| ------ | --------------------------------- | ------ | ------------------------ |
| GET    | /notifications                    | Admin  | Lista paginada e filtros |
| POST   | /notifications/jobs/due-loans/run | Admin  | Dispara job manual       |

## Relatorios

| Metodo | Rota               | Acesso | Observacoes             |
| ------ | ------------------ | ------ | ----------------------- |
| GET    | /reports/stats     | Admin  | Estatisticas do sistema |
| GET    | /reports/loans.csv | Admin  | Exporta CSV             |
| GET    | /reports/fines.pdf | Admin  | Exporta PDF             |
