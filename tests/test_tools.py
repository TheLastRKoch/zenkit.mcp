"""Tests for Zenkit tools, exercised through FastMCP's in-memory client."""

import logging
import socket
from collections.abc import Iterator

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from config import API_BASE_URL_ENV_VAR, API_KEY_ENV_VAR, DEFAULT_API_BASE_URL
from tools.zenkit import register


@pytest.fixture(autouse=True)
def clean_zenkit_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    monkeypatch.delenv(API_BASE_URL_ENV_VAR, raising=False)
    yield


@pytest.fixture
def server() -> FastMCP:
    server = FastMCP("test")
    register(server)
    return server


async def test_status_reports_unconfigured_without_credentials(server: FastMCP) -> None:
    async with Client(server) as client:
        result = await client.call_tool("zenkit_connection_status", {})

    assert result.data["configured"] is False
    assert result.data["api_base_url"] == DEFAULT_API_BASE_URL


async def test_status_reports_configured_with_credentials(
    server: FastMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "test-api-key")

    async with Client(server) as client:
        result = await client.call_tool("zenkit_connection_status", {})

    assert result.data["configured"] is True


async def test_status_reports_overridden_base_url(
    server: FastMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(API_BASE_URL_ENV_VAR, "https://example.test/api/v1")

    async with Client(server) as client:
        result = await client.call_tool("zenkit_connection_status", {})

    assert result.data["api_base_url"] == "https://example.test/api/v1"


async def test_malformed_base_url_raises_tool_error(
    server: FastMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(API_BASE_URL_ENV_VAR, "not-a-url")

    async with Client(server) as client:
        with pytest.raises(ToolError, match=API_BASE_URL_ENV_VAR):
            await client.call_tool("zenkit_connection_status", {})


async def test_api_key_is_never_exposed(
    server: FastMCP, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "super-secret-zenkit-key"
    monkeypatch.setenv(API_KEY_ENV_VAR, secret)
    caplog.set_level(logging.DEBUG)

    async with Client(server) as client:
        result = await client.call_tool("zenkit_connection_status", {})

    assert secret not in repr(result)
    assert secret not in str(result)
    assert secret not in caplog.text


async def test_status_makes_no_network_connections(
    server: FastMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_connect(*args: object, **kwargs: object) -> None:
        raise AssertionError("zenkit_connection_status must not open network connections")

    monkeypatch.setattr(socket.socket, "connect", fail_connect)

    async with Client(server) as client:
        result = await client.call_tool("zenkit_connection_status", {})

    assert result.data["configured"] is False
