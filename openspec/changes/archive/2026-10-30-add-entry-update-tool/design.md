# Design

## Context

See `proposal.md` for motivation. The current `src/zenkit_api.py` client exposes GET, POST, and a paged
`list_entries` helper; `src/tools/zenkit.py` maps tools onto those calls and projects entries through
`_entry_result` (id, uuid, custom fields). Entry update was explicitly excluded in `add-zenkit-api-tools`,
and both `README.md` and `AGENTS.md` still list it as out of scope.

Zenkit keys custom column values as `{elementUuid}_{dataType}`; date elements additionally expose
`{elementUuid}_date`, `_endDate`, `_hasTime`, and `_duration` keys, so a timed slot is written by sending
all three of date, hasTime, and endDate in one payload.

## Goals / Non-Goals

**Goals:**

- One write path for existing entries that reuses the client's authentication, timeout, and error mapping.
- Keep the tool a faithful passthrough of Zenkit's key/value shape, matching `zenkit_create_entry`.
- Offline, deterministic tests that assert the outgoing request and the projected result.

**Non-Goals:**

- Delete, move, or copy operations; bulk updates; list or column management.
- Client-side schema validation of element ids or data types beyond rejecting an empty update.
- Conflict detection, scheduling logic, or timezone conversion inside the server — clients decide values.

## Decisions

### Endpoint: `PUT /lists/{listId}/entries/{entryId}`

The client already writes with `POST /lists/{listId}/entries` and reads with
`GET /lists/{listId}/entries/{entryId}`, so the entry resource path is known and REST-consistent.
Send the field mapping as the JSON body, identical in shape to creation. Zenkit's public docs are not
reachable, so the method was verified against the live API with a no-op update: re-sending all 29 custom
fields of a Work entry returned `200` and left every field unchanged. If a future API revision answers
`405 Method Not Allowed`, switch the client method to `PATCH` without changing the tool contract.

### Response projection: reuse `_entry_result`

Zenkit returns the updated entry. Projecting it through the existing `_entry_result` helper keeps the result
shape identical to `zenkit_get_entry`, so clients can diff before/after without a second read.

### Validation: require a non-empty mapping, otherwise pass through

`zenkit_create_entry` already accepts raw field keys; consistency argues against adding element-id validation
that would need a column lookup per call. The one guard worth adding is rejecting an empty `fields` mapping
before any request, because an empty update is a client bug that would otherwise look successful.

### Partial updates

Only supplied keys are sent, so columns absent from the payload keep their current values. Clearing a value
is expressed by sending `null`, matching Zenkit's own representation.

### Testing strategy

`httpx.MockTransport` asserts the method, path, and JSON body of the update, plus the projection of the
response and the mapping of `404`/`4xx` to `ToolError`. Tool-level tests use FastMCP's in-memory client with
the mocked transport injected through the existing fixture pattern; a missing-key test asserts the
`ZENKIT_API_KEY` guidance without network access.

### Documentation

`README.md` gains a row in the tool table plus a short note that scheduling a timed entry requires date,
hasTime, and endDate together. The out-of-scope lists in `README.md` and `AGENTS.md` drop "entry update"
while keeping delete/move/copy and list/column management excluded.

## Risks / Trade-offs

- **Unverified upstream method** → Verify with a no-op update during implementation; fall back to `PATCH`
  if Zenkit rejects `PUT` with `405`.
- **Accidental broad writes** → The tool only touches keys the caller supplies; tests pin the exact body.
- **Silent typos in field keys** → Zenkit ignores unknown keys; documented, and out of scope for validation.
- **Write operations in tests** → All tests use `MockTransport`; the suite never contacts Zenkit.

## Migration Plan

1. Add `update_entry` to `ZenkitClient` and verify the method against the live API with a no-op update.
2. Add `zenkit_update_entry` and register it in `tools/zenkit.py`.
3. Add offline tests for the client and the tool.
4. Update `README.md` and `AGENTS.md` scope notes and tool documentation.
5. Run `uv run pytest`, `uv run ruff check`, and `uv run ruff format --check`.

Rollback is removing the tool and client method; no stored state or configuration changes.
