"""Tools that expose Zenkit functionality to MCP clients."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from config import Settings, SettingsError


def zenkit_connection_status() -> dict[str, Any]:
    """Report whether Zenkit credentials are configured, without calling the Zenkit API."""
    try:
        settings = Settings.from_env()
    except SettingsError as exc:
        raise ToolError(str(exc)) from exc

    if settings.configured:
        message = (
            "Zenkit API key is configured. This scaffold performs no network calls; "
            "API-backed tools arrive in a later change."
        )
    else:
        message = (
            "Zenkit API key is not configured. Set ZENKIT_API_KEY to enable future API "
            "access. This scaffold performs no network calls."
        )

    return {
        "configured": settings.configured,
        "api_base_url": settings.api_base_url,
        "message": message,
    }


def register(mcp: FastMCP) -> None:
    """Register all Zenkit tools on ``mcp``."""
    mcp.add_tool(zenkit_connection_status)
