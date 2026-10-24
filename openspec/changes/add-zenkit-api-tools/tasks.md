# Tasks

## 1. HTTP client foundation

- [ ] 1.1 Add `httpx` as a runtime dependency with `uv add httpx`; verify `uv lock --check` exits 0 and `pyproject.toml` lists `httpx` under `dependencies`
- [ ] 1.2 Implement `ZenkitClient` in `src/zenkit_api.py` (build from `Settings.from_env()`, `Zenkit-API-Key` header, base-URL resolution, missing-key guard, HTTP error → `ToolError` mapping, bounded timeout); verify `uv run pytest tests/test_zenkit_api.py` passes the client unit tests using `httpx.MockTransport`
- [ ] 1.3 Implement entry-list pagination (accumulate pages until a short/empty page, with an iteration cap); verify a pagination test that returns 2 pages assembles them in order
- [ ] 1.4 Add a test asserting the configured API key never appears in client results, errors, or captured logs; verify it passes

## 2. Read tools

- [ ] 2.1 Implement and register `zenkit_get_current_user` (`GET /users/me`); verify an in-memory `Client` test returns the user for valid credentials and a `ToolError` for a 401
- [ ] 2.2 Implement and register `zenkit_list_lists` (`GET /users/me/workspacesWithLists`) and `zenkit_get_list` (`GET /lists/{list_id}`); verify tests cover accessible lists and an unknown-list `ToolError`
- [ ] 2.3 Implement and register `zenkit_list_columns` (`GET /lists/{list_id}/elements`); verify a test asserts each column carries an identifier, name, and data type
- [ ] 2.4 Implement and register `zenkit_get_entries` (`POST /lists/{list_id}/entries/filter`) and `zenkit_get_entry` (`GET /lists/{list_id}/entries/{entry_id}`); verify tests cover filter/pagination, empty lists, and single-entry lookup
- [ ] 2.5 Add a discovery test asserting all seven new tools are listed with descriptions and input schemas; verify `uv run pytest tests/test_tools.py` passes

## 3. Write tool

- [ ] 3.1 Implement and register `zenkit_create_entry` (`POST /lists/{list_id}/entries` with a `fields` mapping); verify a test asserts the posted body matches the documented `{ "<uuid>_<dataType>": <value> }` shape and returns the created entry id

## 4. Documentation

- [ ] 4.1 Document the new tools, their parameters, and configuration in `README.md`; verify every documented `uv run` command executes as written
- [ ] 4.2 Narrow the "real API calls are out of scope" note in `README.md` and `AGENTS.md` to the operations this change still excludes (update/delete/move, list and column management, OAuth); verify the wording matches the specs' non-goals

## 5. End-to-end verification

- [ ] 5.1 Run `uv sync --locked`, `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest` from a clean environment; verify all exit 0 with no Zenkit credentials and no network access
- [ ] 5.2 Confirm the server still starts and imports with no credentials or network (existing `zenkit_connection_status` and server-discovery tests pass); verify no new outbound call happens at import or startup

## Workflow follow-up

- Archive the change after review and once the spec deltas are synced.
- The `bootstrap-mcp-server` change is still in flight; archive it (or sync its specs) first so the `zenkit-tools` capability exists in the main specs before this change's delta is applied.
