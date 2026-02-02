"""Config flow for AI Configuration Agent integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_URL,
    CONF_MODEL,
    CONF_PROVIDER,
    CONF_LOG_LEVEL,
    CONF_TEMPERATURE,
    CONF_SYSTEM_PROMPT_FILE,
    CONF_ENABLE_CACHE_CONTROL,
    CONF_USAGE_TRACKING,
    PROVIDERS,
    PROVIDER_URLS,
    PROVIDER_MODELS,
    PROVIDER_CUSTOM,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_USAGE_TRACKING,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from the schema with values provided by the user.
    """
    # Validate that we have an API key
    if not data.get(CONF_API_KEY):
        raise ValueError("API key is required")

    # Test the API connection
    try:
        import openai
        import os

        # Temporarily set environment variables for testing
        original_key = os.environ.get("OPENAI_API_KEY")
        original_url = os.environ.get("OPENAI_API_BASE")

        try:
            os.environ["OPENAI_API_KEY"] = data[CONF_API_KEY]
            api_url = data.get(CONF_API_URL) or PROVIDER_URLS.get(data.get(CONF_PROVIDER, DEFAULT_PROVIDER), "")
            if api_url:
                os.environ["OPENAI_API_BASE"] = api_url

            # Simple test to verify API access
            client = openai.OpenAI(
                api_key=data[CONF_API_KEY],
                base_url=api_url
            )

            # Try to list models (minimal API call)
            try:
                models = client.models.list()
                _LOGGER.debug("Successfully connected to API, found %d models", len(list(models)))
            except Exception as e:
                # Some APIs don't support model listing, that's OK
                _LOGGER.debug("Model listing not supported (this is OK): %s", str(e))

        finally:
            # Restore original environment
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            elif "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

            if original_url:
                os.environ["OPENAI_API_BASE"] = original_url
            elif "OPENAI_API_BASE" in os.environ:
                del os.environ["OPENAI_API_BASE"]

    except Exception as err:
        _LOGGER.error("Failed to validate API connection: %s", err)
        raise ValueError(f"Cannot connect to API: {err}")

    return {"title": "AI Configuration Agent"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Configuration Agent."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._provider: str | None = None
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - provider selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            self._data[CONF_PROVIDER] = self._provider
            return await self.async_step_configure()

        # Provider selection schema
        schema = vol.Schema({
            vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(PROVIDERS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the configuration step based on selected provider."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Merge with provider selection
            self._data.update(user_input)
            
            # If API URL is empty, use provider default
            if not self._data.get(CONF_API_URL):
                self._data[CONF_API_URL] = PROVIDER_URLS.get(self._provider, "")

            try:
                info = await validate_input(self.hass, self._data)
            except ValueError as err:
                _LOGGER.error("Validation error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id("ai_config_agent")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=self._data)

        # Build model choices based on provider
        provider = self._provider or DEFAULT_PROVIDER
        model_choices = PROVIDER_MODELS.get(provider, [])
        
        # Add a "custom" option if not already present
        if "custom" not in model_choices:
            model_choices = list(model_choices) + ["custom"]

        # Get default URL for this provider
        default_url = PROVIDER_URLS.get(provider, "")
        
        # Get default model for this provider
        provider_models = PROVIDER_MODELS.get(provider, [])
        default_model = provider_models[0] if provider_models else DEFAULT_MODEL

        # Build the schema
        if provider == PROVIDER_CUSTOM:
            # Custom provider - show text inputs for URL and model
            schema = vol.Schema({
                vol.Required(CONF_API_URL): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_MODEL): cv.string,
                vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): vol.In(["debug", "info", "warning", "error"]),
                vol.Optional(CONF_TEMPERATURE): vol.Coerce(float),
                vol.Optional(CONF_SYSTEM_PROMPT_FILE): cv.string,
                vol.Optional(CONF_ENABLE_CACHE_CONTROL, default=False): cv.boolean,
                vol.Optional(CONF_USAGE_TRACKING, default=DEFAULT_USAGE_TRACKING): vol.In(["stream_options", "usage", "disabled"]),
            })
        else:
            # Known provider - show dropdown for models, prefill URL
            schema = vol.Schema({
                vol.Optional(CONF_API_URL, default=default_url, description={"suggested_value": default_url}): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_MODEL, default=default_model): vol.In(model_choices),
                vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): vol.In(["debug", "info", "warning", "error"]),
                vol.Optional(CONF_TEMPERATURE): vol.Coerce(float),
                vol.Optional(CONF_SYSTEM_PROMPT_FILE): cv.string,
                vol.Optional(CONF_ENABLE_CACHE_CONTROL, default=False): cv.boolean,
                vol.Optional(CONF_USAGE_TRACKING, default=DEFAULT_USAGE_TRACKING): vol.In(["stream_options", "usage", "disabled"]),
            })

        return self.async_show_form(
            step_id="configure",
            data_schema=schema,
            errors=errors,
            description_placeholders={"provider": provider.title()},
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for AI Configuration Agent."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # If API URL is empty, use provider default
            provider = user_input.get(CONF_PROVIDER) or self.config_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
            if not user_input.get(CONF_API_URL):
                user_input[CONF_API_URL] = PROVIDER_URLS.get(provider, "")
            return self.async_create_entry(title="", data=user_input)

        # Get current provider and build model list
        current_provider = self.config_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
        model_choices = list(PROVIDER_MODELS.get(current_provider, [])) + ["custom"]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_PROVIDER,
                    default=self.config_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
                ): vol.In(PROVIDERS),
                vol.Optional(
                    CONF_API_URL,
                    default=self.config_entry.data.get(CONF_API_URL, PROVIDER_URLS.get(current_provider, ""))
                ): cv.string,
                vol.Optional(
                    CONF_MODEL,
                    default=self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)
                ): cv.string,  # Allow any string for flexibility
                vol.Optional(
                    CONF_LOG_LEVEL,
                    default=self.config_entry.data.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)
                ): vol.In(["debug", "info", "warning", "error"]),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=self.config_entry.data.get(CONF_TEMPERATURE)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SYSTEM_PROMPT_FILE,
                    default=self.config_entry.data.get(CONF_SYSTEM_PROMPT_FILE, "")
                ): cv.string,
                vol.Optional(
                    CONF_ENABLE_CACHE_CONTROL,
                    default=self.config_entry.data.get(CONF_ENABLE_CACHE_CONTROL, False)
                ): cv.boolean,
                vol.Optional(
                    CONF_USAGE_TRACKING,
                    default=self.config_entry.data.get(CONF_USAGE_TRACKING, DEFAULT_USAGE_TRACKING)
                ): vol.In(["stream_options", "usage", "disabled"]),
            }),
        )
