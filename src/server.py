"""FastMCP server wiring and command-line entrypoint for Zenkit."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version

from fastmcp import FastMCP

from tools import zenkit

PACKAGE_NAME = "zenkit-mcp"
SERVER_NAME = "zenkit-mcp"
SERVER_INSTRUCTIONS = (
    "Exposes Zenkit project management tools. Start with zenkit_connection_status to "
    "check whether Zenkit credentials are configured."
)
DEFAULT_TRANSPORT = "stdio"
TRANSPORTS = ("stdio", "http")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

logger = logging.getLogger(__name__)


def package_version() -> str:
    """Return the installed package version, falling back when running from source."""
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.0.0"


def create_server() -> FastMCP:
    """Build the Zenkit MCP server with all tools registered."""
    server = FastMCP(
        name=SERVER_NAME,
        version=package_version(),
        instructions=SERVER_INSTRUCTIONS,
    )
    zenkit.register(server)
    return server


mcp = create_server()


def port_number(value: str) -> int:
    """Parse and validate a TCP port number for argparse."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid port: {value!r}") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"port must be between 1 and 65535, got {port}")
    return port


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the server process."""
    parser = argparse.ArgumentParser(
        prog=SERVER_NAME,
        description="Run the Zenkit MCP server over stdio (default) or Streamable HTTP.",
    )
    parser.add_argument(
        "--transport",
        choices=TRANSPORTS,
        default=DEFAULT_TRANSPORT,
        help=f"MCP transport to use (default: {DEFAULT_TRANSPORT}).",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind when using the HTTP transport (default: {DEFAULT_HOST}).",
    )
    parser.add_argument(
        "--port",
        type=port_number,
        default=DEFAULT_PORT,
        help=f"Port to bind when using the HTTP transport (default: {DEFAULT_PORT}).",
    )
    return parser


def configure_logging() -> None:
    """Send diagnostics to stderr so stdout stays a clean MCP protocol stream."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Parse launch options and run the MCP server."""
    args = build_parser().parse_args(argv)
    configure_logging()

    if args.transport == "http":
        logger.info("Starting %s over Streamable HTTP on %s:%s", SERVER_NAME, args.host, args.port)
        mcp.run(transport="http", host=args.host, port=args.port, show_banner=False)
    else:
        logger.info("Starting %s over stdio", SERVER_NAME)
        mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
