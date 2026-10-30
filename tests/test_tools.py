"""Tests for Zenkit tools, exercised through FastMCP's in-memory client."""

from __future__ import annotations

import json
import logging
import socket
from collections.abc import Iterator, Mapping
from typing import Any

import httpx
import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from config import API_BASE_URL_ENV_VAR, API_KEY_ENV_VAR, DEFAULT_API_BASE_URL
from tools.zenkit import _identity_result, register
from zenkit_api import ZenkitClient

TEST_API_KEY = "test-api-key"
TEST_BASE_URL = "https://example.test/api/v1"
TITLE_ELEMENT_UUID = "c0148d60-c58a-4e17-89b6-3f5cc0c0785b"
TITLE_FIELD_KEY = f"{TITLE_ELEMENT_UUID}_text"
NEW_TOOL_NAMES = (
    "zenkit_get_current_user",
    "zenkit_list_lists",
    "zenkit_get_list",
    "zenkit_list_columns",
    "zenkit_get_entries",
    "zenkit_get_entry",
    "zenkit_create_entry",
)


class StubZenkit:
    """Records requests made through the client and replies from a configured table."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self._responses: dict[tuple[str, str], tuple[int, Any]] = {}

    def reply(self, method: str, path: str, payload: Any, status: int = 200) -> None:
        self._responses[(method, path)] = (status, payload)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        status, payload = self._responses.get(
            (request.method, self._path(request)), (404, {"error": "not found"})
        )
        return httpx.Response(status, json=payload)

    def bodies(self, method: str, path: str) -> list[Any]:
        return [
            json.loads(request.content)
            for request in self.requests
            if request.method == method and self._path(request) == path
        ]

    @staticmethod
    def _path(request: httpx.Request) -> str:
        return request.url.path.removeprefix("/api/v1")


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


@pytest.fixture
def zenkit(monkeypatch: pytest.MonkeyPatch) -> Iterator[StubZenkit]:
    """Route every tool call through a stubbed transport with a configured test key."""
    stub = StubZenkit()
    transport = httpx.MockTransport(stub.handler)
    original_from_env = ZenkitClient.from_env.__func__

    def from_env(
        cls: type[ZenkitClient],
        environ: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> ZenkitClient:
        kwargs.setdefault("transport", transport)
        return original_from_env(cls, environ, **kwargs)

    monkeypatch.setattr(ZenkitClient, "from_env", classmethod(from_env))
    monkeypatch.setenv(API_KEY_ENV_VAR, TEST_API_KEY)
    monkeypatch.setenv(API_BASE_URL_ENV_VAR, TEST_BASE_URL)
    yield stub


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


async def test_get_current_user_returns_authenticated_user(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply("GET", "/users/me", {"id": 7, "displayname": "Ada Lovelace"})

    async with Client(server) as client:
        result = await client.call_tool("zenkit_get_current_user", {})

    assert result.data["id"] == 7
    assert result.data["displayname"] == "Ada Lovelace"
    assert str(zenkit.requests[0].url) == f"{TEST_BASE_URL}/users/me"
    assert zenkit.requests[0].headers["Zenkit-API-Key"] == TEST_API_KEY


async def test_get_current_user_rejects_invalid_credentials(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply("GET", "/users/me", {"error": "unauthorized"}, status=401)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="credentials"):
            await client.call_tool("zenkit_get_current_user", {})


def test_identity_result_drops_credential_keys() -> None:
    user = {
        "id": 7,
        "displayname": "Ada Lovelace",
        "api_key": "leaked-key-value",
        "session": {"refreshToken": "leaked-refresh", "token": "leaked-token"},
        "unmapped": "dropped",
    }

    result = _identity_result(user)
    rendered = repr(result)

    assert result["id"] == 7
    assert result["displayname"] == "Ada Lovelace"
    assert set(result) == {"id", "displayname"}
    assert "leaked-key-value" not in rendered
    assert "leaked-refresh" not in rendered
    assert "leaked-token" not in rendered


async def test_get_current_user_omits_credentials_from_the_payload(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply(
        "GET",
        "/users/me",
        {
            "id": 7,
            "displayname": "Ada Lovelace",
            "username": "ada",
            "emails": [{"email": "ada@example.test", "verified": True}],
            "api_key": "leaked-key-value",
            "refreshToken": "leaked-refresh",
        },
    )

    async with Client(server) as client:
        result = await client.call_tool("zenkit_get_current_user", {})

    assert result.data["id"] == 7
    assert result.data["displayname"] == "Ada Lovelace"
    assert result.data["emails"] == [{"email": "ada@example.test", "verified": True}]
    assert "api_key" not in result.data
    assert "refreshToken" not in result.data


async def test_list_lists_returns_lists_with_workspace_context(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply(
        "GET",
        "/users/me/workspacesWithLists",
        [
            {
                "id": 1,
                "name": "Work",
                "lists": [
                    {"id": "Hb6sAdzINt", "name": "Sprint"},
                    {"id": 3639611, "name": "Backlog"},
                ],
            },
            {"id": 2, "name": "Home", "lists": []},
        ],
    )

    async with Client(server) as client:
        result = await client.call_tool("zenkit_list_lists", {})

    assert result.data == [
        {
            "id": "Hb6sAdzINt",
            "name": "Sprint",
            "workspace_id": 1,
            "workspace_name": "Work",
        },
        {"id": 3639611, "name": "Backlog", "workspace_id": 1, "workspace_name": "Work"},
    ]


async def test_get_list_returns_the_requested_list(server: FastMCP, zenkit: StubZenkit) -> None:
    zenkit.reply("GET", "/lists/3639611", {"id": 3639611, "name": "Backlog"})

    async with Client(server) as client:
        result = await client.call_tool("zenkit_get_list", {"list_id": 3639611})

    assert result.data["id"] == 3639611
    assert result.data["name"] == "Backlog"


async def test_get_list_unknown_list_raises_tool_error(server: FastMCP, zenkit: StubZenkit) -> None:
    async with Client(server) as client:
        with pytest.raises(ToolError, match="404"):
            await client.call_tool("zenkit_get_list", {"list_id": "missing"})


async def test_list_columns_carry_identifier_name_and_type(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply(
        "GET",
        "/lists/3639611/elements",
        [
            {
                "id": 41102987,
                "uuid": TITLE_ELEMENT_UUID,
                "name": "Title",
                "dataType": "text",
                "resourceRole": "title",
            }
        ],
    )

    async with Client(server) as client:
        result = await client.call_tool("zenkit_list_columns", {"list_id": 3639611})

    column = result.data[0]
    assert column["id"] == 41102987
    assert column["name"] == "Title"
    assert column["data_type"] == "text"


DERIVED_COLUMN_CASES = (
    ("Text", {"text": "x", "searchText": "x", "textType": "plain"}, "text"),
    ("Notes", {"text": "x", "searchText": "x", "textType": "html"}, "text"),
    ("Due", {"date": 1700000000, "endDate": None, "hasTime": False, "duration": 0}, "date"),
    ("Stage", {"categories": [], "categories_sort": []}, "categories"),
    ("Assignee", {"persons": [], "persons_sort": []}, "persons"),
    ("Attachment", {"files": [], "filesData": {}}, "files"),
    ("Points", {"number": 4, "numberText": "4"}, "number"),
    (
        "Parent",
        {"connected": [], "references": [], "parents": [], "path": "", "sortOrder": 1},
        "references",
    ),
)


def _element(index: int, name: str, business_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": 5000 + index,
        "uuid": f"{index:08x}-0000-4000-8000-000000000000",
        "name": name,
        "dataType": None,
        "resourceRole": None,
        "businessData": business_data,
    }


async def test_list_columns_derives_data_type_from_business_data(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    elements = [
        _element(index, name, business_data)
        for index, (name, business_data, _) in enumerate(DERIVED_COLUMN_CASES)
    ]
    elements.append(_element(len(elements), "Created", {}))
    zenkit.reply("GET", "/lists/3639611/elements", elements)

    async with Client(server) as client:
        result = await client.call_tool("zenkit_list_columns", {"list_id": 3639611})

    assert [column["data_type"] for column in result.data] == [
        expected for _, _, expected in DERIVED_COLUMN_CASES
    ] + [None]
    assert result.data[0]["id"] == 5000
    assert result.data[0]["uuid"] == "00000000-0000-4000-8000-000000000000"
    assert result.data[0]["name"] == "Text"
    assert result.data[0]["resource_role"] is None


async def test_list_columns_prefers_a_reported_data_type(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply(
        "GET",
        "/lists/3639611/elements",
        [{"id": 1, "uuid": TITLE_ELEMENT_UUID, "name": "Title", "dataType": "text"}],
    )

    async with Client(server) as client:
        result = await client.call_tool("zenkit_list_columns", {"list_id": 3639611})

    assert result.data[0]["data_type"] == "text"


async def test_column_data_type_matches_entry_field_key_suffix(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    elements = [
        _element(index, name, business_data)
        for index, (name, business_data, _) in enumerate(DERIVED_COLUMN_CASES)
    ]
    zenkit.reply("GET", "/lists/3639611/elements", elements)
    entry_fields = {
        f"{element['uuid']}_{expected}": None
        for element, (_, _, expected) in zip(elements, DERIVED_COLUMN_CASES, strict=True)
    }
    zenkit.reply(
        "POST",
        "/lists/3639611/entries/filter",
        [{"id": 1, "uuid": "entry-1", **entry_fields}],
    )

    async with Client(server) as client:
        columns = (await client.call_tool("zenkit_list_columns", {"list_id": 3639611})).data
        entries = (await client.call_tool("zenkit_get_entries", {"list_id": 3639611})).data

    types_by_uuid = {column["uuid"]: column["data_type"] for column in columns}
    field_keys = entries[0]["fields"]
    assert field_keys
    for field_key in field_keys:
        element_uuid, _, suffix = field_key.rpartition("_")
        assert types_by_uuid[element_uuid] == suffix


async def test_get_entries_honors_filter_and_window(server: FastMCP, zenkit: StubZenkit) -> None:
    zenkit.reply(
        "POST",
        "/lists/3639611/entries/filter",
        [
            {"id": 1, "uuid": "entry-1", "listId": 3639611, TITLE_FIELD_KEY: "First"},
            {"id": 2, "uuid": "entry-2", "listId": 3639611, TITLE_FIELD_KEY: "Second"},
        ],
    )
    entry_filter = {"AND": {"TERMS": [{"elementId": 41102987, "modus": "equals"}]}}

    async with Client(server) as client:
        result = await client.call_tool(
            "zenkit_get_entries",
            {"list_id": 3639611, "filter": entry_filter, "limit": 2, "skip": 10},
        )

    assert [entry["id"] for entry in result.data] == [1, 2]
    assert result.data[0]["fields"] == {TITLE_FIELD_KEY: "First"}
    assert "listId" not in result.data[0]
    assert zenkit.bodies("POST", "/lists/3639611/entries/filter") == [
        {"limit": 2, "skip": 10, "filter": entry_filter}
    ]


async def test_get_entries_for_empty_list_returns_empty_collection(
    server: FastMCP, zenkit: StubZenkit
) -> None:
    zenkit.reply("POST", "/lists/1/entries/filter", [])

    async with Client(server) as client:
        result = await client.call_tool("zenkit_get_entries", {"list_id": 1})

    assert result.data == []


async def test_get_entry_returns_single_entry(server: FastMCP, zenkit: StubZenkit) -> None:
    zenkit.reply(
        "GET",
        "/lists/3639611/entries/161",
        {"id": 161, "uuid": "entry-uuid", TITLE_FIELD_KEY: "Task"},
    )

    async with Client(server) as client:
        result = await client.call_tool("zenkit_get_entry", {"list_id": 3639611, "entry_id": 161})

    assert result.data["id"] == 161
    assert result.data["fields"] == {TITLE_FIELD_KEY: "Task"}


async def test_create_entry_posts_documented_body(server: FastMCP, zenkit: StubZenkit) -> None:
    fields = {TITLE_FIELD_KEY: "Testing API"}
    zenkit.reply(
        "POST",
        "/lists/3639611/entries",
        {"id": 999, "uuid": "new-entry-uuid", **fields},
        status=201,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "zenkit_create_entry", {"list_id": 3639611, "fields": fields}
        )

    assert zenkit.bodies("POST", "/lists/3639611/entries") == [fields]
    assert result.data["id"] == 999


async def test_tool_results_and_logs_never_expose_the_api_key(
    server: FastMCP, zenkit: StubZenkit, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    zenkit.reply("GET", "/users/me", {"id": 7, "displayname": "Ada Lovelace"})

    async with Client(server) as client:
        result = await client.call_tool("zenkit_get_current_user", {})

    assert TEST_API_KEY not in repr(result)
    assert TEST_API_KEY not in str(result)
    assert TEST_API_KEY not in caplog.text


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("zenkit_get_current_user", {}),
        ("zenkit_list_lists", {}),
        ("zenkit_get_list", {"list_id": 1}),
        ("zenkit_list_columns", {"list_id": 1}),
        ("zenkit_get_entries", {"list_id": 1}),
        ("zenkit_get_entry", {"list_id": 1, "entry_id": 2}),
        ("zenkit_create_entry", {"list_id": 1, "fields": {}}),
    ],
)
async def test_api_tools_require_a_configured_api_key(
    server: FastMCP, tool_name: str, arguments: dict[str, Any]
) -> None:
    async with Client(server) as client:
        with pytest.raises(ToolError, match=API_KEY_ENV_VAR):
            await client.call_tool(tool_name, arguments)


async def test_api_tools_are_discoverable(server: FastMCP) -> None:
    async with Client(server) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    for name in NEW_TOOL_NAMES:
        assert name in tools, f"{name} is not registered"
        assert tools[name].description
        assert tools[name].input_schema["type"] == "object"

    assert tools["zenkit_get_current_user"].input_schema.get("properties", {}) == {}
    assert set(tools["zenkit_get_list"].input_schema["properties"]) == {"list_id"}
    assert set(tools["zenkit_get_entries"].input_schema["properties"]) == {
        "list_id",
        "filter",
        "limit",
        "skip",
    }
    assert set(tools["zenkit_create_entry"].input_schema["properties"]) == {"list_id", "fields"}
    assert tools["zenkit_get_entry"].input_schema["required"] == ["list_id", "entry_id"]
