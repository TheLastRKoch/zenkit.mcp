# Spec Delta

## ADDED Requirements

### Requirement: Current user tool
The server SHALL expose a `zenkit_get_current_user` tool that returns the authenticated Zenkit user's identity, validating the configured API key against Zenkit.

#### Scenario: Valid credentials return the user
- **WHEN** a client calls `zenkit_get_current_user` with a valid API key
- **THEN** the result contains the authenticated user's id and display name

#### Scenario: Invalid credentials fail as a tool error
- **WHEN** a client calls `zenkit_get_current_user` with an invalid API key
- **THEN** the call fails with a tool error indicating the credentials were rejected

### Requirement: List discovery tool
The server SHALL expose a `zenkit_list_lists` tool that returns the lists the authenticated user can access, including each list's id and name.

#### Scenario: Accessible lists are returned
- **WHEN** a client calls `zenkit_list_lists`
- **THEN** the result is a collection of lists, each carrying an id and a name

### Requirement: Single list tool
The server SHALL expose a `zenkit_get_list` tool that returns a single list by id.

#### Scenario: Existing list is returned
- **WHEN** a client calls `zenkit_get_list` with a valid list id
- **THEN** the result contains that list's id and name

#### Scenario: Unknown list fails as a tool error
- **WHEN** a client calls `zenkit_get_list` with a list id that does not exist
- **THEN** the call fails with a tool error

### Requirement: Custom column tool
The server SHALL expose a `zenkit_list_columns` tool that returns a list's custom columns, each with an identifier, a name, and a data type.

#### Scenario: Columns are returned
- **WHEN** a client calls `zenkit_list_columns` with a valid list id
- **THEN** the result is a collection of columns, each carrying an identifier, a name, and a data type

### Requirement: Entries tool
The server SHALL expose a `zenkit_get_entries` tool that returns entries in a list, honoring optional filtering and `limit`/`skip` pagination, with each entry carrying its id and custom column values.

#### Scenario: Entries are returned
- **WHEN** a client calls `zenkit_get_entries` with a valid list id
- **THEN** the result is a collection of entries, each carrying an id and its custom column values

#### Scenario: Pagination parameters are honored
- **WHEN** a client calls `zenkit_get_entries` with a `limit` and `skip`
- **THEN** the returned entries respect the requested window

#### Scenario: Empty list returns no entries
- **WHEN** a client calls `zenkit_get_entries` for a list with no entries
- **THEN** the result is an empty collection rather than an error

### Requirement: Single entry tool
The server SHALL expose a `zenkit_get_entry` tool that returns a single entry by list id and entry id.

#### Scenario: Existing entry is returned
- **WHEN** a client calls `zenkit_get_entry` with a valid list id and entry id
- **THEN** the result contains that entry's id and custom column values

### Requirement: Create entry tool
The server SHALL expose a `zenkit_create_entry` tool that creates an entry in a list with the supplied custom column values and returns the created entry's identifier.

#### Scenario: Entry is created
- **WHEN** a client calls `zenkit_create_entry` with a valid list id and column values
- **THEN** a new entry is created and the result contains the new entry's identifier

### Requirement: API-backed tools require configuration
API-backed tools SHALL fail with a tool error instructing the user to configure `ZENKIT_API_KEY` when no key is configured, rather than performing an unauthenticated request.

#### Scenario: Unconfigured API tool fails with guidance
- **WHEN** a client calls any API-backed tool while no API key is configured
- **THEN** the call fails with a tool error referencing `ZENKIT_API_KEY`

### Requirement: API-backed tool discovery
The new API-backed tools SHALL be discoverable through MCP tool listing with a `zenkit_`-prefixed snake_case name, a description, and an input schema generated from typed parameters.

#### Scenario: New tools are discoverable
- **WHEN** a client lists the server's tools
- **THEN** `zenkit_get_current_user`, `zenkit_list_lists`, `zenkit_get_list`, `zenkit_list_columns`, `zenkit_get_entries`, `zenkit_get_entry`, and `zenkit_create_entry` all appear with a description and an input schema

### Requirement: Secrets never appear in tool results
No API-backed tool SHALL include the configured API key in its results, error messages, or logs.

#### Scenario: Key is absent from results
- **WHEN** any API-backed tool runs while a key is configured
- **THEN** the key value does not appear in the tool result or captured logs
