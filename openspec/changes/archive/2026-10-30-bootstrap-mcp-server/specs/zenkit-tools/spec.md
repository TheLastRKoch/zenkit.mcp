# Spec Delta

## Purpose

Defines the tool surface the server exposes to MCP clients, starting with a credential-safe Zenkit connection status tool that works before real API integration exists.

## ADDED Requirements

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
