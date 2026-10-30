# Proposal

## Why

Two defects surface only against the real Zenkit API. `zenkit_get_current_user` returns Zenkit's `/users/me` payload verbatim, and that payload includes the caller's `api_key` field, so the server's own credential is echoed back into MCP tool results and client transcripts — directly contradicting the repository rule that secrets never leave results or logs. Separately, `zenkit_list_columns` reports `data_type` from the element's `dataType` field, which Zenkit returns as `null` for every element; the real type discriminator is the key inside `businessData`, so the tool currently reports `null` for every column and clients cannot map columns to the `<element-uuid>_<type>` keys that entry tools use.

## What Changes

- Redact credential-bearing fields from `zenkit_get_current_user` results. The tool keeps returning the authenticated user's identity (id, display name, username, email) but never returns `api_key` or any other secret-typed field, regardless of what Zenkit includes in the payload.
- Derive `data_type` in `zenkit_list_columns` from the element's `businessData` keys when Zenkit returns `dataType: null`, so each column reports a usable type (`text`, `date`, `categories`, `persons`, `files`, `number`, `references`, and so on) that corresponds to the entry field-key suffix.
- Keep the column's raw Zenkit identifiers (`id`, `uuid`, `name`, `resource_role`) unchanged so existing callers are unaffected apart from `data_type` becoming populated.
- Add regression tests for both behaviors and update the documentation that describes the current-user result and the column `data_type`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `zenkit-tools`: The `zenkit_get_current_user` requirement gains a credential-redaction guarantee, and the `zenkit_list_columns` requirement changes from "reports the element's data type" to "reports a data type that is derived from the element definition and matches the entry field-key suffix".

## Impact

- **Code**: `src/tools/zenkit.py` (`zenkit_get_current_user`, `zenkit_list_columns`, plus a small shared helper for the two transformations).
- **Tests**: `tests/test_tools.py` gains cases for a payload containing `api_key` and for elements whose `dataType` is `null` with typed `businessData`.
- **Documentation**: `README.md` describes the current-user result shape and the meaning of `data_type`; `AGENTS.md` gains nothing beyond what it already mandates.
- **Compatibility**: Additive for `zenkit_list_columns` (`data_type` stops being `null`). Removing `api_key` from the current-user result is an intentional, security-motivated narrowing of that tool's output.
- **Out of scope**: New tools, changes to filtering/pagination, and any change to the HTTP client's error mapping.
