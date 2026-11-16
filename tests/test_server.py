"""Tests for server wiring, discovery, and launch options."""

from importlib.metadata import version

import pytest
from fastmcp import Client
from starlette.testclient import TestClient

from config import AUTH_TOKEN_ENV_VAR, HttpAuthSettings
from server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    SERVER_NAME,
    build_auth_provider,
    build_parser,
    create_server,
    ensure_http_auth_configured,
    is_loopback_host,
)


async def test_server_advertises_identity_and_tools() -> None:
    async with Client(create_server()) as client:
        server_info = client.server_info
        instructions = client.instructions
        tools = await client.list_tools()

    assert server_info is not None
    assert server_info.name == SERVER_NAME
    assert server_info.version == version("zenkit-mcp")
    assert instructions

    tool = next(tool for tool in tools if tool.name == "zenkit_connection_status")
    assert tool.description
    assert not tool.input_schema.get("required")


def test_parser_defaults_to_stdio() -> None:
    args = build_parser().parse_args([])

    assert args.transport == "stdio"
    assert args.host == DEFAULT_HOST
    assert args.port == DEFAULT_PORT


def test_parser_accepts_http_options() -> None:
    args = build_parser().parse_args(["--transport", "http", "--host", "0.0.0.0", "--port", "9000"])

    assert args.transport == "http"
    assert args.host == "0.0.0.0"
    assert args.port == 9000


@pytest.mark.parametrize("argv", [["--transport", "grpc"], ["--port", "0"], ["--port", "70000"]])
def test_parser_rejects_invalid_options(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(argv)

    assert excinfo.value.code == 2


def test_server_without_auth_setting_is_unauthenticated() -> None:
    assert create_server().auth is None
    assert build_auth_provider(HttpAuthSettings()) is None


def test_auth_provider_is_built_from_configured_token() -> None:
    assert build_auth_provider(HttpAuthSettings(token="client-token")) is not None


@pytest.mark.parametrize("host", ["127.0.0.1", "127.0.0.5", "::1", "localhost", "LOCALHOST"])
def test_loopback_hosts_are_recognized(host: str) -> None:
    assert is_loopback_host(host)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.10", "zenkit-mcp", ""])
def test_non_loopback_hosts_are_not_recognized(host: str) -> None:
    assert not is_loopback_host(host)


def test_loopback_http_without_token_is_allowed() -> None:
    ensure_http_auth_configured("127.0.0.1", HttpAuthSettings())


def test_non_loopback_http_with_token_is_allowed() -> None:
    ensure_http_auth_configured("0.0.0.0", HttpAuthSettings(token="client-token"))


def test_non_loopback_http_without_token_is_refused(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(SystemExit) as excinfo:
        ensure_http_auth_configured("0.0.0.0", HttpAuthSettings())

    assert excinfo.value.code == 2
    assert AUTH_TOKEN_ENV_VAR in caplog.text


def test_http_endpoint_requires_the_configured_bearer_token() -> None:
    token = "client-token"
    server = create_server(build_auth_provider(HttpAuthSettings(token=token)))
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    headers = {"Accept": "application/json, text/event-stream"}

    with TestClient(server.http_app()) as http_client:
        unauthenticated = http_client.post("/mcp", json=initialize, headers=headers)
        authenticated = http_client.post(
            "/mcp", json=initialize, headers={**headers, "Authorization": f"Bearer {token}"}
        )

    assert unauthenticated.status_code == 401
    assert authenticated.status_code != 401
