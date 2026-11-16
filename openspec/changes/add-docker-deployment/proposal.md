# Proposal

## Why

The server can already be launched over Streamable HTTP, but there is no supported way to run it as a
long-lived service. There is no container image and no compose file, so hosting it for a workflow engine
means hand-assembling a Python environment and a launch command. More importantly, the HTTP endpoint has no
inbound authentication: any process that can reach the port exercises the full authority of
`ZENKIT_API_KEY`, including entry creation and updates. Packaging the server for a shared host without fixing
that would turn a local developer tool into an unauthenticated write path into Zenkit.

## What Changes

- Add a multi-stage `Dockerfile` that builds the server from the lock file, runs as a non-root user, bakes no
  credentials into any layer, and defaults to serving Streamable HTTP on `0.0.0.0:9010`.
- Add a `.dockerignore` so the build context excludes virtual environments, git metadata, tests, and local
  configuration.
- Add a `docker-compose.yml` that publishes port `9010`, passes `ZENKIT_API_KEY` and the new
  `ZENKIT_MCP_AUTH_TOKEN` through from the environment, fails to start when either is unset, and includes a
  healthcheck and restart policy.
- Add inbound bearer-token authentication: when `ZENKIT_MCP_AUTH_TOKEN` is set, HTTP requests must carry
  `Authorization: Bearer <token>` and are rejected otherwise.
- Refuse to start HTTP mode on a non-loopback host when no token is configured, so an exposed port is never
  silently unauthenticated.
- Document the image build, compose usage, token generation, and client wiring (including n8n's MCP Client
  Tool) in `README.md`, and record the new environment variable in the configuration table.
- Narrow the out-of-scope notes in `README.md` and `AGENTS.md`, which currently exclude deployment artifacts.
- Add offline tests for the new configuration and startup guard.

**BREAKING**: starting the server with `--transport http --host <non-loopback address>` and no
`ZENKIT_MCP_AUTH_TOKEN` now exits with a non-zero status instead of serving unauthenticated. Stdio mode and
loopback HTTP are unchanged.

## Capabilities

### New Capabilities

- `container-deployment`: how the server is packaged and run as a container service — image contents,
  non-root user, default transport, port, environment contract, and compose exposure.

### Modified Capabilities

- `mcp-server-runtime`: the Streamable HTTP transport requirement gains inbound bearer-token authentication
  and a startup guard that rejects unauthenticated non-loopback binding.

## Impact

- New files: `Dockerfile`, `.dockerignore`, `docker-compose.yml`.
- `src/config.py`: `ZENKIT_MCP_AUTH_TOKEN` parsing alongside the existing settings.
- `src/server.py`: auth provider wiring for `create_server()` and the non-loopback startup guard.
- `tests/test_config.py`, `tests/test_server.py`: offline coverage for token parsing, startup rejection, and
  rejected HTTP requests.
- `README.md`, `AGENTS.md`: container usage, token handling, and revised scope notes.
- No new runtime dependency: `fastmcp>=4.1` already provides the static bearer-token verifier. No change to
  Zenkit API calls or the tool surface.
