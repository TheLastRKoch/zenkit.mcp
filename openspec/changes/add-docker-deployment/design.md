# Design

## Context

See `proposal.md` for motivation and `specs/` for the behavioral contract.

Current state that shapes the approach:

- `src/server.py` builds the server with `FastMCP(name=..., version=..., instructions=...)` inside
  `create_server()` and launches it with `mcp.run(transport="http", host=..., port=..., show_banner=False)`.
- FastMCP is pinned to `>=4.1,<5` (installed: 4.1.3). In this version `run()` only forwards transport
  arguments; the HTTP app applies `self.auth`, so an auth provider must be attached when the `FastMCP`
  instance is constructed, not passed to `run()`.
- `fastmcp.server.auth.providers.jwt.StaticTokenVerifier` implements `AuthProvider` (via `TokenVerifier`) and
  validates bearer tokens against an in-memory mapping, returning `401` for unknown tokens.
- `src/config.py` owns environment parsing (`Settings`, `SettingsError`) and the project convention that
  rejected values are never echoed in errors.
- `pyproject.toml` declares `requires-python = ">=3.12"`, a `zenkit-mcp` console script, and a `uv.lock`
  that must be the source of truth for installed versions.

## Goals / Non-Goals

**Goals:**

- A reproducible image built from `uv.lock`, runnable by `docker compose up` with no Python knowledge.
- One obvious server endpoint: `http://<host>:9010/mcp`.
- Credentials supplied only at runtime, never in the image.
- Inbound authentication that a stock MCP client (n8n, VS Code, Copilot CLI) can satisfy with a static
  bearer token.

**Non-Goals:**

- OAuth 2.1 authorization-server discovery (the MCP spec's preferred model for shared servers). A single
  self-hosted operator with one token does not need dynamic registration or user consent.
- Multi-tenant tokens, rotation, expiry, or per-client scopes.
- TLS termination inside the container; a reverse proxy owns that if the deployment needs HTTPS.
- Publishing an image to a registry, CI pipelines, and Kubernetes manifests.

## Decisions

### Static bearer token via `ZENKIT_MCP_AUTH_TOKEN`

Parse the token in `config.py` next to the existing settings and pass
`StaticTokenVerifier(tokens={token: {"client_id": "zenkit-mcp", "scopes": []}})` to `FastMCP(auth=...)`
through a new `create_server(auth=...)` parameter.

- *Why not OAuth?* It requires an authorization server and discovery endpoints; the deployment target is a
  single compose stack behind a private network. OAuth is a larger, separate change.
- *Why not a reverse proxy with basic auth?* It adds a second moving part and still needs a static secret;
  it does not reduce the secret-management work.
- *Why not `DebugTokenVerifier`?* It is intended for tests and does not model a real token check.
- *Accepted caveat:* upstream documents `StaticTokenVerifier` as development-oriented because tokens live in
  memory in plaintext and do not expire. For one long random token in a self-hosted container this is an
  acceptable trade-off; it is documented in `README.md` and revisited when OAuth becomes necessary.

### Startup guard instead of silent exposure

`main()` rejects `--transport http` on a non-loopback host when the token is missing, exiting with a
non-zero status and a message naming the variable only.

- *Why not warn and continue?* A warning in a container log is easy to miss and leaves the write path open.
- *Why not default to loopback and require an opt-in flag?* The container must bind `0.0.0.0`; a flag that
  only exists to be set in the Dockerfile adds ceremony without adding safety.
- Host classification treats `127.0.0.1`, `::1`, and `localhost` as loopback; everything else, including
  `0.0.0.0` and `::`, requires a token.
- This is the change's only breaking behavior; it is called out in the proposal and `README.md`.

### Image built with a verified lock file and run unprivileged

A multi-stage build on `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`: the builder installs runtime
dependencies with `uv sync --locked --no-dev --no-install-project`, then the runtime stage copies the
virtual environment and `src/`, installs the project, and drops to a fixed unprivileged uid.

- `--locked` makes the build fail when `uv.lock` does not match `pyproject.toml`, matching the repository's
  `uv lock --check` rule instead of silently installing a stale resolution.
- Dependencies and source are copied as separate layers so source edits do not reinstall packages.
- `PYTHONUNBUFFERED=1` keeps logs immediate; the server already logs to stderr only.
- No `ARG` or `ENV` carries a credential, satisfying the image-content requirement.
- `.dockerignore` excludes `.venv`, `.git`, `tests`, `openspec`, caches, and `.env` so they cannot leak into
  layers and the context stays small.

### Default command serves Streamable HTTP on 9010

`ENTRYPOINT ["zenkit-mcp"]` with `CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "9010"]`.

- Keeping the arguments in `CMD` rather than `ENTRYPOINT` lets operators override the port or switch to
  stdio (`docker run ... zenkit-mcp`) without rebuilding.
- The CLI default of `8000` stays unchanged so local usage is unaffected.

### Compose contract

`docker-compose.yml` declares one service, publishes `9010:9010`, requires
`${ZENKIT_API_KEY:?}` and `${ZENKIT_MCP_AUTH_TOKEN:?}`, sets `restart: unless-stopped`, and healthchecks
with a TCP connect to `127.0.0.1:9010`.

- The `:?` form makes compose fail before creating the container and names the missing variable, which is the
  behavior the spec requires; it also prevents an accidental anonymous deployment.
- A TCP check avoids adding a health endpoint to the server and works even though `/mcp` rejects unauthenticated
  probes. It proves the listener is up, not that the token is valid — the tests cover token validation.
- Compose reads `.env` automatically; the application does not, preserving the existing no-dotenv convention.

### Keep FastMCP's Host/Origin protection at its default

- DNS-rebinding protection is not enabled explicitly. With a bearer token required, a rebinding request
  without the token is rejected; enabling it would require hard-coding an allowlist of container hostnames,
  which the compose file cannot know.

## Risks / Trade-offs

- **Token in `.env` or shell history** → document generating it with `openssl rand -hex 32`, keep `.env`
  git-ignored, and never print it in logs or errors.
- **Publishing `9010` on all host interfaces** → the bearer token is the only barrier; restrict the host
  firewall or bind `127.0.0.1:9010` when a reverse proxy or local-only client is used. Called out in the
  README as the recommended tightening.
- **`StaticTokenVerifier` is upstream-flagged for development** → single static secret, constant operational
  cost; migrate to OAuth 2.1 when per-client identity or rotation is needed.
- **Building from `uv.lock` can drift from `pyproject.toml`** → the image build runs `uv sync --locked`, so a
  stale lock fails the build instead of installing a resolution that no longer matches the manifest.
- **Healthcheck proves liveness only, not correctness** → deployment docs include a `curl` check against
  `/mcp` with the token for post-start verification.
- **Breaking change for anyone binding `0.0.0.0` today** → release notes and README call out the new
  requirement; rollback is reverting the guard.

## Migration Plan

1. Deploy the new image or compose stack with `ZENKIT_API_KEY` and `ZENKIT_MCP_AUTH_TOKEN` present.
2. Update MCP clients to send `Authorization: Bearer <token>`; clients that fail now return `401` instead of
   silently working.
3. Verify with a request to `http://<host>:9010/mcp` using the token.
4. Rollback: redeploy the previous image tag or revert `Dockerfile`/`docker-compose.yml`; stdio deployments
   need no action at any point.

## Open Questions

- Whether the compose file should later carry an `n8n` service on the same network as a convenience for the
  primary use case. Deferrable: it does not change the server's behavior or the specs.
