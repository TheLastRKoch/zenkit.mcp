# Proposal

## Why

`Settings.from_env()` accepts `ZENKIT_API_BASE_URL` values with either an `http` or an `https`
scheme. Because every API request attaches the `Zenkit-API-Key` header, an operator who points the
server at a plaintext base URL transmits the API key in cleartext where it can be read or modified
in transit. A security audit rated this a medium-severity finding.

## What Changes

- **BREAKING** — `validate_api_base_url` rejects base URLs whose scheme is not `https`, raising
  `SettingsError` with an actionable message that names `ZENKIT_API_BASE_URL`.
- The default base URL (`https://zenkit.com/api/v1`) continues to work unchanged; only explicit
  plaintext overrides are rejected.
- HTTP is rejected even for loopback hosts; no cleartext exception is added.
- README and tool documentation state that `ZENKIT_API_BASE_URL` must be an absolute HTTPS URL.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `zenkit-api-client`: the requirement that requests target the configured base URL is extended so
  that the API access layer only transmits credentials over HTTPS and rejects non-HTTPS base URLs.

## Impact

- `src/config.py`: `validate_api_base_url` and the error message text.
- `tests/test_config.py`: invalid-URL cases gain plaintext overrides; the accepted-override case
  stays HTTPS.
- `README.md`: the `ZENKIT_API_BASE_URL` environment variable table row and troubleshooting text.
- Operators using an `http://` base URL, including local proxies, must switch to `https://` or to a
  TLS-terminating endpoint. No credentials, dependencies, or tool signatures change.
