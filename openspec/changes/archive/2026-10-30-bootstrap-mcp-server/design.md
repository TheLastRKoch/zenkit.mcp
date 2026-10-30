# Design

## Context

See `proposal.md` for motivation. The repository is a fresh Python project: the legacy Telegram bot files are deleted in the working tree, OpenSpec 1.15 is configured, and no Python sources, dependency manifest, or tests exist. The only remaining operational constraints come from MCP clients: a server launched over stdio must keep protocol traffic on stdout, and discovery/config must work with no credentials present.

The FastMCP framework (PyPI `fastmcp`, current major version 4, requires Python >= 3.10) provides the server class, decorator-based tool registration, transport handling, and an in-memory `Client` suitable for tests. FastMCP 4 is the standalone successor to the implementation bundled in the official MCP Python SDK and matches the "fast mcp" requirement.

## Goals / Non-Goals

**Goals:**

- A small set of importable top-level modules under `src/` whose server can be constructed for tests and launched as a process.
- A runnable, discoverable tool that validates credentials/config handling without requiring a Zenkit account or network.
- One canonical developer workflow: `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`.
- Documentation that is executable as written by a new contributor or coding agent.

**Non-Goals:**

- Real Zenkit API calls, authentication flows, pagination, or write operations.
- HTTP middleware/auth hardening, deployment artifacts, containers, or CI workflows.
- Multi-capability domain decomposition beyond what the placeholder tool needs.

## Decisions

### Framework: FastMCP 4, pinned to the current major

Use `fastmcp>=4.1,<5`. Alternatives: the low-level `mcp` SDK (more boilerplate for schemas and dispatch) and FastMCP 2 (older major, now superseded). The decorator API (`@mcp.tool`, `mcp.run()`) plus in-memory `Client` gives testable dispatch with no socket handling, and pinning below 5 avoids silent breakage from a future major.

### Packaging: `uv` with a flat `src/` module tree and a console script

`pyproject.toml` declares `requires-python = ">=3.12"` and dependencies; `uv.lock` is committed; `.python-version` pins 3.12. Sources live directly under `src/` as top-level modules (`server.py`, `config.py`, `tools/`). Hatchling packages the contents of `src/` with `only-include = ["src"]` and `sources = ["src"]`, so the installed distribution exposes `server`, `config`, and `tools` at the top level. The console script is `zenkit-mcp = "server:main"`. Direct execution is `uv run python src/server.py`, guarded by `if __name__ == "__main__": main()`; there is no `python -m` entrypoint because `src` is not an importable package.

Because `src/` is placed on `sys.path` when running the script directly, `server.py` imports its siblings with top-level imports (`from config import ...`, `from tools.zenkit import ...`), which also match the installed module names.

`uv` replaces `requirements.txt`: `uv add` / `uv add --dev` update both manifest and lock file, while `uv sync` and `uv lock --check` reproduce and verify the environment.

### Server construction: factory plus module-level instance

`server.py` exposes:

- `create_server(...) -> FastMCP`: builds and configures the server, registers tools, and is what tests use.
- `mcp = create_server()`: module-level instance so the FastMCP CLI (`fastmcp run ...:mcp`) and other tooling can discover it.
- `main(argv=None) -> None`: parses launch options and calls `mcp.run(...)`.

Version reporting reads `importlib.metadata.version("zenkit-mcp")`, falling back to `"0.0.0"` only when running from uninstalled sources, so the single source of truth remains `pyproject.toml`.

Tool registration lives in `tools/zenkit.py` behind `register(mcp)`, keeping `server.py` limited to wiring. This makes adding a second tool a one-line change plus a test.

### Configuration: environment-only, read per invocation

`config.py` defines a frozen `Settings` dataclass with `api_key: str | None` and `api_base_url: str`, loaded by `Settings.from_env()`. The tool loads settings at call time rather than import time, so tests can use `monkeypatch.setenv` without re-importing modules and a client can change configuration without restarting the server.

Only `ZENKIT_API_KEY` and `ZENKIT_API_BASE_URL` are supported; the default base URL is `https://zenkit.com/api/v1`. No `.env` loading dependency is added: the file is ignored by git but users export variables themselves (documented in the README). Base URL validation requires an `http`/`https` scheme and a non-empty host; failures raise `fastmcp.exceptions.ToolError` with a message that names `ZENKIT_API_BASE_URL`.

### Placeholder tool contract

`zenkit_connection_status` is a no-argument tool returning a JSON-serializable dict: `configured` (bool), `api_base_url` (str), and `message` (str). It deliberately performs no HTTP calls; this keeps startup and tests offline and gives the later API-integration change a stable shape to extend.

