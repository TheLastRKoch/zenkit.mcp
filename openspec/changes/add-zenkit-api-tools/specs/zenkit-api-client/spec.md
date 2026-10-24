# Spec Delta

## Purpose

Defines the authenticated HTTP access layer that talks to the Zenkit REST API on behalf of MCP tools.

## ADDED Requirements

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
