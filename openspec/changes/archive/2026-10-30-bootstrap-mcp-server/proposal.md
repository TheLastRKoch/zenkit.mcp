# Proposal

## Why

The repository currently contains only an archived Telegram bot, with no reusable foundation for the Model Context Protocol (MCP) work this project is now meant to do (`zenkit.mcp`). Starting from a clean, well-documented scaffold removes the cost of piecing together packaging, dependency management, server wiring, and contributor guidance on every future change, and gives the Zenkit MCP server a validated starting point that clients can launch immediately.

## What Changes

- **BREAKING**: Remove the legacy Telegram bot sources (`main.py`, `command_handlers.py`, `services.py`, `utils.py`, `Procfile`, `requirements.txt`, `templates/`) so the repository becomes a Python MCP server project. The deletion is already staged in the working tree; this change formalizes the new target layout.
- Introduce a `uv`-managed Python project (`pyproject.toml`, `uv.lock`, `.python-version`) targeting Python 3.12, with `fastmcp` (v4) as the runtime dependency and a flat `src/` layout containing the top-level modules `server.py`, `config.py`, and `tools/`.
- Add a FastMCP server entrypoint that runs over stdio by default and can be started with `uv run zenkit-mcp`, `uv run python src/server.py`, or the FastMCP CLI, with an opt-in HTTP transport mode.
- Add one placeholder Zenkit tool, `zenkit_connection_status`, that reports whether Zenkit credentials are configured without performing any network calls, so the scaffold is runnable and testable before the real API client exists.
- Add developer tooling: `ruff` lint/format configuration, `pytest` tests exercising the server through FastMCP's in-memory `Client`, and a `uv sync` / `uv run` workflow documented for contributors.
- Add `README.md` (purpose, prerequisites, setup, run, client configuration, layout, troubleshooting) and `AGENTS.md` (repository conventions and instructions for coding agents).
- Update `.gitignore` for the Python/uv toolchain (`.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `.env`) while keeping editor and secrets ignores.

## Capabilities

### New Capabilities

- `mcp-server-runtime`: How the FastMCP application is constructed, named, versioned, and launched (stdio by default, optional HTTP), including clean stdout/stderr behavior and the executable entrypoints.
- `zenkit-tools`: The tool surface exposed to MCP clients, starting with the credential-free `zenkit_connection_status` placeholder and the conventions (typed arguments, docstrings, structured errors) every future Zenkit tool follows.
- `project-tooling`: The reproducible `uv`-based development workflow, lint/format rules, in-memory test strategy, and the required `README.md` / `AGENTS.md` contribution documentation.

### Modified Capabilities

None. No existing specs exist in this repository.

## Impact

- **Code**: Replaces the legacy bot sources with top-level modules under `src/` (`server.py`, `config.py`, `tools/zenkit.py`), plus `tests/`.
- **Dependencies**: New runtime dependency `fastmcp>=4.1,<5`; dev dependencies `pytest`, `pytest-asyncio`, `ruff`. Removes the pinned `requirements.txt` set used by the Telegram bot.
- **Tooling**: Adds `pyproject.toml`, `uv.lock`, `.python-version`, Markdown docs, and updated `.gitignore`. Git history and the existing OpenSpec configuration are untouched.
- **Operations**: No deployment target is defined in this change; the previous Heroku `Procfile` is removed. The server is launched locally by MCP clients over stdio.
- **Assumptions**: "fast mcp" means the [FastMCP](https://gofastmcp.com) framework (PyPI `fastmcp`, current major version 4). "agents.md" means the conventional root-level `AGENTS.md`. Real Zenkit API integration, authentication flows, and CI are explicitly out of scope and will be separate changes.
