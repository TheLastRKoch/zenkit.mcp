# zenkit.mcp

MCP server exposing Zenkit project management tools to AI agents, built with [FastMCP](https://gofastmcp.com) and managed with [uv](https://docs.astral.sh/uv/).

## Requirements

- Python 3.12 or newer (`.python-version` pins 3.12)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

```bash
uv sync
```

## Running the server

The default transport is stdio, which is what local MCP clients use when they launch the server as a subprocess:

```bash
uv run zenkit-mcp
# equivalent:
uv run python src/server.py
```

To serve Streamable HTTP instead (useful for inspecting with `curl` or a browser-based client):

```bash
uv run zenkit-mcp --transport http --host 127.0.0.1 --port 8000
```

Use `uv run zenkit-mcp --help` to see all options. In stdio mode, logs go to stderr and stdout carries only MCP protocol messages, so the server can be safely launched by a client.

### MCP client configuration

Register the server in your MCP client (for example GitHub Copilot CLI or Claude Desktop) with an absolute path to this repository:

```json
{
  "mcpServers": {
    "zenkit": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/zenkit.mcp",
        "zenkit-mcp"
      ],
      "env": {
        "ZENKIT_API_KEY": "your-api-key"
      }
    }
  }
}
```

Omit the `env` block if you have no key yet; `zenkit_connection_status` reports the configuration state either way.

## Configuration

The server reads Zenkit configuration from environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ZENKIT_API_KEY` | No (needed by future API-backed tools) | — | Zenkit API key. The scaffold never returns or logs this value. |
| `ZENKIT_API_BASE_URL` | No | `https://zenkit.com/api/v1` | Base URL for the Zenkit API. Must be an absolute HTTP or HTTPS URL. |

The scaffold performs no outbound network requests. The `zenkit_connection_status` tool reports whether a key is configured and which base URL is in effect, without contacting Zenkit:

```bash
export ZENKIT_API_KEY="your-api-key"
uv run python -c "from tools.zenkit import zenkit_connection_status; print(zenkit_connection_status())"
```

> `.env` files are git-ignored but are not loaded automatically; export the variables in your shell or pass them through your MCP client's `env` block.

## Project layout

```
src/server.py         create_server(), module-level mcp, CLI + transports
src/config.py         environment settings and URL validation
src/tools/zenkit.py   Zenkit tools and registration
tests/                           pytest suite (in-memory MCP client)
openspec/                        specs and in-flight changes
```

## Development

```bash
uv run pytest                        # test suite
uv run ruff check                    # lint
uv run ruff format --check           # formatting check
uv run ruff format                   # apply formatting
uv lock --check                      # verify lock file is current
```

Tests run offline and do not require Zenkit credentials. Add a tool by following `AGENTS.md`.

The project version lives in `VERSION`, which `pyproject.toml` reads dynamically. Before opening a pull request, use the `version-bump` skill in `.github/skills/version-bump/` to classify and commit the bump.

## Troubleshooting

- **`zenkit-mcp: command not found`** — run commands through `uv` (for example `uv run zenkit-mcp`) and make sure `uv sync` has completed.
- **The MCP client cannot start the server** — use an absolute repository path in the client's `--directory` argument. Check the client's server logs (stderr) for startup errors.
- **`ZENKIT_API_BASE_URL` error** — the value must be an absolute HTTP or HTTPS URL; correct it and restart the server or client.
- **Port already in use** — choose another port with `--port`, for example `uv run zenkit-mcp --transport http --port 9000`.
- **Environment changes are not picked up** — configuration is read per tool call, but clients launch the server with their own environment; restart the client session after changing variables in its `env` block.
- **Streamable HTTP does not respond** — confirm the server is bound to the expected host/port and start it with `--transport http`; the default transport is stdio.

## Scope

This repository is currently a bootstrap scaffold. The following are intentionally out of scope until later changes:

- Real Zenkit API calls, pagination, and write operations
- Authentication and OAuth flows
- CI pipelines and deployment automation

Today it provides the server runtime, one credential-safe `zenkit_connection_status` tool, tests, linting, and documentation.
