# Spec Delta

## ADDED Requirements

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
