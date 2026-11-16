# Tasks

## 1. Configuration

- [x] 1.1 Add `ZENKIT_MCP_AUTH_TOKEN` parsing to `src/config.py` as a dedicated immutable settings object with a `configured`-style property, treating blank values as absent; verify with new cases in `tests/test_config.py` covering set, unset, and whitespace-only values.
- [x] 1.2 Extend `tests/test_config.py` to assert a configured token is never included in validation errors or dataclass representations; verify the new assertions fail if the token is interpolated into a message.

## 2. HTTP authentication and startup guard

- [x] 2.1 Add a helper that builds a static bearer-token auth provider from the configured token, and give `create_server()` an optional `auth` argument passed to `FastMCP(auth=...)`; verify `tests/test_server.py` shows an unauthenticated server when no token is configured.
- [x] 2.2 Enforce the startup guard in `main()`: HTTP mode on a non-loopback host without a token exits non-zero with a message naming `ZENKIT_MCP_AUTH_TOKEN`, while `127.0.0.1`, `::1`, `localhost`, and a configured token are accepted; verify each case in `tests/test_server.py`.
- [x] 2.3 Add a test that builds the HTTP app from an authenticated server and asserts a POST to `/mcp` without a bearer token returns `401` while the same request with the configured token is not rejected; verify it passes offline through an ASGI transport.
- [x] 2.4 Document `ZENKIT_MCP_AUTH_TOKEN` in the `README.md` configuration table, including how to generate a value, and add a troubleshooting entry for `401` responses; verify the documented command produces a token and the table lists the variable.

## 3. Container image

- [x] 3.1 Add `.dockerignore` excluding `.venv`, `.git`, `tests`, `openspec`, caches, and `.env`; verify `docker build` transfers no excluded path by checking the build context summary.
- [x] 3.2 Add the multi-stage `Dockerfile` on `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` that installs from `uv.lock` with `uv sync --locked --no-dev`, carries no credential in any `ARG`/`ENV`, runs as a non-root user, exposes `9010`, and defaults to `--transport http --host 0.0.0.0 --port 9010`; verify `docker build -t zenkit-mcp:test .` succeeds.
- [x] 3.3 Verify the built image: confirm the process runs as a non-root user, confirm port `9010` answers, and confirm a request without a bearer token is rejected while one with the token succeeds; record the commands and output.
- [x] 3.4 Add a "Running in Docker" section to `README.md` covering build, run with the two environment variables, the `/mcp` endpoint path, and the security note about publishing port `9010`; verify each command in the section runs as written.

## 4. Compose deployment

- [x] 4.1 Add `docker-compose.yml` with one service, `ports: ["9010:9010"]`, required `${ZENKIT_API_KEY:?}` and `${ZENKIT_MCP_AUTH_TOKEN:?}`, `restart: unless-stopped`, and a TCP healthcheck on `127.0.0.1:9010`; verify `docker compose config` fails and names the missing variable when either is unset, and succeeds when both are exported.
- [x] 4.2 Verify `docker compose up -d` starts the stack, the container reports healthy, and an MCP initialization to `http://127.0.0.1:9010/mcp` succeeds only with the bearer token; tear the stack down afterwards.
- [x] 4.3 Extend the `README.md` deployment section with compose usage, `.env` handling (git-ignored, not auto-loaded by the application), a note that Docker bypasses host firewall rules on Linux so `127.0.0.1:9010` is the safer binding, and client configuration examples for n8n's MCP Client Tool and a VS Code HTTP server entry; verify the examples match the ports and path used in the compose file.
- [x] 4.4 Update the scope notes in `README.md` and `AGENTS.md` so container deployment is no longer listed as out of scope, and add the new files to the `AGENTS.md` project layout; verify no stale "deployment artifacts" exclusion remains.

## 5. Integration verification

- [x] 5.1 Run `uv run pytest`, `uv run ruff check`, and `uv run ruff format --check` and confirm all pass.
- [x] 5.2 Re-run the end-to-end flow from a clean state (build, compose up, unauthenticated rejection, authenticated tool listing, compose down) and confirm the observed behavior matches the specs in `specs/`.

## Workflow follow-up

- Bump `VERSION` with the `version-bump` skill before opening a pull request, noting the breaking change for non-loopback HTTP without a token.
- Archive the change after implementation and review are complete.
