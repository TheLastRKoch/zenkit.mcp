"""FastMCP server wiring and command-line entrypoint for Zenkit."""

from __future__ import annotations

import argparse
import ipaddress
import logging
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from config import AUTH_TOKEN_ENV_VAR, HttpAuthSettings
from tools import zenkit

if TYPE_CHECKING:
    from fastmcp.server.auth import AuthProvider

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


def create_server(auth: AuthProvider | None = None) -> FastMCP:
    """Build the Zenkit MCP server with all tools registered."""
    server = FastMCP(
        name=SERVER_NAME,
        version=package_version(),
        instructions=SERVER_INSTRUCTIONS,
        auth=auth,
    )
    zenkit.register(server)
    return server


def build_auth_provider(auth_settings: HttpAuthSettings) -> AuthProvider | None:
    """Return a bearer-token auth provider, or ``None`` when no token is configured."""
    if auth_settings.token is None:
        return None
    # Imported lazily: the auth providers pull in heavy optional dependencies that
    # stdio deployments never need.
    from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

    return StaticTokenVerifier(tokens={auth_settings.token: {"client_id": SERVER_NAME}})


def is_loopback_host(host: str) -> bool:
    """Whether ``host`` only accepts connections from the same machine."""
    candidate = host.strip().lower()
    if candidate == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def ensure_http_auth_configured(host: str, auth_settings: HttpAuthSettings) -> None:
    """Refuse to expose the HTTP transport on a reachable address without a token."""
    if auth_settings.configured or is_loopback_host(host):
        return
    logger.error(
        "Refusing to serve HTTP on %s: set %s to the token clients must send, "
        "or bind to 127.0.0.1.",
        host,
        AUTH_TOKEN_ENV_VAR,
    )
    raise SystemExit(2)


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

    auth_settings = HttpAuthSettings.from_env()
    if args.transport == "http":
        ensure_http_auth_configured(args.host, auth_settings)
        logger.info("Starting %s over Streamable HTTP on %s:%s", SERVER_NAME, args.host, args.port)
        if auth_settings.configured:
            logger.info("Client authentication is required via %s", AUTH_TOKEN_ENV_VAR)
        else:
            logger.info("No client authentication configured; %s is loopback only", args.host)
        create_server(build_auth_provider(auth_settings)).run(
            transport="http", host=args.host, port=args.port, show_banner=False
        )
    else:
        logger.info("Starting %s over stdio", SERVER_NAME)
        create_server().run(show_banner=False)


if __name__ == "__main__":
    main()
