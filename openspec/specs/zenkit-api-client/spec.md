# zenkit-api-client Specification

## Purpose

Defines the authenticated HTTP access layer that talks to the Zenkit REST API on behalf of MCP tools.

## Requirements

### Requirement: Requests authenticate with the Zenkit API key
The API access layer SHALL attach the configured Zenkit API key as the `Zenkit-API-Key` header on every request it makes.

#### Scenario: Header is present on every request
- **WHEN** a tool triggers a request through the API access layer while an API key is configured
- **THEN** the outgoing request carries a `Zenkit-API-Key` header whose value equals the configured key

### Requirement: Requests target the configured base URL
The API access layer SHALL resolve all endpoint paths against the configured Zenkit base URL.

#### Scenario: Endpoint path is resolved against the base URL
- **WHEN** the base URL is `https://example.test/api/v1` and a request targets the `/users/me` path
- **THEN** the request is sent to `https://example.test/api/v1/users/me`

### Requirement: Non-success responses become tool errors
The API access layer SHALL translate HTTP error statuses and malformed JSON responses into a tool error with an actionable message, without exposing stack traces or internal paths.

#### Scenario: HTTP error status is surfaced as a tool error
- **WHEN** Zenkit responds with a 4xx or 5xx status
- **THEN** the caller receives a tool error that includes the failing status and a message describing how to recover

### Requirement: The API key is never exposed
The API access layer SHALL NOT include the API key, or any fragment of it, in results, error messages, or logs.

#### Scenario: Key does not appear in errors or results
- **WHEN** a request fails while an API key is configured
- **THEN** neither the resulting error nor any captured log contains the key value

### Requirement: Result lists are paginated
The API access layer SHALL paginate result lists using the Zenkit `limit` and `skip` parameters and SHALL continue fetching pages until a short or empty page indicates completion.

#### Scenario: All pages are collected
- **WHEN** a list endpoint returns more results than a single page
- **THEN** the caller receives all results across pages, in order

### Requirement: Requests complete within a bounded timeout
The API access layer SHALL enforce a request timeout so that an unresponsive Zenkit service fails fast instead of hanging indefinitely.

#### Scenario: Unresponsive service fails fast
- **WHEN** Zenkit does not respond within the configured timeout
- **THEN** the caller receives a tool error instead of an indefinite wait

### Requirement: Missing credentials fail with guidance
The API access layer SHALL fail with a tool error that tells the user to set `ZENKIT_API_KEY` when an API-backed request is attempted without a configured key.

#### Scenario: Unauthenticated request is rejected
- **WHEN** a tool attempts an API-backed request while no API key is configured
- **THEN** the call fails with a tool error instructing the user to configure `ZENKIT_API_KEY`

### Requirement: Credentials are sent only over HTTPS

The system SHALL accept only `https` base URLs, so the `Zenkit-API-Key` header is never transmitted
over a plaintext connection. A base URL with any other scheme SHALL be rejected with an actionable
configuration error that names `ZENKIT_API_BASE_URL`.

#### Scenario: Plaintext base URL is rejected

- **WHEN** `ZENKIT_API_BASE_URL` is set to an `http://` URL
- **THEN** configuration loading fails with an error naming `ZENKIT_API_BASE_URL` and stating that
  an HTTPS URL is required

#### Scenario: Plaintext loopback base URL is rejected

- **WHEN** `ZENKIT_API_BASE_URL` is set to `http://127.0.0.1:8080/api/v1` or
  `http://localhost:8080/api/v1`
- **THEN** configuration loading fails with the same HTTPS-required error, because no cleartext
  exception is granted for loopback hosts

#### Scenario: HTTPS base URL is accepted

- **WHEN** `ZENKIT_API_BASE_URL` is set to `https://example.test/api/v1`
- **THEN** configuration loading succeeds and requests resolve against that URL

#### Scenario: Default needs no configuration

- **WHEN** `ZENKIT_API_BASE_URL` is unset or blank
- **THEN** configuration loading succeeds using the HTTPS default `https://zenkit.com/api/v1`

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
