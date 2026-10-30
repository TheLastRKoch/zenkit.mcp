# Design

## Context

The scaffold from `bootstrap-mcp-server` provides a flat `src/` tree (`server.py`, `config.py`, `tools/zenkit.py`), environment-only configuration (`ZENKIT_API_KEY`, `ZENKIT_API_BASE_URL`, default `https://zenkit.com/api/v1`), and an offline test suite driven through FastMCP's in-memory `Client`. The only tool today is the credential-safe `zenkit_connection_status` placeholder.

The reference integration is `opentasks.service/src/services/zenkit.py`: a synchronous, `requests`-based class that reads the same two environment variables and calls the Zenkit REST API. `Zenkit.postman_collection.json` documents the endpoints (list, entries, columns, user) and the `Zenkit-API-Key` header; `create-entry-curl.txt` shows entry creation via `POST /lists/{listId}/entries` with a body of `{ "<elementUuid>_<dataType>": <value> }` pairs. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**

- A typed, async HTTP client owned by one module, so tools share auth, error mapping, and pagination instead of re-implementing them.
- Seven API-backed tools that map one-to-one onto the documented endpoints, each testable without network access.
- Preserve the existing secret-safety, per-invocation-config, and offline-test conventions.

**Non-Goals:**

- Entry update/delete/move, list or column management, OAuth, webhooks, retries with backoff, or response caching.
- A caching layer or a richer domain model beyond what the Zenkit API already returns.

## Decisions

### HTTP client: `httpx` (async)

Use `httpx` over `requests`. FastMCP 4 dispatches tools in an async event loop, and the in-memory `Client` runs that loop in tests; an async client avoids blocking the loop and gives `httpx.MockTransport` for deterministic, offline unit tests. `requests` (used by the reference service) is synchronous and offers no equivalent mock transport. The `httpx` version is pinned through `uv.lock`.

### One client module: `src/zenkit_api.py`

Add a top-level `ZenkitClient` in `src/zenkit_api.py`, consistent with the flat layout and the generic-name-collision guidance in `AGENTS.md` (a `zenkit_`-prefixed module is safer than a bare `api.py`). It owns the `Zenkit-API-Key` header, base-URL resolution, JSON encoding, error mapping, and pagination. Tools in `src/tools/zenkit.py` import and call it, so `server.py` wiring is unchanged.

### Client constructed per invocation, with injectable transport

Each tool builds its client from `Settings.from_env()` at call time (matching the existing "read config per tool invocation" rule). The client accepts an injected `httpx.AsyncClient`/transport so tests substitute a mock without touching the network. This keeps behavior consistent whether the server is a long-lived process or a fresh test client.

### Error mapping to tool errors

The client translates failures into `fastmcp.exceptions.ToolError` with actionable messages: a non-2xx response reports the endpoint and status (401/403 are phrased as credential problems), a malformed response reports an unexpected payload, and a timeout reports that Zenkit was unreachable. No stack traces, internal paths, or raw exception text reach the client. The API key is never interpolated into a message.

### Pagination contract

`zenkit_get_entries` calls `POST /lists/{listId}/entries/filter` with `limit`/`skip` (the same shape as the reference service) and accumulates pages until a short or empty page, with a bounded iteration cap to prevent runaway loops. The tool accepts optional `filter` (the Zenkit filter object passed through verbatim), `limit` (default 100), and `skip` (default 0).

### Entry and column representation

Zenkit keys entry fields by `{elementUuid}_{dataType}` (for example `c0148d60-…_text`). To stay faithful to the API and composable, entries are returned with `id`, `uuid`, and `fields` (the raw custom-column values); `zenkit_list_columns` returns each element's id, name, and data type so clients can resolve ids to human names. This avoids an extra round-trip inside every entry read and keeps `zenkit_create_entry` a direct passthrough of the documented body shape.

### Tool surface

Seven tools are registered in `tools/zenkit.py`'s `register(mcp)` alongside the existing placeholder:

- `zenkit_get_current_user` → `GET /users/me`
- `zenkit_list_lists` → `GET /users/me/workspacesWithLists`
- `zenkit_get_list(list_id)` → `GET /lists/{list_id}`
- `zenkit_list_columns(list_id)` → `GET /lists/{list_id}/elements`
- `zenkit_get_entries(list_id, filter=None, limit=100, skip=0)` → `POST /lists/{list_id}/entries/filter`
- `zenkit_get_entry(list_id, entry_id)` → `GET /lists/{list_id}/entries/{entry_id}`
- `zenkit_create_entry(list_id, fields)` → `POST /lists/{list_id}/entries`

Each tool has a docstring (FastMCP derives its description), typed parameters, and returns JSON-serializable data. A missing `ZENKIT_API_KEY` makes every API-backed tool raise a `ToolError` that names the variable, before any request is sent.

### Dependencies and documentation

`httpx` is added with `uv add httpx`. `README.md` documents the new tools and their parameters; `AGENTS.md` and `README.md` narrow the "real API calls are out of scope" note to the operations this change still excludes.

## Risks / Trade-offs

- **Zenkit API shape drift** → Tests pin behavior against mocked, documented responses; an upstream change fails the suite rather than silently corrupting output.
- **Secret leakage** → A test asserts the key never appears in results or logs; the client only ever sets the key as a header value.
- **Pagination runaway** → The loop stops on short/empty pages and is capped; the cap is surfaced as a tool error if exceeded.
- **Blocking the async loop** → All network I/O goes through `httpx` async calls; no synchronous `requests` calls are introduced.
- **Field-key opacity for clients** → `zenkit_list_columns` provides the id→name mapping; entries remain faithful to the API rather than guessing a normalized shape.

## Migration Plan

1. `uv add httpx` to update `pyproject.toml` and `uv.lock`.
2. Add `src/zenkit_api.py` with `ZenkitClient` (auth, error mapping, pagination, timeout).
3. Extend `src/tools/zenkit.py` with the seven tools and register them; leave `zenkit_connection_status` and `server.py` unchanged.
4. Add client tests (via `httpx.MockTransport`) and tool tests (via the in-memory `Client` with a mocked client), all offline.
5. Run `uv sync --locked`, `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest`.
6. Update `README.md` and `AGENTS.md`.
7. Rollback is `git checkout -- .` for tracked files plus removing the new untracked files; no data or deployment state is involved.
