# Design

## Context

See `proposal.md` — Why. The current state that shapes the approach:

- `src/config.py` owns `Settings.from_env()` and `validate_api_base_url()`. The validator accepts
  any absolute URL whose scheme is `http` or `https` and whose host is non-empty.
- `Settings.from_env()` runs per tool invocation (`src/tools/zenkit.py`,
  `src/zenkit_api.py`), and both call sites already convert `SettingsError` into a
  `fastmcp.exceptions.ToolError`, so a stricter validator propagates without new error plumbing.
- Tests exercise `validate_api_base_url` directly (`tests/test_config.py`) and through
  `Client.call_tool` (`tests/test_tools.py`).

## Goals / Non-Goals

**Goals:**

- Guarantee that the `Zenkit-API-Key` header can only ever be sent over TLS.
- Reject a plaintext `ZENKIT_API_BASE_URL` before any request is built, with a message an operator
  can act on.
- Keep the default and all existing HTTPS deployments working with no code change.

**Non-Goals:**

- TLS certificate pinning, custom CA bundles, or proxy configuration.
- Detecting or repairing an insecure deployment that already leaked a key.
- Adding an opt-in cleartext escape hatch for loopback or test hosts.

## Decisions

**Reject `http` in the validator rather than warn.** The audit offered HTTPS-only enforcement or a
warning. A warning still transmits the key in cleartext, and the server cannot verify that the
operator saw it, so enforcement is the only outcome that satisfies the security guarantee. This is
a breaking change for operators using plaintext URLs, which the proposal marks explicitly.
Alternative rejected: warn-and-continue; it leaves the credential exposed by default.

**No loopback exception.** A loopback exception would keep local test proxies usable, but it also
reintroduces a code path where the scheme check depends on host parsing, and a mistaken host value
(misconfigured DNS, container networking) silently reopens the exposure. Tests already stub HTTP
with `httpx.MockTransport`, so they need no real endpoint. Alternative rejected: allow `http` for
`127.0.0.1`/`localhost`/`::1`.

**Keep the check in `validate_api_base_url`.** Validation stays centralized where the URL is
constructed from the environment, so every consumer — tools, client, and connection status —
inherits it. Alternative rejected: validating inside `ZenkitClient`, which would let other future
consumers bypass it.

**Compare the scheme case-insensitively.** `urlsplit` preserves the scheme's case. Lowercasing
before comparison keeps `HTTPS://` working instead of rejecting it as an unknown scheme, while
still rejecting `http` in any casing. The original value is returned unchanged, preserving the
operator's configured URL for request resolution.

**Message shape.** The error names `ZENKIT_API_BASE_URL`, states that an HTTPS URL is required, and
shows the HTTPS default as an example. It must not include the rejected value, because an operator
may have embedded credentials in it.

## Risks / Trade-offs

- **Breaking change for plaintext deployments** → Documented in the README and in the proposal;
  the error message tells the operator exactly which variable to fix. Rollback is reverting the
  validator and README change.
- **Local development against a plaintext mock server stops working through the environment** →
  Tests use an injected `httpx.MockTransport`; developers needing a local endpoint run it behind
  TLS. No production workaround is added, by design.
- **Operators may set an `https` URL that redirects to `http`** → Out of scope; `httpx` follows
  redirects, but this change only governs the configured base URL. Noted rather than partially
  mitigated, to avoid scope creep.
- **Case-sensitivity assumptions about `urlsplit`** → Covered by parametrized tests for uppercase
  and mixed-case schemes.

## Migration Plan

1. Deploy the stricter validator with the README update.
2. Operators who set an `http://` base URL receive a `ToolError` naming
   `ZENKIT_API_BASE_URL` on the first API-backed call or on `zenkit_connection_status`; they change
   the value to an `https://` endpoint and restart or reconnect.
3. No data migration or dependency change is required. Rollback is reverting the commit.
