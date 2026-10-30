# Tasks

## 1. Credential redaction in the current-user tool

- [x] 1.1 Add a redaction helper in `src/tools/zenkit.py` that projects a user payload onto the documented identity fields and recursively drops keys whose normalized name matches `key`, `apikey`, `api_key`, `token`, `secret`, or `password`; verify with unit-level assertions that a payload containing `api_key` and a nested `refreshToken` yields neither key
- [x] 1.2 Apply the helper in `zenkit_get_current_user` and keep the returned shape a flat identity mapping; verify an in-memory `Client` test whose mocked `/users/me` payload contains `api_key` returns id and display name and no key value
- [x] 1.3 Document the current-user result projection in `README.md` (supported identity fields, credential fields never returned); verify the documented field list matches the helper's allowlist

## 2. Derived column data type

- [x] 2.1 Add `_column_data_type(element)` in `src/tools/zenkit.py` that returns a non-empty `dataType` when present and otherwise selects a value-type key from `businessData` using the fixed precedence `text`, `date`, `categories`, `persons`, `files`, `number`, `references`, `link`, `checked`, excluding helper keys; verify tests cover every observed shape and that an empty `businessData` yields `null`
- [x] 2.2 Use the helper for `data_type` in `zenkit_list_columns`, leaving `id`, `uuid`, `name`, and `resource_role` unchanged; verify an in-memory `Client` test with `dataType: null` elements reports `text`, `date`, `categories`, `persons`, `files`, `number`, and `references` as applicable
- [x] 2.3 Assert the derived type matches the suffix of the entry field key in a test that lists columns and then reads entries from the same mocked list; verify the assertion passes
- [x] 2.4 Update the `README.md` tool table and column guidance to state that `data_type` is derived from the element definition and that system columns without a value type report `null`; verify the wording matches the spec scenarios

## 3. Integration verification

- [x] 3.1 Run `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest` from a clean shell with no Zenkit credentials; verify all exit 0 and the suite stays offline
- [x] 3.2 Confirm `zenkit_connection_status` and the other tools are unchanged in discovery output (names, descriptions, input schemas); verify `uv run pytest tests/test_tools.py` passes

## Workflow follow-up

- Archive the change after review; the `zenkit-tools` main spec does not exist yet, so archive or sync `bootstrap-mcp-server` and `add-zenkit-api-tools` first and confirm this delta applies on top of their requirements.
- Verify the archived spec retains both MODIFIED requirements with all scenarios.
