# Tasks

## 1. Client update path

- [x] 1.1 Add `ZenkitClient.update_entry(list_id, entry_id, fields)` in `src/zenkit_api.py`, sending the field mapping to the entry resource and returning the decoded payload; verify with `httpx.MockTransport` assertions on method, path, and body in `tests/test_zenkit_api.py`
- [x] 1.2 Verify the upstream method against the live API with a no-op update (re-send an entry's current values, then read it back and confirm the values are unchanged); record the observed method in the design's endpoint decision and switch to `PATCH` if Zenkit answers `405`
- [x] 1.3 Cover client error paths in `tests/test_zenkit_api.py`: `404` maps to a missing-resource tool error, rejected credentials name the credentials problem, and no error message contains the API key; verify with `uv run pytest tests/test_zenkit_api.py -q`

## 2. Update tool

- [x] 2.1 Implement `zenkit_update_entry(list_id, entry_id, fields)` in `src/tools/zenkit.py` with a docstring, an empty-`fields` guard that raises `ToolError` before any request, and `_entry_result` projection; register it in `register(mcp)`; verify the tool appears in `client.list_tools()` through FastMCP's in-memory client
- [x] 2.2 Add offline tool tests in `tests/test_tools.py` for a successful update, the empty-`fields` rejection, and the missing-`ZENKIT_API_KEY` guidance; verify with `uv run pytest tests/test_tools.py -q`
- [x] 2.3 Document the tool in the `README.md` tool table and add a note that a timed slot is written by sending the date value, its `hasTime` flag, and its `endDate` together; remove entry update from the out-of-scope lists in `README.md` and `AGENTS.md`; verify by re-reading the three edited sections

## 3. Integration checks

- [x] 3.1 Run `uv run pytest`, `uv run ruff check`, and `uv run ruff format --check`; all must pass with no network access required
- [x] 3.2 Confirm the documented contract end to end by updating one real entry's due date through the registered tool and reading it back with `zenkit_get_entry`; confirm the field values match what was sent
