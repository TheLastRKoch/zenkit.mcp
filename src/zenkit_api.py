"""Authenticated HTTP access layer for the Zenkit REST API."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx
from fastmcp.exceptions import ToolError

from config import API_KEY_ENV_VAR, Settings, SettingsError

API_KEY_HEADER = "Zenkit-API-Key"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_PAGE_SIZE = 100
MAX_PAGES = 100

logger = logging.getLogger(__name__)


def missing_api_key_message() -> str:
    """Return the guidance shown when an API-backed call has no key configured."""
    return (
        f"{API_KEY_ENV_VAR} is not configured. Set {API_KEY_ENV_VAR} to a Zenkit API key "
        "before using Zenkit tools that contact the Zenkit API."
    )


class ZenkitClient:
    """Async client that owns Zenkit authentication, error mapping, and pagination."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if settings.api_key is None:
            raise ToolError(missing_api_key_message())
        self._api_key = settings.api_key
        self._base_url = settings.api_base_url
        self._transport = transport
        self._timeout = timeout
        self._http: httpx.AsyncClient | None = None

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ZenkitClient:
        """Build a client from the environment, refusing to start without an API key."""
        try:
            settings = Settings.from_env(environ)
        except SettingsError as exc:
            raise ToolError(str(exc)) from exc
        return cls(settings, transport=transport, timeout=timeout)

    async def __aenter__(self) -> ZenkitClient:
        self._http = httpx.AsyncClient(
            headers={API_KEY_HEADER: self._api_key, "Accept": "application/json"},
            timeout=httpx.Timeout(self._timeout),
            transport=self._transport,
        )
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> Any:
        """Send a GET request and return the decoded JSON payload."""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, *, json: Any = None) -> Any:
        """Send a POST request with a JSON body and return the decoded JSON payload."""
        return await self._request("POST", path, json=json)

    async def list_entries(
        self,
        list_id: int | str,
        *,
        filter: Mapping[str, Any] | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch up to ``limit`` entries, accumulating pages of ``skip``-offset results."""
        if limit < 1:
            raise ToolError("limit must be at least 1.")
        if skip < 0:
            raise ToolError("skip must be zero or greater.")

        page_size = min(limit, DEFAULT_PAGE_SIZE)
        entries: list[dict[str, Any]] = []
        next_skip = skip

        for _ in range(MAX_PAGES):
            payload: dict[str, Any] = {"limit": page_size, "skip": next_skip}
            if filter is not None:
                payload["filter"] = filter

            page = await self.post(f"/lists/{list_id}/entries/filter", json=payload)
            if not isinstance(page, list) or not all(isinstance(item, dict) for item in page):
                raise ToolError(
                    f"Zenkit returned an unexpected payload for the entries of list {list_id}."
                )

            entries.extend(page)
            if len(page) < page_size or len(entries) >= limit:
                return entries[:limit]
            next_skip += page_size

        raise ToolError(
            f"Zenkit returned more than {MAX_PAGES} pages of entries for list {list_id}. "
            "Narrow the request with a filter or a smaller limit."
        )

    def _url(self, path: str) -> str:
        return f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"

    def _require_http(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("ZenkitClient must be used as an async context manager.")
        return self._http

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        http = self._require_http()
        logger.debug("Zenkit request: %s %s", method, path)

        try:
            response = await http.request(method, self._url(path), params=params, json=json)
        except httpx.TimeoutException:
            raise ToolError(
                f"Zenkit did not respond within {self._timeout:g} seconds for {method} {path}. "
                "Check network connectivity and try again."
            ) from None
        except httpx.HTTPError:
            raise ToolError(
                f"Zenkit could not be reached for {method} {path}. Check network connectivity "
                "and the configured base URL, then try again."
            ) from None

        status = response.status_code
        if status in {401, 403}:
            raise ToolError(
                f"Zenkit rejected the credentials for {method} {path} (HTTP {status}). "
                f"Check that {API_KEY_ENV_VAR} is valid and has access to this resource."
            )
        if status == 404:
            raise ToolError(
                f"Zenkit returned HTTP 404 for {method} {path}: the requested resource does "
                "not exist. Check the id and try again."
            )
        if response.is_error:
            raise ToolError(
                f"Zenkit returned HTTP {status} for {method} {path}. Retry later or check the "
                "request parameters."
            )
        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            raise ToolError(
                f"Zenkit returned a response that is not valid JSON for {method} {path} "
                f"(HTTP {status})."
            ) from None
