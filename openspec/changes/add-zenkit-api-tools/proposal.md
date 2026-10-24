# Proposal

## Why

The repository currently ships only a credential-safe placeholder tool, `zenkit_connection_status`, so agents cannot actually read or create Zenkit work. Real project-management value comes from Zenkit's core objects — **lists** (containers that group and sort entries) and **entries** (task-like objects with a title, due date, description, and arbitrary custom columns). A rudimentary reference already exists in the sibling `opentasks.service` project (`src/services/zenkit.py`), but it is a monolithic, JMESPath-string-driven module coupled to that application. Porting its capabilities into `zenkit.mcp` as clean, typed MCP tools gives agents first-class, reusable access to Zenkit.

## What Changes

- Add a typed Zenkit HTTP client module (`src/zenkit_api.py`) that sends the `Zenkit-API-Key` header, targets `ZENKIT_API_BASE_URL`, maps HTTP/JSON failures to tool errors, and paginates result lists.
- Add API-backed tools in `src/tools/zenkit.py`:
  - `zenkit_get_current_user` — validate credentials and return the authenticated user.
  - `zenkit_list_lists` — list the lists (workspaces → lists) the user can access.
  - `zenkit_get_list` — fetch a single list by id.
  - `zenkit_list_columns` — fetch a list's custom columns (Zenkit "elements").
  - `zenkit_get_entries` — fetch entries in a list, with optional filtering and `limit`/`skip` pagination.
  - `zenkit_get_entry` — fetch a single entry by id.
  - `zenkit_create_entry` — create an entry in a list with custom column values.
- Add `httpx` as a runtime dependency for async HTTP requests.
- Extend `tests/` to cover the client (mocked transport) and the tools (in-memory FastMCP client plus mocked HTTP), preserving the offline, credential-free test strategy.
- Update `README.md` and `AGENTS.md` to document the new tools and narrow the "real API calls are out of scope" note to cover only the operations this change does not add.

## Capabilities

### New Capabilities

- `zenkit-api-client`: The typed HTTP client that authenticates to the Zenkit REST API and owns base-URL handling, request headers, error mapping, pagination, and secret safety.

### Modified Capabilities

- `zenkit-tools`: Adds the API-backed tool surface (list, entry, and custom-column read operations plus entry creation) on top of the existing `zenkit_connection_status` tool.

## Impact

- **Code**: New `src/zenkit_api.py` client; extended `src/tools/zenkit.py` and its `register()`; new client and tool tests under `tests/`.
- **Dependencies**: Adds runtime dependency `httpx`; no change to `fastmcp` or dev dependencies.
- **Configuration**: Reuses existing `ZENKIT_API_KEY` and `ZENKIT_API_BASE_URL` (default `https://zenkit.com/api/v1`). No new environment variables are introduced.
- **Documentation**: `README.md` gains tool and environment documentation; `AGENTS.md` and `README.md` scope notes are updated.
- **Out of scope**: Updating, deleting, moving, or copying entries; creating/renaming lists and columns; OAuth flows; webhooks; and CI pipelines. These remain future changes.
