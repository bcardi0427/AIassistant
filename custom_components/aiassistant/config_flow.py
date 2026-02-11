"""Config flow for AIassistant integration."""
from __future__ import annotations

import logging
from typing import Any
import aiohttp

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
    PROVIDER_OPENAI,
    PROVIDER_GEMINI,
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENROUTER,
    PROVIDER_OLLAMA,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_USAGE_TRACKING,
)

_LOGGER = logging.getLogger(__name__)


async def fetch_models_from_provider(
    provider: str, api_key: str, api_url: str | None = None
) -> list[str]:
    """Fetch available models from the provider's API.
    
    Returns a list of model IDs, or an empty list if fetching fails.
    """
    if not api_key and provider != PROVIDER_OLLAMA:
        return []
    
    # Determine the base URL
    base_url = api_url or PROVIDER_URLS.get(provider, "")
    if not base_url:
        return []
    
    # Remove trailing slash
    base_url = base_url.rstrip("/")
    
    headers = {}
    models_url = ""
    
    try:
        if provider == PROVIDER_OPENAI:
            models_url = f"{base_url}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        
        elif provider == PROVIDER_ANTHROPIC:
            models_url = f"{base_url}/models"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        
        elif provider == PROVIDER_OPENROUTER:
            models_url = f"{base_url}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        
        elif provider == PROVIDER_OLLAMA:
            # Ollama uses a different endpoint
            models_url = base_url.replace("/v1", "/api/tags")
            # Ollama doesn't require auth
        
        elif provider == PROVIDER_GEMINI:
            # Google Gemini doesn't have a standard models list endpoint
            # Return the static list
            return PROVIDER_MODELS.get(PROVIDER_GEMINI, [])
        
        else:
            # Custom or unknown provider - return empty
            return []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(models_url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    _LOGGER.warning(
                        "Failed to fetch models from %s: HTTP %s",
                        provider, response.status
                    )
                    return []
                
                data = await response.json()
                
                # Parse the response based on provider format
                if provider == PROVIDER_OLLAMA:
                    # Ollama format: {"models": [{"name": "llama3.3", ...}, ...]}
                    models = [m.get("name", "") for m in data.get("models", [])]
                elif provider == PROVIDER_OPENROUTER:
                    # OpenRouter format: {"data": [{"id": "openai/gpt-5.2", ...}, ...]}
                    models = [m.get("id", "") for m in data.get("data", [])]
                else:
                    # OpenAI/Anthropic format: {"data": [{"id": "gpt-5.2", ...}, ...]}
                    models = [m.get("id", "") for m in data.get("data", [])]
                
                # Filter out empty strings and return
                models = [m for m in models if m]
                
                # Sort models for better UX
                models.sort()
                
                _LOGGER.info("Fetched %d models from %s", len(models), provider)
                return models
                
    except aiohttp.ClientError as err:
        _LOGGER.warning("Network error fetching models from %s: %s", provider, err)
        return []
    except Exception as err:
        _LOGGER.warning("Error fetching models from %s: %s", provider, err)
        return []


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from the schema with values provided by the user.
    """
    # Validate that we have an API key (except for Ollama)
    provider = data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
    if not data.get(CONF_API_KEY) and provider != PROVIDER_OLLAMA:
        raise ValueError("API key is required")

    # Test the API connection
    try:
        import openai
        import os

        api_url = data.get(CONF_API_URL) or PROVIDER_URLS.get(provider, "")
        
        # Simple test to verify API access
        client = openai.AsyncOpenAI(
            api_key=data.get(CONF_API_KEY) or "ollama",
            base_url=api_url
        )

        # Try to list models (minimal API call)
        try:
            models = await client.models.list()
            _LOGGER.debug("Successfully connected to API, found models")
        except Exception as e:
            # Some APIs don't support model listing, that's OK
            _LOGGER.debug("Model listing not supported (this is OK): %s", str(e))

    except Exception as err:
        _LOGGER.error("Failed to validate API connection: %s", err)
        raise ValueError(f"Cannot connect to API: {err}")

    return {"title": "AIassistant"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AIassistant."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._provider: str | None = None
        self._api_key: str | None = None
        self._api_url: str | None = None
        self._fetched_models: list[str] = []
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - provider selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            self._data[CONF_PROVIDER] = self._provider
            return await self.async_step_credentials()

        # Provider selection schema
        schema = vol.Schema({
            vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(PROVIDERS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the credentials step - get API key and fetch models."""
        errors: dict[str, str] = {}
        provider = self._provider or DEFAULT_PROVIDER

        if user_input is not None:
            self._api_key = user_input.get(CONF_API_KEY, "")
            self._api_url = user_input.get(CONF_API_URL, "") or PROVIDER_URLS.get(provider, "")
            self._data[CONF_API_KEY] = self._api_key
            self._data[CONF_API_URL] = self._api_url
            
            # Fetch models from the provider
            self._fetched_models = await fetch_models_from_provider(
                provider, self._api_key, self._api_url
            )
            
            # If we got models, go to model selection
            # If not, fall back to static list or text input
            return await self.async_step_configure()

        # Get default URL for this provider
        default_url = PROVIDER_URLS.get(provider, "")

        # Build the schema
        if provider == PROVIDER_CUSTOM:
            schema = vol.Schema({
                vol.Required(CONF_API_URL): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
            })
        elif provider == PROVIDER_OLLAMA:
            schema = vol.Schema({
                vol.Optional(CONF_API_URL, default=default_url): cv.string,
                vol.Optional(CONF_API_KEY, default=""): cv.string,
            })
        else:
            schema = vol.Schema({
                vol.Optional(CONF_API_URL, default=default_url): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
            })

        return self.async_show_form(
            step_id="credentials",
            data_schema=schema,
            errors=errors,
            description_placeholders={"provider": provider.title()},
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the configuration step - model selection and options."""
        errors: dict[str, str] = {}
        provider = self._provider or DEFAULT_PROVIDER

        if user_input is not None:
            # Merge with previous data
            self._data.update(user_input)
            
            # If API URL is empty, use provider default
            if not self._data.get(CONF_API_URL):
                self._data[CONF_API_URL] = PROVIDER_URLS.get(provider, "")

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
                await self.async_set_unique_id("aiassistant")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=self._data)

        # Build model choices - use fetched models or fall back to static list
        if self._fetched_models:
            model_choices = self._fetched_models
            _LOGGER.info("Using %d fetched models for selection", len(model_choices))
        else:
            model_choices = list(PROVIDER_MODELS.get(provider, []))
            _LOGGER.info("Using static model list (%d models)", len(model_choices))
        
        # Add a "custom" option if not already present
        if "custom" not in model_choices:
            model_choices = list(model_choices) + ["custom"]
        
        # Get default model for this provider
        if self._fetched_models:
            # Use first fetched model as default
            default_model = self._fetched_models[0] if self._fetched_models else DEFAULT_MODEL
        else:
            provider_models = PROVIDER_MODELS.get(provider, [])
            default_model = provider_models[0] if provider_models else DEFAULT_MODEL

        # Build the schema based on whether we have fetched models
        if provider == PROVIDER_CUSTOM or not model_choices:
            # Custom provider or no models - use text input
            schema = vol.Schema({
                vol.Required(CONF_MODEL): cv.string,
                vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): vol.In(["debug", "info", "warning", "error"]),
                vol.Optional(CONF_TEMPERATURE): vol.Coerce(float),
                vol.Optional(CONF_SYSTEM_PROMPT_FILE): cv.string,
                vol.Optional(CONF_ENABLE_CACHE_CONTROL, default=False): cv.boolean,
                vol.Optional(CONF_USAGE_TRACKING, default=DEFAULT_USAGE_TRACKING): vol.In(["stream_options", "usage", "disabled"]),
            })
        else:
            # Known provider with models - show dropdown
            schema = vol.Schema({
                vol.Required(CONF_MODEL, default=default_model): vol.In(model_choices),
                vol.Optional(CONF_LOG_LEVEL, default=DEFAULT_LOG_LEVEL): vol.In(["debug", "info", "warning", "error"]),
                vol.Optional(CONF_TEMPERATURE): vol.Coerce(float),
                vol.Optional(CONF_SYSTEM_PROMPT_FILE): cv.string,
                vol.Optional(CONF_ENABLE_CACHE_CONTROL, default=False): cv.boolean,
                vol.Optional(CONF_USAGE_TRACKING, default=DEFAULT_USAGE_TRACKING): vol.In(["stream_options", "usage", "disabled"]),
            })

        # Show number of models found
        models_count = len(self._fetched_models) if self._fetched_models else len(PROVIDER_MODELS.get(provider, []))

        return self.async_show_form(
            step_id="configure",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "provider": provider.title(),
                "models_count": str(models_count),
            },
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
    """Handle options flow for AIassistant."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._fetched_models: list[str] = []

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

        # Get current provider and try to fetch models
        current_provider = self.config_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
        current_api_key = self.config_entry.data.get(CONF_API_KEY, "")
        current_api_url = self.config_entry.data.get(CONF_API_URL, "")
        
        # Fetch models dynamically
        self._fetched_models = await fetch_models_from_provider(
            current_provider, current_api_key, current_api_url
        )
        
        if self._fetched_models:
            model_choices = self._fetched_models
        else:
            model_choices = list(PROVIDER_MODELS.get(current_provider, []))
        
        # Add custom option
        if "custom" not in model_choices:
            model_choices = list(model_choices) + ["custom"]

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
                    CONF_API_KEY,
                    default=self.config_entry.data.get(CONF_API_KEY, "")
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
            description_placeholders={
                "models_count": str(len(self._fetched_models)) if self._fetched_models else "static list",
            },
        )
