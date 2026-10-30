# Tasks

## 1. Harden base URL validation

- [x] 1.1 Change `validate_api_base_url` in `src/config.py` to require the `https` scheme, comparing case-insensitively and returning the original value unchanged; verify with `uv run pytest tests/test_config.py`
- [x] 1.2 Make the `SettingsError` message name `ZENKIT_API_BASE_URL`, state that an HTTPS URL is required, show the HTTPS default as an example, and not echo the rejected value; verify the message by asserting the new rejection tests match `API_BASE_URL_ENV_VAR` and `https`

## 2. Cover the behavior with tests

- [x] 2.1 Extend the invalid-URL parametrization in `tests/test_config.py` with `http://zenkit.com/api/v1`, `http://127.0.0.1:8080/api/v1`, `http://localhost:8080/api/v1`, and a mixed-case `HtTp://...` value; verify `uv run pytest tests/test_config.py` passes
- [x] 2.2 Add an acceptance case for an uppercase `HTTPS://` base URL in `tests/test_config.py` and verify it is returned unchanged
- [x] 2.3 Add a tool-level test in `tests/test_tools.py` asserting `zenkit_connection_status` fails with a `ToolError` naming `ZENKIT_API_BASE_URL` when `ZENKIT_API_BASE_URL` is a plaintext URL; verify with `uv run pytest tests/test_tools.py -k connection_status`

## 3. Update documentation

- [x] 3.1 Update the `ZENKIT_API_BASE_URL` row in the README configuration table to require an absolute HTTPS URL, and update the troubleshooting entry that currently says "HTTP or HTTPS"; verify `grep -rn "HTTP or HTTPS" README.md` returns nothing
- [x] 3.2 Update the docstring of `validate_api_base_url` to describe the HTTPS-only contract; verify `uv run ruff check` passes

## 4. Integration verification

- [x] 4.1 Run `uv run pytest`, `uv run ruff check`, and `uv run ruff format --check` and confirm all pass
- [x] 4.2 Start the server with `ZENKIT_API_BASE_URL=http://example.test/api/v1` and confirm `zenkit_connection_status` reports the configuration error without contacting Zenkit

## Workflow follow-up

- Run the `version-bump` skill before opening the pull request; the plaintext rejection is a breaking change.
- Archive the change after review and merge.
