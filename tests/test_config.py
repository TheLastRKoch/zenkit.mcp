"""Tests for environment-driven configuration."""

import pytest

from config import (
    API_BASE_URL_ENV_VAR,
    API_KEY_ENV_VAR,
    DEFAULT_API_BASE_URL,
    Settings,
    SettingsError,
    validate_api_base_url,
)


def test_defaults_apply_without_environment() -> None:
    settings = Settings.from_env({})

    assert settings.api_key is None
    assert settings.configured is False
    assert settings.api_base_url == DEFAULT_API_BASE_URL


def test_api_key_is_read_from_environment() -> None:
    settings = Settings.from_env({API_KEY_ENV_VAR: "test-key"})

    assert settings.api_key == "test-key"
    assert settings.configured is True


def test_blank_api_key_is_treated_as_absent() -> None:
    settings = Settings.from_env({API_KEY_ENV_VAR: "   "})

    assert settings.api_key is None
    assert settings.configured is False


def test_base_url_override_is_applied() -> None:
    settings = Settings.from_env({API_BASE_URL_ENV_VAR: "https://example.test/api/v1"})

    assert settings.api_base_url == "https://example.test/api/v1"


@pytest.mark.parametrize(
    "value",
    ["", "zenkit.com/api/v1", "ftp://zenkit.com/api/v1", "https://", "/relative/path"],
)
def test_invalid_base_url_is_rejected(value: str) -> None:
    with pytest.raises(SettingsError, match=API_BASE_URL_ENV_VAR):
        validate_api_base_url(value)


def test_settings_are_immutable() -> None:
    settings = Settings(api_key=None, api_base_url=DEFAULT_API_BASE_URL)

    with pytest.raises(AttributeError):
        settings.api_key = "other"  # type: ignore[misc]
