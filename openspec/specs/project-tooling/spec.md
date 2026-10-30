# project-tooling Specification

## Purpose

Defines the reproducible `uv`-based development workflow, quality checks, and contributor documentation required to build on the Zenkit MCP server.

## Requirements

### Requirement: uv-managed environment

The project SHALL declare its runtime and development dependencies in `pyproject.toml`, target Python 3.12 or newer, and install completely with `uv sync`.

#### Scenario: Fresh environment setup
- **WHEN** a contributor clones the repository and runs `uv sync`
- **THEN** a virtual environment is created containing `fastmcp`, `pytest`, `pytest-asyncio`, and `ruff` at the locked versions

#### Scenario: Locked dependencies are reproducible
- **WHEN** a contributor runs `uv lock --check`
- **THEN** the committed lock file matches the declared dependencies

### Requirement: Single dependency management path

All dependency changes SHALL be applied through `uv`, and the lock file SHALL be committed so installs are reproducible across machines.

#### Scenario: Lock file is tracked
- **WHEN** the repository is inspected
- **THEN** `uv.lock` is present and not excluded by version control ignores

### Requirement: Lint and format checks

The project SHALL provide `ruff` configuration, and the scaffold sources and tests SHALL pass both `uv run ruff check` and `uv run ruff format --check`.

#### Scenario: Lint gate passes on the scaffold
- **WHEN** a contributor runs the documented lint commands on a clean checkout
- **THEN** both commands exit successfully

### Requirement: Automated tests through a real client

The project SHALL include a `pytest` suite that exercises the server and tools through FastMCP's in-memory client, and the suite SHALL pass with `uv run pytest`.

#### Scenario: Test suite passes
- **WHEN** a contributor runs `uv run pytest` on a clean checkout with no Zenkit credentials
- **THEN** the suite completes successfully without network access

#### Scenario: Removing a tool breaks the suite
- **WHEN** the registration of `zenkit_connection_status` is removed from the server
- **THEN** at least one test fails because the tool is no longer discoverable

### Requirement: README documentation

The repository SHALL include a `README.md` covering the project purpose, prerequisites, installation, how to run the server in stdio and HTTP modes, an MCP client configuration example, test and lint commands, the project layout, and troubleshooting.

#### Scenario: New contributor follows the README
- **WHEN** a new contributor follows the README from a clean checkout
- **THEN** they can install dependencies, run the server, run the tests, and connect a client using only the documented commands

### Requirement: AGENTS.md guidance

The repository SHALL include an `AGENTS.md` describing the canonical `uv` commands, project layout, coding conventions, secrets and stdout rules, how to add a tool with tests, and the OpenSpec workflow.

#### Scenario: Agent follows repository guidance
- **WHEN** a coding agent reads `AGENTS.md`
- **THEN** it finds the commands to set up, test, lint, and run the server, plus the rules for adding tools and handling secrets

### Requirement: Ignore hygiene

The repository SHALL ignore local environments, Python and tool caches, build artifacts, and `.env` files while continuing to track project sources, documentation, and `uv.lock`.

#### Scenario: Local artifacts stay untracked
- **WHEN** a contributor runs the server and tests locally
- **THEN** `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, and `.env` do not appear as untracked files

### Requirement: Documented commands stay accurate

The commands shown in `README.md` and `AGENTS.md` SHALL be executable as written in the managed environment.

#### Scenario: Documentation commands run successfully
- **WHEN** every setup, run, test, and lint command listed in the documentation is executed from the repository root
- **THEN** each command completes without a command-not-found error or missing-dependency failure
