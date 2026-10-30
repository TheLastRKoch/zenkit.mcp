# zenkit-tools Specification

## Purpose

Defines the tool surface the server exposes to MCP clients, starting with a credential-safe Zenkit connection status tool that works before real API integration exists.

## Requirements

### Requirement: Connection status tool

The server SHALL expose a tool named `zenkit_connection_status` that accepts no arguments and reports whether Zenkit credentials are configured, along with the effective Zenkit API base URL.

#### Scenario: No credentials configured
- **WHEN** a client calls `zenkit_connection_status` while no Zenkit API key is present
- **THEN** the result reports `configured` as `false` and includes the effective API base URL, without failing

#### Scenario: Credentials configured
- **WHEN** a client calls `zenkit_connection_status` while a Zenkit API key is present
- **THEN** the result reports `configured` as `true` and includes the effective API base URL

### Requirement: Credential configuration sources

The server SHALL read the Zenkit API key from the `ZENKIT_API_KEY` environment variable and the API base URL from `ZENKIT_API_BASE_URL`, using `https://zenkit.com/api/v1` when the base URL is not set.

#### Scenario: Default base URL is applied
- **WHEN** no base URL is configured and `zenkit_connection_status` is called
- **THEN** the reported API base URL is `https://zenkit.com/api/v1`

#### Scenario: Overridden base URL is applied
- **WHEN** `ZENKIT_API_BASE_URL` is set to a valid HTTPS URL and `zenkit_connection_status` is called
- **THEN** the reported API base URL matches the configured value

### Requirement: Credentials are never exposed

The server SHALL NOT return, log, or otherwise expose the Zenkit API key value in tool results, error messages, or standard error output.

#### Scenario: API key is not echoed
- **WHEN** `zenkit_connection_status` is called while a Zenkit API key is set
- **THEN** the tool result and captured server logs contain no occurrence of that key value

### Requirement: Malformed base URL is reported as a tool error

The server SHALL reject a configured API base URL that is not an absolute HTTP or HTTPS URL by returning a tool error with an actionable message instead of returning a normal result.

#### Scenario: Invalid base URL produces a tool error
- **WHEN** `ZENKIT_API_BASE_URL` is set to a value without a host or with a non-HTTP scheme and the tool is called
- **THEN** the call fails as a tool error whose message explains that the base URL must be an absolute HTTP or HTTPS URL

### Requirement: Tool discovery metadata

Every exposed tool SHALL be discoverable through MCP tool listing with a short snake_case name, a description of its purpose, and an input schema generated from its typed parameters.

#### Scenario: Clients can discover the tool
- **WHEN** a client lists the server's tools
- **THEN** `zenkit_connection_status` appears with a non-empty description and an input schema that declares no required properties

### Requirement: No network access during scaffold operations

The scaffold SHALL NOT perform outbound network requests when starting or when serving `zenkit_connection_status`, leaving real Zenkit API calls to a later change.

#### Scenario: Status check performs no HTTP calls
- **WHEN** `zenkit_connection_status` is called with any credential configuration
- **THEN** no outbound HTTP request is made

### Requirement: Tool error contract

Tools that cannot complete SHALL surface an MCP tool error with a user-actionable message and SHALL NOT return stack traces, internal file paths, or raw exception text to clients.

#### Scenario: Tool failure is client-safe
- **WHEN** any exposed tool encounters a failure it cannot resolve
- **THEN** the client receives a tool error containing guidance to fix the problem and no traceback or internal path

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

### Requirement: Update entry tool
The server SHALL expose a `zenkit_update_entry` tool that applies supplied custom column values to an existing entry and returns the updated entry's identifier and custom column values.

#### Scenario: Entry is updated
- **WHEN** a client calls `zenkit_update_entry` with a valid list id, a valid entry id, and column values
- **THEN** the entry's custom column values are updated and the result contains the entry's id, uuid, and updated fields

#### Scenario: Date and time are scheduled in one call
- **WHEN** a client supplies a date value together with the scheduling metadata that marks the date as timed and sets its end
- **THEN** the entry is stored as a timed entry with that start and end, and the result reflects the new values

#### Scenario: Unknown entry fails as a tool error
- **WHEN** a client calls `zenkit_update_entry` with an entry id that does not exist in the list
- **THEN** the call fails with a tool error identifying the missing resource

#### Scenario: Empty update is rejected
- **WHEN** a client calls `zenkit_update_entry` without any column values
- **THEN** the call fails with a tool error before any request is sent

#### Scenario: Unconfigured API tool fails with guidance
- **WHEN** a client calls `zenkit_update_entry` while no API key is configured
- **THEN** the call fails with a tool error referencing `ZENKIT_API_KEY`

### Requirement: Update tool is discoverable
The update tool SHALL be discoverable through MCP tool listing with a `zenkit_`-prefixed snake_case name, a description derived from its docstring, and an input schema generated from typed parameters.

#### Scenario: Update tool appears in the tool list
- **WHEN** a client lists the server's tools
- **THEN** `zenkit_update_entry` is present with a description and a schema accepting a list id, an entry id, and a mapping of column values

#### Scenario: Failure messages stay actionable
- **WHEN** an update request fails because Zenkit rejects the credentials or the payload
- **THEN** the client receives a tool error describing the failure without stack traces or internal paths
