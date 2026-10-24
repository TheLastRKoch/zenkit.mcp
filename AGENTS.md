# AGENTS.md

Guidance for coding agents and contributors working in this repository. Read `README.md` first for user-facing usage.

## Project overview

`zenkit-mcp` is a [FastMCP](https://gofastmcp.com) server that exposes Zenkit project management tools to MCP clients. It ships a credential-safe `zenkit_connection_status` tool plus API-backed tools for users, lists, columns, and entries (including entry creation), built on a shared HTTP client in `src/zenkit_api.py`.

- Language: Python 3.12+
- Framework: `fastmcp` 4.x (pinned `<5`)
- Dependency management: `uv`
- Layout: flat modules under `src/` with tests in `tests/`

## Canonical commands

Run everything with `uv` from the repository root.

```bash
uv sync                              # install runtime and dev dependencies
uv lock --check                      # verify the lock file matches pyproject.toml
uv run pytest                        # run the test suite
uv run ruff check                    # lint
uv run ruff format --check           # verify formatting
uv run ruff format                   # apply formatting
uv run zenkit-mcp                    # run over stdio (default)
uv run python src/server.py          # equivalent direct-script entrypoint
uv run zenkit-mcp --transport http --host 127.0.0.1 --port 8000
```

Never hand-edit `uv.lock`; change dependencies with `uv add` / `uv add --dev` so the manifest and lock file stay in sync.

## Project layout

```
VERSION                          single source of truth for the project version
src/server.py         create_server(), module-level mcp, CLI + transports
src/config.py         Settings.from_env() and URL validation
src/zenkit_api.py     ZenkitClient: auth header, error mapping, pagination
src/tools/zenkit.py   Zenkit tool implementations + register()
tests/                           pytest suite using FastMCP's in-memory Client
openspec/                        OpenSpec specs and in-flight changes
.github/skills/                  project skills (mirrored in .agents/skills/)
```

## Versioning

- `VERSION` at the repository root is the single source of truth. `pyproject.toml` reads it dynamically through hatchling; never hard-code or edit a version field in `pyproject.toml`.
- Before opening a pull request, run the `version-bump` skill (`.github/skills/version-bump/SKILL.md`). It inspects the branch diff, applies SemVer rules, writes `VERSION`, verifies `importlib.metadata`, and commits only the version file.
- Do not bump on the default branch, and do not bump twice on the same branch (`VERSION` already differs from the base branch).
- The skill commits the bump but does not create the PR.

## Conventions

- Use type hints on public functions and modules; keep `from __future__ import annotations` for modern syntax.
- Ruff is configured in `pyproject.toml` (`target-version = "py312"`, `line-length = 100`, rules `E`, `F`, `I`, `UP`, `B`). Run lint and format checks before finishing.
- **Never write to stdout from project code.** In stdio mode stdout is the MCP protocol stream. Use the `logging` module, which is configured to stderr in `configure_logging()`. Do not add `print()` calls under `src/`.
- **Secrets stay out of results and logs.** Read credentials through `Settings.from_env()`; never echo `ZENKIT_API_KEY`, its fragments, or full request headers.
- Load configuration per tool invocation (`Settings.from_env()`), not at import time, so clients and tests can change environment variables without re-importing.
- Raise `fastmcp.exceptions.ToolError` with an actionable message for expected failures. Do not leak tracebacks, internal paths, or raw exception text to clients.
- Name tools with the `zenkit_` prefix and snake_case (for example `zenkit_connection_status`). Write a docstring; FastMCP derives the tool description from it.
- The scaffold must start and run with no credentials and no outbound network access. Do not add network calls at import or startup time.
- `.env` is ignored but not auto-loaded; document environment variables in `README.md` instead of adding a dotenv dependency.

## Adding a tool

1. Implement a typed function in `src/tools/` (one module per Zenkit area) with a docstring describing its purpose. API-backed tools build a `ZenkitClient` from `Settings.from_env()` inside the call and use it as an async context manager; never construct a client at import time.
2. Register it in that module's `register(mcp)` with `mcp.add_tool(...)`.
3. Add a test in `tests/` that calls it through FastMCP's in-memory client:

   ```python
   from fastmcp import Client

   async with Client(create_server()) as client:
       result = await client.call_tool("zenkit_connection_status", {})
   ```

   Tests must stay offline: stub HTTP with `httpx.MockTransport` (see `tests/test_zenkit_api.py` and the `zenkit` fixture in `tests/test_tools.py`).
4. Document the tool and any new environment variables in `README.md`.

## Testing rules

- Tests run offline with no Zenkit credentials; clear `ZENKIT_API_KEY` and `ZENKIT_API_BASE_URL` in fixtures when behavior depends on the environment.
- Prefer testing observable MCP behavior through `Client` over calling internal helpers directly.
- Assert on values and types that distinguish correct behavior, and cover error paths when a tool can fail.
- `pytest-asyncio` runs in `auto` mode, so async tests need no marker.

## OpenSpec workflow

This repository uses OpenSpec (see `openspec/`). Plan behavior changes before implementing them.

```bash
openspec list                         # in-flight changes
openspec list --specs                 # existing capabilities
openspec status --change <name>       # artifact and task progress
openspec validate <name> --strict     # validate a change
```

- Planning artifacts live in `openspec/changes/<change-name>/` (`proposal.md`, `specs/<capability>/spec.md`, `design.md`, `tasks.md`).
- Do not implement behavior that is not described in an approved change; update the artifacts first if scope changes.
- Mark tasks complete in `tasks.md` only when the specified behavior is fully implemented and verified.
- Archive a change only after implementation and review are complete.

## Out of scope for the current tool surface

Entry update/delete/move/copy, list and column management (create, rename, delete), OAuth flows, webhooks, retries with backoff, response caching, deployment artifacts, and CI pipelines are intentionally not implemented yet. Do not add them without an approved OpenSpec change.