The API key is used only to compute `configured`; it is never included in results, messages, or logs.

### Transports: stdio default, HTTP opt-in via argparse

`main()` uses `argparse` with `--transport {stdio,http}` (default `stdio`), `--host` (default `127.0.0.1`), and `--port` (default `8000`). `argparse` rejects unknown choices with exit status 2 and an explanatory usage message on stderr, satisfying fail-fast behavior without custom validation. HTTP mode maps to `mcp.run(transport="http", host=..., port=...)`; stdio maps to `mcp.run()`.

Environment variables are not used for transport selection, keeping process behavior explicit and reproducible in client configuration files.

### Logging: standard library logging to stderr

A module logger writes through a `StreamHandler(sys.stderr)`. No `print()` calls are used in server code. This preserves stdout for the stdio protocol stream and keeps diagnostics visible in client logs. FastMCP's default behavior is not overridden beyond ensuring our own output is stderr-bound.

### Tests: in-memory FastMCP client, async by default

Dev dependencies are `pytest`, `pytest-asyncio` (with `asyncio_mode = "auto"`), and `ruff`. Tests build `create_server()` and use `async with Client(server) as client` to exercise real dispatch:

- discovery: `list_tools()` contains `zenkit_connection_status` with no required inputs;
- status without credentials and with credentials;
- default and overridden base URL;
- malformed base URL raises `ToolError`;
- the API key value never appears in the result;
- `parse_args` rejects unknown transports with `SystemExit`.

This tests observable MCP behavior instead of internal helpers, and requires no network or subprocess.

### Quality configuration and docs

`ruff` runs with `target-version = "py312"`, `line-length = 100`, and rules `E`, `F`, `I`, `UP`, `B`. Configuration lives in `pyproject.toml` to avoid a second config file.

`README.md` is user-facing (purpose, prerequisites, install, run, client config, tests, layout, troubleshooting). `AGENTS.md` is agent-facing (canonical commands, layout, conventions, adding a tool and test, secrets/stdout rules, OpenSpec workflow). Both use only commands validated during implementation.

`.gitignore` is replaced with Python/uv ignores (`.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `.env`) while retaining editor ignores; `uv.lock` stays tracked.

### Target layout

```
pyproject.toml
uv.lock
.python-version
README.md
AGENTS.md
.gitignore
src/server.py         # create_server(), mcp, main(), __main__ guard
src/config.py         # Settings.from_env(), URL validation
src/tools/__init__.py # tools package marker
src/tools/zenkit.py   # zenkit_connection_status + register()
tests/test_server.py
tests/test_tools.py
```

## Risks / Trade-offs

- **FastMCP 4 API drift** → Pin `<5`, rely on documented public API only, and cover behavior through the in-memory client so upgrades fail in tests rather than at runtime.
- **Stdout pollution breaks stdio clients** → Logging handler pinned to stderr, no `print()` in project code, and a code-review rule recorded in `AGENTS.md`. A subprocess smoke check is part of manual verification.
- **Top-level module name collisions** → Flattening to `src/server.py`, `src/config.py`, and `src/tools/` installs generic module names that could be shadowed by another distribution or the working directory. Run through `uv run`/the installed console script, avoid adding further generic module names, and revisit a namespaced package if the module count grows.
- **Placeholder tool mistaken for real integration** → Name and description state that it reports configuration only; README marks real API calls as future work.
- **Secret leakage through logs/errors** → The key is never interpolated into a result or error; a test asserts its absence, and URL errors reference only the variable name.
- **Version looked up from uninstalled sources** → `importlib.metadata` fallback keeps local runs working; tests assert a non-empty reported version.
- **No CI in this change** → Quality gates are documented and runnable locally; automation can be added later without changing the specs.
- **Local HTTP port conflicts when validating HTTP mode** → Document an override via `--port` and keep `127.0.0.1` as the default bind address.

## Migration Plan

1. Keep the already-staged deletions of the legacy bot files.
2. Move the existing modules from `src/zenkit_mcp/` to the flat `src/` tree (`src/server.py`, `src/config.py`, `src/tools/`), delete `src/zenkit_mcp/` (including `__init__.py` and `__main__.py`), and remove `requirements.txt` from the tree.
3. Run `uv sync`, `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest`; then smoke-test stdio startup and HTTP mode.
4. Rollback is `git checkout -- .` plus `git clean -fd` for the new untracked scaffold files; no data migration or deployment state is involved.
