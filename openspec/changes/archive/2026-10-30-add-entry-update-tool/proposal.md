# Proposal

## Why

The server can read entries and create new ones, but it cannot change an existing entry. Plans that need
edits — rescheduling a task to a concrete time, correcting a due date, updating a workload — force clients
to leave the MCP tool surface and call the Zenkit API directly. Adding a single update tool closes that gap
while keeping authentication, error mapping, and secret handling in one place.

## What Changes

- Add a `zenkit_update_entry` tool that updates custom column values on an existing entry and returns the
  updated entry's `id`, `uuid`, and `fields`.
- Add `ZenkitClient.update_entry(list_id, entry_id, fields)` to the shared HTTP client so the tool reuses the
  existing auth header, timeout, and error mapping.
- Validate that at least one field is supplied, so an empty call fails loudly instead of silently doing nothing.
- Document how to schedule a dated task (set the date value, `hasTime`, and `endDate` together) in `README.md`.
- Update the scope notes in `README.md` and `AGENTS.md`, which currently list entry update as out of scope.
- Add offline tests through `httpx.MockTransport` and FastMCP's in-memory client.

No existing tool changes behavior, and no breaking changes are introduced.

## Capabilities

### New Capabilities

- `zenkit-tools`: adds the `zenkit_update_entry` requirement to the tool surface.
- `zenkit-api-client`: adds the write-path requirement for updating an entry through the shared client.

### Modified Capabilities

None.

## Impact

- `src/zenkit_api.py`: new `update_entry` method on `ZenkitClient`.
- `src/tools/zenkit.py`: new tool plus registration.
- `tests/test_zenkit_api.py`, `tests/test_tools.py`: offline coverage for the new method and tool.
- `README.md`, `AGENTS.md`: tool documentation and narrowed out-of-scope notes.
- Dependencies and configuration are unchanged; no new environment variables.
