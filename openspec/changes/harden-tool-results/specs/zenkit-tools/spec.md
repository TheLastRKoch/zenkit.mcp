# Spec Delta

## MODIFIED Requirements

### Requirement: Current user tool

The server SHALL expose a `zenkit_get_current_user` tool that returns the authenticated Zenkit user's identity, validating the configured API key against Zenkit. The result SHALL exclude the API key and any other credential-bearing field present in the upstream payload.

#### Scenario: Valid credentials return the user
- **WHEN** a client calls `zenkit_get_current_user` with a valid API key
- **THEN** the result contains the authenticated user's id and display name

#### Scenario: API key is never returned
- **WHEN** a client calls `zenkit_get_current_user` and Zenkit includes the caller's API key in its user payload
- **THEN** the result contains no field carrying that key value and no fragment of it

#### Scenario: Invalid credentials fail as a tool error
- **WHEN** a client calls `zenkit_get_current_user` with an invalid API key
- **THEN** the call fails with a tool error indicating the credentials were rejected

### Requirement: Custom column tool

The server SHALL expose a `zenkit_list_columns` tool that returns a list's custom columns, each with an identifier, a name, and a data type. When Zenkit omits or nulls its own type field, the reported data type SHALL be derived from the column definition.

#### Scenario: Columns are returned
- **WHEN** a client calls `zenkit_list_columns` with a valid list id
- **THEN** the result is a collection of columns, each carrying an identifier and a name, and a non-empty data type whenever the definition exposes a value type

#### Scenario: Data type is derived when Zenkit omits it
- **WHEN** a column's upstream type field is null and the column definition carries its values under a typed key
- **THEN** the reported data type is that key, so text, date, label, person, file, number, and reference columns are distinguishable

#### Scenario: Columns without a value type do not guess
- **WHEN** a column's definition carries no value payload, such as a created-at or last-updated system column
- **THEN** the reported data type is null rather than an invented value

#### Scenario: Data type matches the entry field-key suffix
- **WHEN** a client reads a column and then reads entries from the same list
- **THEN** the reported data type equals the suffix of the entry field key built from that column
