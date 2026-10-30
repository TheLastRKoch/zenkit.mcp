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

Omit the `env` block if you have no key yet; `zenkit_connection_status` reports the configuration state either way, and API-backed tools explain that `ZENKIT_API_KEY` is missing until you set it.

#### Project-scoped configuration

The repository ships `.mcp.json`, so clients that read project-level MCP configuration pick the server up with no setup:

- **GitHub Copilot CLI** reads `.mcp.json` (or `.github/mcp.json`) from the session workspace. No per-session flags are needed; `copilot mcp list` shows `zenkit` as a workspace server.
- **Antigravity CLI (`agy`)** only reads user-level configuration, so register the launcher once per machine:

  ```bash
  agy mcp add zenkit -- bash /absolute/path/to/zenkit.mcp/scripts/zenkit-mcp.sh
  ```

Both entries launch `scripts/zenkit-mcp.sh`, which runs `uv run zenkit-mcp` from the repository root and resolves the API key without storing it in the repository: it uses `ZENKIT_API_KEY` when exported, otherwise the key recorded for the `zenkit` server in `~/.copilot/mcp-config.json`. The key only enters the server's environment and is never printed.

Because a project-level entry shadows a same-named user-level entry, the launcher performs that key lookup itself. Clients that only read user-level configuration can keep using the JSON above with an explicit `env` block.

## Tools

All tools use the `zenkit_` prefix. API-backed tools read `ZENKIT_API_KEY` and `ZENKIT_API_BASE_URL` from the environment on every call, attach the key as the `Zenkit-API-Key` header, and fail with an error naming `ZENKIT_API_KEY` when no key is configured.

| Tool | Parameters | Returns |
| --- | --- | --- |
| `zenkit_connection_status` | — | Configuration state and the effective base URL; makes no network calls. |
| `zenkit_get_current_user` | — | The authenticated user's identity; validates the configured key. |
| `zenkit_list_lists` | — | Accessible lists, each with `id`, `name`, and workspace context. |
| `zenkit_get_list` | `list_id` | A single list's details. |
| `zenkit_list_columns` | `list_id` | The list's columns, each with `id`, `uuid`, `name`, `data_type`, and `resource_role`. |
| `zenkit_get_entries` | `list_id`, `filter=None`, `limit=100`, `skip=0` | Entries, each with `id`, `uuid`, and `fields`. |
| `zenkit_get_entry` | `list_id`, `entry_id` | A single entry. |
| `zenkit_create_entry` | `list_id`, `fields` | The created entry's `id`, `uuid`, and `fields`. |
| `zenkit_update_entry` | `list_id`, `entry_id`, `fields` | The updated entry's `id`, `uuid`, and `fields`. |

`zenkit_get_current_user` projects Zenkit's user payload onto these identity fields: `id`, `uuid`, `username`, `displayname`, `fullname`, `emails`, `imageLink`, `created_at`, `last_login`, `last_seen`, and `organizationId`. Every other upstream field is dropped, and any field whose name denotes a credential (`key`, `apiKey`/`api_key`, `token`, `secret`, or `password`) is removed recursively, so the configured API key never appears in a tool result.

`list_id` and `entry_id` accept Zenkit's numeric and short string identifiers.

Zenkit keys custom column values as `<element-uuid>_<dataType>`, for example `c0148d60-c58a-4e17-89b6-3f5cc0c0785b_text`. Entry tools return those pairs under `fields`, and `zenkit_create_entry` accepts them verbatim:

```json
{"list_id": 3639611, "fields": {"c0148d60-c58a-4e17-89b6-3f5cc0c0785b_text": "Testing API"}}
```

`zenkit_update_entry` accepts the same key/value shape and sends only the supplied keys, so every other column keeps its current value; send `null` to clear one. Zenkit distinguishes date-only values from timed slots: to schedule an entry at a specific time, send the date value together with its `<element-uuid>_hasTime` flag set to `true` and its `<element-uuid>_endDate` in the same call.

