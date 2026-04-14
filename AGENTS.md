# Repository Guidelines

## Project Structure & Module Organization
`ext_api/` contains the application code: `server.py` defines Bottle routes, `repositories/` handles persistence, `helpers/` holds shared HTTP/auth/AWS utilities, and `s3/` contains image storage logic. `app.py` is the CLI entrypoint for running the server, database initialization, and extension sync tasks. Tests live under `tests/` and mirror the runtime layout (`tests/s3/`, `tests/helpers/`). Database migrations are in `db_migrations/`, Bottle templates in `views/`, and local typing shims in `typings/`.

## Build, Test, and Development Commands
Use the `Makefile` as the default interface:

- `make test` runs the full gate: Ruff, Pyright, and pytest.
- `make ruff` checks linting and formatting.
- `make format` applies Ruff formatting.
- `make pyright` runs strict type checking.
- `make pytest` runs the unit-focused pytest suite on the host.
- `make integration` runs the containerized integration suite in `tests/integration/`.
- `make integration-down` stops and removes integration test containers, networks, and volumes.
- `docker-compose up -d` starts local services such as MongoDB.
- `./app.py init_db` applies database setup; `./app.py http_server` starts the API locally.

## Coding Style & Naming Conventions
Python uses 4-space indentation and a 120-character line length. Prefer type hints everywhere; Pyright runs in `strict` mode. Keep imports sorted and let Ruff handle formatting. Follow existing naming patterns: `snake_case` for functions/modules, `PascalCase` for TypedDict-style entity keys only when matching API payloads such as `GithubUrl` or `DeveloperName`. Place small, reusable integrations in `ext_api/helpers/`.

## Testing Guidelines
Write tests with `pytest` and keep them close to the module area they cover. Name files `test_*.py` and test functions `test_*`. Add focused unit tests for route helpers, repository behavior, and S3/GitHub edge cases.

Use the following test paths:

- Unit tests: run `make pytest` for normal host-side development. This covers the standard pytest suite and is the default fast feedback loop.
- Integration tests: run `make integration` to execute `tests/integration/` in Podman Compose with its required services. Host-side `pytest` skips these tests unless `RUN_INTEGRATION=1` is set by the container runner.
- Full verification: run `make test` before opening a PR to cover Ruff, Pyright, and the host-side pytest suite. If your change affects cross-service behavior, run `make integration` as well.

## Commit & Pull Request Guidelines
Recent history favors short, imperative subjects such as `Run extension sync once` or `Minor improvements`; dependency updates use `Bump <package> from <old> to <new>`. Keep commits scoped and descriptive. For pull requests, include a clear summary, note any config or migration impact, link the relevant issue, and include request/response examples or screenshots when route behavior or rendered templates change.

## Configuration & Security Tips
Secrets live in `.env` and should never be committed. The app expects AWS, Auth0, and MongoDB settings locally; use the sample values in `README.md` as a template and prefer least-privilege AWS credentials.
