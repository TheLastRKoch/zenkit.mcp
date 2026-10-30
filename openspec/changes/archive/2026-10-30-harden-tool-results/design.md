# Design

## Context

See `proposal.md` for motivation. Today `zenkit_get_current_user` returns the decoded `GET /users/me` payload unchanged, and `zenkit_list_columns` maps `zenkit_list_columns.data_type` straight from the element's `dataType`. Verified against the live API (2026-10-30):

- `/users/me` includes a populated `api_key` field alongside identity fields (`id`, `username`, `displayname`, `fullname`, `emails`, `imageLink`, timestamps, organization and experiment metadata).
- `/lists/{id}/elements` returns `dataType: null` for every element. The value type is instead implied by the keys inside `businessData`: `{text, searchText, textType}` for text and notes, `{date, endDate, hasTime, duration}` for dates, `{categories, categories_sort}` for stages and labels, `{persons, persons_sort}` for assignments, `{files, filesData}` for attachments, `{number, numberText}` for numbers, `{connected, references, parents, path, sortOrder}` for subitems and dependencies, and `{}` for system columns such as Created and Last Updated.

The entry field keys returned by `zenkit_get_entries` use the same vocabulary as the value-type key (for example `190a37b0-…_date`), which is why the column type must align with it.

## Goals / Non-Goals

**Goals:**

- Guarantee that no credential-bearing field from an upstream payload reaches a tool result, even if Zenkit adds new ones.
- Make `data_type` useful: callers must be able to build entry field keys from a column without guessing.
- Keep the rest of both tool payloads stable so existing callers and tests continue to work.

**Non-Goals:**

- Changing the HTTP client, error mapping, filters, or pagination.
- Normalizing entry values into a typed domain model.
- Adding new tools or new configuration.

## Decisions

### Curated identity projection for the current-user tool

Return an explicit allowlist of identity fields (`id`, `uuid`, `username`, `displayname`, `fullname`, `emails`, `imageLink`, `created_at`, `last_login`, `last_seen`, `organizationId`) instead of the raw payload. An allowlist is chosen over a denylist because the failure mode of a denylist is silent credential disclosure when Zenkit renames or adds a field, whereas an allowlist fails closed. Unknown or future identity fields are dropped until someone deliberately adds them.

A defense-in-depth scrub runs over the projected value as well: any mapping key whose normalized form matches `key`, `apikey`, `api_key`, `token`, `secret`, or `password` is removed, recursively through nested mappings and lists. This is redundant for today's payload but protects the projection if someone later widens it.

Alternative considered: keep the full payload and drop only `api_key`. Rejected — it fixes today's symptom while leaving the tool one upstream field away from leaking again.

### Shared redaction helper

Both the allowlist and the recursive scrub live in one small helper in `src/tools/zenkit.py` so any future tool that surfaces user or organization payloads can reuse it. It operates on the decoded JSON already in memory; no client changes are needed.

### Derive `data_type` from `businessData` with a fixed precedence

`_column_data_type(element)` returns the element's `dataType` when it is a non-empty string, otherwise inspects `businessData` and returns the first key from a fixed precedence list:

`text`, `date`, `categories`, `persons`, `files`, `number`, `references`, `link`, `checked`

Helper keys (`searchText`, `textType`, `*_sort`, `filesData`, `numberText`, `endDate`, `hasTime`, `duration`, `connected`, `parents`, `path`, `sortOrder`, `milestone`, `tags`) are never candidates. An element whose `businessData` is empty or contains no candidate key reports `null`, matching the spec's "do not guess" scenario.

Precedence, not "first key in the mapping", because JSON object order is not contractual. A fixed order also keeps the result deterministic across responses.

Alternative considered: infer the type from an existing entry's field-key suffixes. Rejected — it requires an extra entry fetch per column listing and fails for empty lists.

### Payload stability

`zenkit_list_columns` keeps `id`, `uuid`, `name`, `resource_role`; only `data_type` changes from `null` to a derived string. `zenkit_get_current_user` keeps a flat mapping of identity fields; only credential-bearing keys disappear. No shared helper changes the shape of `zenkit_get_entries`, `zenkit_get_entry`, or `zenkit_create_entry`, because entry payloads carry custom-column values rather than account credentials.

## Risks / Trade-offs

- **Dropped identity fields** → Clients that relied on an unmapped field lose it. Mitigation: the projection documents the supported identity fields in `README.md`; adding one is a one-line change.
- **Type vocabulary drift** → If Zenkit introduces a new value type, the precedence list reports `null` instead of the new key. Mitigation: the fallback is safe (no wrong guesses), and the mapping is covered by a test that mirrors the observed `businessData` shapes.
- **Scrub false positives** → A legitimate field named e.g. `tokenCount` would be removed. Mitigation: the scrub applies only to the current-user projection, whose allowlist contains no such field.
- **Spec/tool mismatch for system columns** → System columns legitimately have no value type; the spec's "do not guess" scenario records that a `null` result is correct rather than a defect.

## Migration Plan

1. Add the redaction helper and apply it in `zenkit_get_current_user`.
2. Add `_column_data_type` and use it in `zenkit_list_columns`.
3. Extend `tests/test_tools.py`: a user payload containing `api_key` (plus a nested credential-looking key) must not appear in the result; element payloads with `dataType: null` and each observed `businessData` shape must map to the expected type; an empty `businessData` must yield `null`.
4. Update `README.md` to describe the current-user projection and the meaning of `data_type`.
5. Verify with `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest`; no lock-file or dependency changes are involved.
6. Rollback is `git checkout -- src/tools/zenkit.py tests/test_tools.py README.md` for the implementation commit.