Use `zenkit_list_columns` to map an element's `uuid` and `data_type` to a human-readable column name. `data_type` is derived from the element definition: it is Zenkit's own type when the element reports one, otherwise the value-type key inside its `businessData` (`text`, `date`, `categories`, `persons`, `files`, `number`, `references`, `link`, or `checked`). System columns such as Created or Last Updated carry no value payload and report `null` rather than a guessed type.

`zenkit_get_entries` passes `filter` through to Zenkit verbatim. `limit` is the maximum number of entries to return; larger values are fetched in pages of 100 internally, and `skip` offsets the first returned entry.

## Configuration

The server reads Zenkit configuration from environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ZENKIT_API_KEY` | Yes, for API-backed tools | — | Zenkit API key. It is sent only as the `Zenkit-API-Key` header and is never returned or logged. |
| `ZENKIT_API_BASE_URL` | No | `https://zenkit.com/api/v1` | Base URL for the Zenkit API. Must be an absolute HTTPS URL; plaintext URLs are rejected so the API key is never sent unencrypted. |

The `zenkit_connection_status` tool reports whether a key is configured and which base URL is in effect, without contacting Zenkit:

```bash
export ZENKIT_API_KEY="your-api-key"
uv run python -c "from tools.zenkit import zenkit_connection_status; print(zenkit_connection_status())"
```

Every other API-backed tool sends requests to the configured base URL. A missing key, a rejected key, an unreachable service, a timeout, or a malformed response becomes a tool error with guidance instead of a traceback.

> `.env` files are git-ignored but are not loaded automatically; export the variables in your shell or pass them through your MCP client's `env` block.

## Project layout

```
src/server.py         create_server(), module-level mcp, CLI + transports
src/config.py         environment settings and URL validation
src/zenkit_api.py     ZenkitClient: auth header, error mapping, pagination
src/tools/zenkit.py   Zenkit tools and registration
tests/                           pytest suite (in-memory MCP client, mocked HTTP)
scripts/zenkit-mcp.sh            stdio launcher used by project-level MCP config
.mcp.json                        project-scoped MCP server configuration
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

Tests run offline and do not require Zenkit credentials: the Zenkit HTTP client is exercised through `httpx.MockTransport` and tools through the in-memory client. Add a tool by following `AGENTS.md`.

The project version lives in `VERSION`, which `pyproject.toml` reads dynamically. Before opening a pull request, use the `version-bump` skill in `.github/skills/version-bump/` to classify and commit the bump.

## Troubleshooting

- **`zenkit-mcp: command not found`** — run commands through `uv` (for example `uv run zenkit-mcp`) and make sure `uv sync` has completed.
- **The MCP client cannot start the server** — use an absolute repository path in the client's `--directory` argument. Check the client's server logs (stderr) for startup errors.
- **`ZENKIT_API_KEY` is not configured** — API-backed tools refuse to send unauthenticated requests; set the key in the environment or your MCP client's `env` block.
- **Zenkit rejected the credentials** — the key is invalid or lacks access to the requested list; verify it in Zenkit and restart the client session.
- **Zenkit did not respond within 30 seconds** — check network connectivity and that `ZENKIT_API_BASE_URL` points at the Zenkit API.
- **`ZENKIT_API_BASE_URL` error** — the value must be an absolute HTTPS URL; correct it and restart the server or client.
- **Port already in use** — choose another port with `--port`, for example `uv run zenkit-mcp --transport http --port 9000`.
- **Environment changes are not picked up** — configuration is read per tool call, but clients launch the server with their own environment; restart the client session after changing variables in its `env` block.
- **Streamable HTTP does not respond** — confirm the server is bound to the expected host/port and start it with `--transport http`; the default transport is stdio.

## Scope

The server covers reading Zenkit users, lists, columns, and entries, plus creating and updating entries, through the Zenkit REST API. The following remain out of scope until later changes:

- Deleting, moving, or copying entries
- Creating, renaming, or deleting lists and columns
- OAuth flows, webhooks, retries with backoff, and response caching
- CI pipelines and deployment automation

Today it provides the server runtime, the credential-safe `zenkit_connection_status` tool, eight API-backed tools for users, lists, columns, and entries, an offline test suite, linting, and documentation.
