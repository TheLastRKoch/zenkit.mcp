"""Tools that expose Zenkit functionality to MCP clients."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from config import Settings, SettingsError
from zenkit_api import DEFAULT_PAGE_SIZE, ZenkitClient

_ENTRY_FIELD_KEY = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}_\w+$"
)


def zenkit_connection_status() -> dict[str, Any]:
    """Report whether Zenkit credentials are configured, without calling the Zenkit API."""
    try:
        settings = Settings.from_env()
    except SettingsError as exc:
        raise ToolError(str(exc)) from exc

    if settings.configured:
        message = (
            "Zenkit API key is configured. API-backed tools are available; run "
            "zenkit_get_current_user to validate the key."
        )
    else:
        message = (
            "Zenkit API key is not configured. Set ZENKIT_API_KEY to use the API-backed "
            "Zenkit tools."
        )

    return {
        "configured": settings.configured,
        "api_base_url": settings.api_base_url,
        "message": message,
    }


def _entry_result(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Split a raw Zenkit entry into its identity and custom-column values."""
    fields = {key: value for key, value in entry.items() if _ENTRY_FIELD_KEY.match(key)}
    return {"id": entry.get("id"), "uuid": entry.get("uuid"), "fields": fields}


def _expect(payload: Any, expected: type, description: str) -> Any:
    if not isinstance(payload, expected):
        raise ToolError(f"Zenkit returned an unexpected payload for {description}.")
    return payload


async def zenkit_get_current_user() -> dict[str, Any]:
    """Return the authenticated Zenkit user, validating the configured API key."""
    async with ZenkitClient.from_env() as client:
        payload = await client.get("/users/me")
    return _expect(payload, dict, "the authenticated user")


async def zenkit_list_lists() -> list[dict[str, Any]]:
    """List the Zenkit lists the authenticated user can access, with workspace context."""
    async with ZenkitClient.from_env() as client:
        payload = await client.get("/users/me/workspacesWithLists")

    workspaces = _expect(payload, list, "the accessible workspaces")
    lists: list[dict[str, Any]] = []
    for workspace in workspaces:
        if not isinstance(workspace, dict):
            continue
        for zenkit_list in workspace.get("lists") or []:
            if not isinstance(zenkit_list, dict):
                continue
            lists.append(
                {
                    "id": zenkit_list.get("id"),
                    "name": zenkit_list.get("name"),
                    "workspace_id": workspace.get("id"),
                    "workspace_name": workspace.get("name"),
                }
            )
    return lists


async def zenkit_get_list(list_id: int | str) -> dict[str, Any]:
    """Return a single Zenkit list by id."""
    async with ZenkitClient.from_env() as client:
        payload = await client.get(f"/lists/{list_id}")
    return _expect(payload, dict, f"list {list_id}")


async def zenkit_list_columns(list_id: int | str) -> list[dict[str, Any]]:
    """Return a list's columns (Zenkit elements), each with its id, name, and data type."""
    async with ZenkitClient.from_env() as client:
        payload = await client.get(f"/lists/{list_id}/elements")

    elements = _expect(payload, list, f"the columns of list {list_id}")
    return [
        {
            "id": element.get("id"),
            "uuid": element.get("uuid"),
            "name": element.get("name"),
            "data_type": element.get("dataType"),
            "resource_role": element.get("resourceRole"),
        }
        for element in elements
        if isinstance(element, dict)
    ]


async def zenkit_get_entries(
    list_id: int | str,
    filter: dict[str, Any] | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    skip: int = 0,
) -> list[dict[str, Any]]:
    """Return entries in a Zenkit list, optionally filtered, with limit/skip paging.

    ``filter`` is the Zenkit filter object and is passed through verbatim. ``limit`` is the
    maximum number of entries to return; larger values are fetched in pages of 100. ``skip``
    is the number of entries to skip before collecting results. Each entry carries its ``id``,
    ``uuid``, and ``fields`` (custom column values keyed ``<element-uuid>_<dataType>``).
    """
    async with ZenkitClient.from_env() as client:
        entries = await client.list_entries(list_id, filter=filter, limit=limit, skip=skip)
    return [_entry_result(entry) for entry in entries]


async def zenkit_get_entry(list_id: int | str, entry_id: int | str) -> dict[str, Any]:
    """Return a single entry from a Zenkit list by list id and entry id."""
    async with ZenkitClient.from_env() as client:
        payload = await client.get(f"/lists/{list_id}/entries/{entry_id}")
    entry = _expect(payload, dict, f"entry {entry_id} in list {list_id}")
    return _entry_result(entry)


async def zenkit_create_entry(list_id: int | str, fields: dict[str, Any]) -> dict[str, Any]:
    """Create an entry in a Zenkit list and return the created entry's identifier.

    ``fields`` maps custom column keys of the form ``<element-uuid>_<dataType>`` to values,
    for example ``{"c0148d60-c58a-4e17-89b6-3f5cc0c0785b_text": "Testing API"}``. Use
    zenkit_list_columns to discover an element's uuid and data type.
    """
    async with ZenkitClient.from_env() as client:
        payload = await client.post(f"/lists/{list_id}/entries", json=fields)

    entry = _expect(payload, dict, f"the entry created in list {list_id}")
    return _entry_result(entry)


def register(mcp: FastMCP) -> None:
    """Register all Zenkit tools on ``mcp``."""
    mcp.add_tool(zenkit_connection_status)
    mcp.add_tool(zenkit_get_current_user)
    mcp.add_tool(zenkit_list_lists)
    mcp.add_tool(zenkit_get_list)
    mcp.add_tool(zenkit_list_columns)
    mcp.add_tool(zenkit_get_entries)
    mcp.add_tool(zenkit_get_entry)
    mcp.add_tool(zenkit_create_entry)
