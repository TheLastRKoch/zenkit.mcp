"""Tests for server wiring, discovery, and launch options."""

from importlib.metadata import version

import pytest
from fastmcp import Client

from server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    SERVER_NAME,
    build_parser,
    create_server,
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
