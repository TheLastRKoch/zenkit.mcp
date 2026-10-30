# Tasks

## 1. Project foundation

- [x] 1.1 Confirm the legacy bot files (`main.py`, `command_handlers.py`, `services.py`, `utils.py`, `Procfile`, `requirements.txt`, `templates/`, `env.example`) are removed and no source references remain; verify with `git status --short` and `grep -r "telegram" --include="*.py" src tests 2>/dev/null`
- [x] 1.2 Create `pyproject.toml` with project metadata, `requires-python = ">=3.12"`, `zenkit-mcp` console script pointing at `server:main`, hatchling wheel config (`only-include = ["src"]`, `sources = ["src"]`), and `[tool.ruff]` / `[tool.pytest.ini_options]` settings; verify `uv sync` succeeds and `uv run zenkit-mcp --help` shows the server options
- [x] 1.3 Add runtime dependency `fastmcp>=4.1,<5` and dev dependencies `pytest`, `pytest-asyncio`, `ruff` with `uv add`; verify `uv.lock` is created and `uv lock --check` exits 0
- [x] 1.4 Add `.python-version` pinned to 3.12 and replace `.gitignore` with Python/uv ignores (`.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `.env`, editor directories); verify `git status --short` does not list `.venv/`, `.pytest_cache/`, `.ruff_cache/`, or `.env`
- [x] 1.5 Create the flat `src/` module tree (`server.py`, `config.py`, `tools/`) and `tests/` skeleton, with a `tools/__init__.py` marker; verify `uv run python -c "import server, config, tools"` succeeds

## 2. Configuration and Zenkit status tool

- [x] 2.1 Implement `src/config.py` with a frozen `Settings` dataclass, `Settings.from_env()` reading `ZENKIT_API_KEY` and `ZENKIT_API_BASE_URL`, the default `https://zenkit.com/api/v1`, and absolute HTTP/HTTPS URL validation; verify with unit tests covering default, override, and invalid values
- [x] 2.2 Implement `src/tools/zenkit.py` with `zenkit_connection_status` returning `configured`, `api_base_url`, and `message`, never echoing the API key, and raising `ToolError` for malformed URLs; verify with in-memory `Client` tests for both credential states and the error case
- [x] 2.3 Add a test asserting the configured API key value never appears in the tool result or captured logs, importing modules from the flat `src/` tree; verify with `uv run pytest tests/test_tools.py`
- [x] 2.4 Document Zenkit configuration and the status tool in `README.md` (environment variables, default URL, no-network behavior), using imports that match the flat `src/` modules; verify the shown `export`/`uv run` commands execute as written

## 3. Server runtime and entrypoints

- [x] 3.1 Implement `src/server.py` with `create_server()` (name `zenkit-mcp`, version from `importlib.metadata`, instructions, registered tools), module-level `mcp`, and `main(argv=None)`; verify `uv run python -c "from server import create_server; create_server()"` succeeds
- [x] 3.2 Add `argparse` transport options (`--transport {stdio,http}`, `--host` default `127.0.0.1`, `--port` default `8000`) and configure logging to stderr; verify unknown transports exit non-zero with a message on stderr and no `print()` calls exist in project code
- [x] 3.3 Add an `if __name__ == "__main__": main()` guard to `src/server.py` and remove the `__main__.py` module; verify `uv run python src/server.py --help` and `uv run zenkit-mcp --help` both show the same options
- [x] 3.4 Write `tests/test_server.py` importing `server` from the flat `src/` tree and covering tool discovery through the in-memory client, server name/version metadata, argument parsing defaults, and rejection of unknown transports; verify `uv run pytest tests/test_server.py`
- [x] 3.5 Document running the server and connecting an MCP client in `README.md` (stdio command via `zenkit-mcp` or `src/server.py`, HTTP command, client configuration snippet); verify the snippet's command starts the server over stdio without writing non-protocol output to stdout

## 4. Contributor and agent documentation

- [x] 4.1 Create `AGENTS.md` covering canonical `uv` commands, the flat `src/` project layout, coding conventions, secrets and stdout rules, the "add a tool plus tests" recipe, and the OpenSpec workflow; verify every command it lists runs successfully from the repository root
- [x] 4.2 Complete `README.md` with purpose, prerequisites (Python 3.12, uv), installation, the flat `src/` project layout, test/lint commands, and troubleshooting; verify `uv run pytest` and both `ruff` commands match the documented invocations
- [x] 4.3 Add a note that real Zenkit API calls, authentication, and CI are out of scope in both `README.md` and `AGENTS.md`; verify the wording matches the specs' non-goals

## 5. End-to-end verification

- [x] 5.1 Run `uv sync --locked`, `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest` from a clean environment after the layout move; verify all commands exit 0 with no credentials set
- [x] 5.2 Smoke-test stdio startup and tool listing with the FastMCP CLI or an MCP client using the documented `zenkit-mcp` command; verify stdout contains only protocol messages and diagnostics appear on stderr
- [x] 5.3 Smoke-test HTTP mode on port 9000 and confirm shutdown leaves no process or listening socket behind
- [x] 5.4 Confirm `git status --short` shows only intended new/changed files, with `uv.lock`, `README.md`, and `AGENTS.md` tracked and no secrets or local caches present

## Workflow follow-up

- Archive the change after review and once the specification deltas are synced.
