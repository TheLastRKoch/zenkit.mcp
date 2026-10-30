# Spec Delta

## Purpose

Defines how the Zenkit MCP server is identified, launched, and connected to by MCP clients across its supported transports.

## ADDED Requirements

### Requirement: Server identity

The server SHALL identify itself to MCP clients with the name `zenkit-mcp`, the version declared by the installed package metadata, and instructions describing that it exposes Zenkit project-management tools.

#### Scenario: Client reads server metadata
- **WHEN** a client completes the MCP initialization handshake
- **THEN** the server reports the name `zenkit-mcp`, a non-empty semantic version, and non-empty usage instructions

#### Scenario: Reported version tracks the package
- **WHEN** the package version is changed in the project metadata and the server is restarted
- **THEN** the version reported during initialization matches the new package version

### Requirement: Stdio is the default transport

The server SHALL communicate over standard input/output when it is started without an explicit transport selection, so local MCP clients can launch it as a subprocess.

#### Scenario: Default launch uses stdio
- **WHEN** the server is started with no transport arguments
- **THEN** it waits for MCP messages on standard input and writes protocol responses to standard output

### Requirement: Stdout carries only MCP protocol messages

While running in stdio mode, the server SHALL write logs, warnings, and diagnostics only to standard error, keeping standard output valid for the MCP protocol stream.

#### Scenario: Startup produces no stray stdout
- **WHEN** the server starts and handles a request in stdio mode
- **THEN** every line written to standard output is part of the protocol exchange and any log output appears on standard error

### Requirement: Opt-in Streamable HTTP transport

The server SHALL support the Streamable HTTP transport when HTTP is explicitly selected, honoring a configurable host and port that default to `127.0.0.1` and `8000`.

#### Scenario: HTTP mode is reachable
- **WHEN** the server is started with the HTTP transport selected and port `9000`
- **THEN** MCP clients can connect to `http://127.0.0.1:9000` and complete initialization

#### Scenario: Default launch does not open a network port
- **WHEN** the server is started without selecting HTTP
- **THEN** no listening TCP port is opened by the server

### Requirement: Stable executable entrypoints

The project SHALL expose the same server through an installed console command `zenkit-mcp` and through direct execution of the `src/server.py` script.

#### Scenario: Console command starts the server
- **WHEN** a user runs `zenkit-mcp` inside the managed environment
- **THEN** the server starts with default settings

#### Scenario: Direct script execution starts the server
- **WHEN** a user runs `python src/server.py` inside the managed environment
- **THEN** the server starts with the same behavior as the console command

### Requirement: Invalid launch options fail fast

The server SHALL reject unsupported transport selections with a clear error message on standard error and a non-zero exit status instead of hanging or silently falling back.

#### Scenario: Unknown transport is rejected
- **WHEN** the server is started with an unsupported transport name
- **THEN** it prints an error explaining the valid options, exits with a non-zero status, and opens no protocol session

### Requirement: Startup requires no credentials

The server SHALL start and complete the MCP initialization handshake without Zenkit credentials or any outbound network access, so the scaffold is usable before API integration exists.

#### Scenario: Cold start without configuration
- **WHEN** the server is started in an environment with no Zenkit environment variables and no network access
- **THEN** initialization succeeds and the advertised tools remain available
