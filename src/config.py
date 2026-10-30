"""Runtime configuration for the Zenkit MCP server."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_API_BASE_URL = "https://zenkit.com/api/v1"
API_KEY_ENV_VAR = "ZENKIT_API_KEY"
API_BASE_URL_ENV_VAR = "ZENKIT_API_BASE_URL"


class SettingsError(ValueError):
    """Raised when the environment configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    """Zenkit connection settings resolved from the process environment."""

    api_key: str | None
    api_base_url: str

    @property
    def configured(self) -> bool:
        """Whether an API key is available for future API calls."""
        return self.api_key is not None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Build settings from environment variables, applying defaults and validation."""
        env = os.environ if environ is None else environ
        api_key = env.get(API_KEY_ENV_VAR, "").strip() or None
        api_base_url = env.get(API_BASE_URL_ENV_VAR, "").strip() or DEFAULT_API_BASE_URL
        return cls(api_key=api_key, api_base_url=validate_api_base_url(api_base_url))


def validate_api_base_url(value: str) -> str:
    """Return ``value`` unchanged when it is an absolute HTTPS URL, else raise.

    Only ``https`` is accepted so the ``Zenkit-API-Key`` header is never sent over a plaintext
    connection. The rejected value is not included in the error.
    """
    parts = urlsplit(value)
    if parts.scheme.lower() != "https" or not parts.hostname:
        raise SettingsError(
            f"{API_BASE_URL_ENV_VAR} must be an absolute HTTPS URL "
            f"(for example {DEFAULT_API_BASE_URL})."
        )
    return value
