"""Tests for the Zenkit HTTP client, driven through a mocked transport."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterator, Mapping
from typing import Any

import httpx
import pytest
from fastmcp.exceptions import ToolError

import zenkit_api
from config import API_BASE_URL_ENV_VAR, API_KEY_ENV_VAR
from zenkit_api import API_KEY_HEADER, DEFAULT_PAGE_SIZE, ZenkitClient

API_KEY = "test-zenkit-api-key"
BASE_URL = "https://example.test/api/v1"

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    monkeypatch.delenv(API_BASE_URL_ENV_VAR, raising=False)
    yield


def make_client(handler: Handler, environ: Mapping[str, str] | None = None) -> ZenkitClient:
    env = {API_KEY_ENV_VAR: API_KEY, API_BASE_URL_ENV_VAR: BASE_URL} if environ is None else environ
    return ZenkitClient.from_env(env, transport=httpx.MockTransport(handler))


async def test_request_sends_api_key_header_and_resolves_base_url() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 7})

    async with make_client(handler) as client:
        payload = await client.get("/users/me")

    assert payload == {"id": 7}
    assert len(seen) == 1
    assert seen[0].headers[API_KEY_HEADER] == API_KEY
    assert str(seen[0].url) == f"{BASE_URL}/users/me"


@pytest.mark.parametrize("status", [400, 500, 503])
async def test_error_status_becomes_tool_error(status: int) -> None:
    async with make_client(lambda request: httpx.Response(status, json={})) as client:
        with pytest.raises(ToolError, match=f"HTTP {status}"):
            await client.get("/users/me")


@pytest.mark.parametrize("status", [401, 403])
async def test_rejected_credentials_name_the_api_key_variable(status: int) -> None:
    async with make_client(lambda request: httpx.Response(status, json={})) as client:
        with pytest.raises(ToolError, match=API_KEY_ENV_VAR) as excinfo:
            await client.get("/users/me")

    assert f"HTTP {status}" in str(excinfo.value)


async def test_malformed_json_becomes_tool_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    async with make_client(handler) as client:
        with pytest.raises(ToolError, match="not valid JSON"):
            await client.get("/users/me")


async def test_timeout_becomes_tool_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async with make_client(handler) as client:
        with pytest.raises(ToolError, match="did not respond"):
            await client.get("/users/me")


async def test_unreachable_service_becomes_tool_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with make_client(handler) as client:
        with pytest.raises(ToolError, match="could not be reached"):
            await client.get("/users/me")


async def test_missing_api_key_fails_before_any_request() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={})

    with pytest.raises(ToolError, match=API_KEY_ENV_VAR):
        async with make_client(handler, environ={}):
            pass

    assert seen == []


async def test_invalid_base_url_becomes_tool_error() -> None:
    with pytest.raises(ToolError, match=API_BASE_URL_ENV_VAR):
        ZenkitClient.from_env({API_KEY_ENV_VAR: API_KEY, API_BASE_URL_ENV_VAR: "not-a-url"})


async def test_api_key_never_appears_in_results_errors_or_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    async with make_client(lambda request: httpx.Response(200, json={"id": 7})) as client:
        result = await client.get("/users/me")
        client_repr = repr(client)

    async with make_client(lambda request: httpx.Response(500, json={})) as client:
        with pytest.raises(ToolError) as excinfo:
            await client.get("/users/me")

    assert API_KEY not in repr(result)
    assert API_KEY not in client_repr
    assert API_KEY not in str(excinfo.value)
    assert API_KEY not in caplog.text


async def test_entries_from_all_pages_are_assembled_in_order() -> None:
    pages = {
        0: [{"id": entry_id} for entry_id in range(1, DEFAULT_PAGE_SIZE + 1)],
        100: [{"id": entry_id} for entry_id in range(101, 105)],
    }
    bodies: list[dict[str, Any]] = []
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        bodies.append(body)
        urls.append(str(request.url))
        return httpx.Response(200, json=pages.get(body["skip"], []))

    async with make_client(handler) as client:
        entries = await client.list_entries("3639611", limit=250)

    assert [entry["id"] for entry in entries] == list(range(1, 105))
    assert [body["skip"] for body in bodies] == [0, DEFAULT_PAGE_SIZE]
    assert all(body["limit"] == DEFAULT_PAGE_SIZE for body in bodies)
    assert urls[0] == f"{BASE_URL}/lists/3639611/entries/filter"


async def test_filter_and_window_are_sent_verbatim() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    async with make_client(handler) as client:
        entries = await client.list_entries(3639611, filter={"AND": {}}, limit=2, skip=40)

    assert [entry["id"] for entry in entries] == [1, 2]
    assert len(seen) == 1
    assert json.loads(seen[0].content) == {"limit": 2, "skip": 40, "filter": {"AND": {}}}
    assert str(seen[0].url) == f"{BASE_URL}/lists/3639611/entries/filter"


async def test_pagination_stops_at_the_iteration_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(zenkit_api, "MAX_PAGES", 2)
    full_page = [{"id": entry_id} for entry_id in range(DEFAULT_PAGE_SIZE)]

    async with make_client(lambda request: httpx.Response(200, json=full_page)) as client:
        with pytest.raises(ToolError, match="pages of entries"):
            await client.list_entries("1", limit=DEFAULT_PAGE_SIZE * 3)


@pytest.mark.parametrize(("limit", "skip", "fragment"), [(0, 0, "limit"), (10, -1, "skip")])
async def test_invalid_window_parameters_are_rejected(limit: int, skip: int, fragment: str) -> None:
    async with make_client(lambda request: httpx.Response(200, json=[])) as client:
        with pytest.raises(ToolError, match=fragment):
            await client.list_entries("1", limit=limit, skip=skip)


async def test_empty_response_body_returns_none() -> None:
    async with make_client(lambda request: httpx.Response(204)) as client:
        assert await client.get("/users/me") is None
