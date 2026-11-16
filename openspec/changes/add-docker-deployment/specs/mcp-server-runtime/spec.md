# Spec Delta

## MODIFIED Requirements

### Requirement: Opt-in Streamable HTTP transport

The server SHALL support the Streamable HTTP transport when HTTP is explicitly selected, honoring a configurable host and port that default to `127.0.0.1` and `8000`. When a client authentication token is configured, HTTP requests SHALL be authenticated before any tool is invoked.

#### Scenario: HTTP mode is reachable
- **WHEN** the server is started with the HTTP transport selected and port `9000`
- **THEN** MCP clients can connect to `http://127.0.0.1:9000` and complete initialization

#### Scenario: Authenticated request over HTTP is accepted
- **WHEN** the server is started with the HTTP transport selected, a client authentication token configured, and a client sends the matching bearer token
- **THEN** the client can list and call the Zenkit tools

#### Scenario: Default launch does not open a network port
- **WHEN** the server is started without selecting HTTP
- **THEN** no listening TCP port is opened by the server

## ADDED Requirements

### Requirement: HTTP requests require the configured bearer token
When `ZENKIT_MCP_AUTH_TOKEN` is configured, the server SHALL accept an HTTP request only if it carries an `Authorization` header with the bearer token matching that value, and SHALL reject every other request without invoking a tool.

#### Scenario: Missing credentials are rejected
- **WHEN** a client sends an HTTP request without an `Authorization` header while a token is configured
- **THEN** the request is rejected with an authentication error and no tool is executed

#### Scenario: Incorrect credentials are rejected
- **WHEN** a client sends an HTTP request with a bearer token that does not match the configured value
- **THEN** the request is rejected with an authentication error and no tool is executed

### Requirement: Non-loopback HTTP binding requires a token
The server SHALL refuse to start in HTTP mode on a non-loopback host when no client authentication token is configured, exiting with a non-zero status and an error that names `ZENKIT_MCP_AUTH_TOKEN`.

#### Scenario: Unauthenticated exposure is refused
- **WHEN** the server is started with the HTTP transport on a non-loopback host and no configured token
- **THEN** it exits with a non-zero status, explains that `ZENKIT_MCP_AUTH_TOKEN` is required, and opens no listening port

#### Scenario: Loopback remains usable without a token
- **WHEN** the server is started with the HTTP transport bound to `127.0.0.1` and no configured token
- **THEN** it starts and serves HTTP requests as before

#### Scenario: Configured token allows a non-loopback binding
- **WHEN** the server is started with the HTTP transport on a non-loopback host and a configured token
- **THEN** it starts and requires the bearer token on every request

### Requirement: The authentication token is never exposed
The server SHALL NOT include the client authentication token in logs, error messages, or tool results.

#### Scenario: Token is absent from startup failure output
- **WHEN** the server rejects a request or exits because of its HTTP authentication configuration
- **THEN** neither the resulting message nor any captured log contains the token value
