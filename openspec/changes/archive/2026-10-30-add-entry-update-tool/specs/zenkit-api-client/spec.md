# Spec Delta

## ADDED Requirements

### Requirement: Entry updates target the entry resource
The API access layer SHALL update an existing entry through that entry's resource in the target list, sending only the supplied custom column values and returning the updated entry payload.

#### Scenario: Update carries the supplied values
- **WHEN** a caller updates an entry with a mapping of custom column values
- **THEN** Zenkit receives those values for that entry and the caller receives the updated entry payload

#### Scenario: Unknown entry surfaces as a tool error
- **WHEN** the entry resource does not exist for the given list
- **THEN** the caller receives a tool error that the requested resource does not exist

#### Scenario: Rejected credentials surface as a tool error
- **WHEN** Zenkit rejects the configured API key during an update
- **THEN** the caller receives a tool error that names the credentials problem without exposing the key

#### Scenario: Invalid payload surfaces as a tool error
- **WHEN** Zenkit rejects the supplied values with a client error
- **THEN** the caller receives a tool error that includes the failing status and how to recover
