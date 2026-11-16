# Spec Delta

## Purpose

Defines how the Zenkit MCP server is packaged and operated as a container service, including its default transport, published port, credential contract, and runtime privileges.

## ADDED Requirements

### Requirement: Container serves Streamable HTTP on port 9010
The container image SHALL start the server in Streamable HTTP mode, bound to all container interfaces on port `9010`, when it is run without overriding the launch arguments.

#### Scenario: Default container launch listens on 9010
- **WHEN** the container starts with its default command and the required environment variables set
- **THEN** the server accepts Streamable HTTP connections on port `9010` inside the container

#### Scenario: MCP client completes initialization
- **WHEN** a client connects to `http://<container-host>:9010/mcp` with a valid bearer token and completes the initialization handshake
- **THEN** the server responds with its identity and advertises the Zenkit tools

### Requirement: Container image carries no credentials
The image SHALL NOT contain the Zenkit API key or the client authentication token in any layer, build argument, or default environment value.

#### Scenario: Credentials are absent from the image
- **WHEN** the built image is inspected without runtime environment variables
- **THEN** neither the Zenkit API key nor the client authentication token value appears in image metadata or layers

### Requirement: Container runs without root privileges
The container SHALL run the server process as an unprivileged user.

#### Scenario: Server process is not root
- **WHEN** the container starts
- **THEN** the server process runs as a user other than `root`

### Requirement: Compose deployment requires credentials
The compose deployment SHALL publish port `9010` on the host and SHALL refuse to start the container when `ZENKIT_API_KEY` or `ZENKIT_MCP_AUTH_TOKEN` is unset.

#### Scenario: Missing credentials fail before startup
- **WHEN** the compose deployment is started while either required variable is unset
- **THEN** it fails with an error that names the missing variable and no server container is started

#### Scenario: Configured deployment starts successfully
- **WHEN** both required variables are set and the deployment starts
- **THEN** the container runs, serves port `9010`, and reports a healthy status

### Requirement: Compose deployment reports container health
The compose deployment SHALL define a healthcheck that verifies the server is accepting connections on port `9010`.

#### Scenario: Unresponsive server is reported unhealthy
- **WHEN** the server stops accepting connections on port `9010`
- **THEN** the container health status becomes unhealthy
