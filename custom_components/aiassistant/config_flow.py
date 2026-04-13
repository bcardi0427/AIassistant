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
    CONF_OPENAI_API_KEY,
    CONF_GEMINI_API_KEY,
    CONF_API_URL,
    CONF_GEMINI_API_URL,
    CONF_MODEL,
    CONF_LOG_LEVEL,
    CONF_TEMPERATURE,
    CONF_SYSTEM_PROMPT_FILE,
    CONF_ENABLE_CACHE_CONTROL,
    CONF_USAGE_TRACKING,
    OPENAI_MODELS,
    GEMINI_MODELS,
    DEFAULT_API_URL,
    DEFAULT_GEMINI_API_URL,
    DEFAULT_MODEL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_USAGE_TRACKING,
)

_LOGGER = logging.getLogger(__name__)

async def fetch_openai_models(api_key: str, api_url: str | None = None) -> list[str]:
    """Fetch available models from the OpenAI API."""
    if not api_key:
        return []
    
    base_url = api_url or DEFAULT_API_URL
    base_url = base_url.rstrip("/")
    models_url = f"{base_url}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(models_url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    _LOGGER.warning("Failed to fetch models from OpenAI: HTTP %s", response.status)
                    return []
                
                data = await response.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                models = [m for m in models if m]
                models.sort()
                
                _LOGGER.info("Fetched %d models from OpenAI", len(models))
                return models
                
    except Exception as err:
        _LOGGER.warning("Error fetching models from OpenAI: %s", err)
        return []


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    if not data.get(CONF_OPENAI_API_KEY) and not data.get(CONF_GEMINI_API_KEY):
        raise ValueError("At least one API key (OpenAI or Gemini) is required")

    return {"title": "AIassistant"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AIassistant."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - API Keys."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_OPENAI_API_KEY) and not user_input.get(CONF_GEMINI_API_KEY):
                errors["base"] = "missing_keys"
            else:
                self._data.update(user_input)
                return await self.async_step_configure()

        schema = vol.Schema({
            vol.Optional(CONF_OPENAI_API_KEY, default=""): cv.string,
            vol.Optional(CONF_GEMINI_API_KEY, default=""): cv.string,
            vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): cv.string,
            vol.Optional(CONF_GEMINI_API_URL, default=DEFAULT_GEMINI_API_URL): cv.string,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the configuration step - model selection and options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            try:
                info = await validate_input(self.hass, self._data)
            except ValueError as err:
                _LOGGER.error("Validation error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id("aiassistant")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=self._data)

        # Build model choices
        model_choices = []
        
        # Load OpenAI models if key is present
        if self._data.get(CONF_OPENAI_API_KEY):
            fetched_openai = await fetch_openai_models(
                self._data[CONF_OPENAI_API_KEY], 
                self._data.get(CONF_API_URL)
            )
            if fetched_openai:
                model_choices.extend(fetched_openai)
            else:
                model_choices.extend(OPENAI_MODELS)
                
        # Load Gemini models if key is present
        if self._data.get(CONF_GEMINI_API_KEY):
            model_choices.extend(GEMINI_MODELS)
            
        # Add custom option
        if "custom" not in model_choices:
            model_choices.append("custom")

        default_model = model_choices[0] if model_choices else DEFAULT_MODEL

        schema = vol.Schema({
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # We want to update config data, so we can access it through title="" and data=
            return self.async_create_entry(title="", data=user_input)

        # Get current keys
        current_openai_key = self.config_entry.data.get(CONF_OPENAI_API_KEY, "")
        current_gemini_key = self.config_entry.data.get(CONF_GEMINI_API_KEY, "")
        current_api_url = self.config_entry.data.get(CONF_API_URL, DEFAULT_API_URL)
        current_gemini_url = self.config_entry.data.get(CONF_GEMINI_API_URL, DEFAULT_GEMINI_API_URL)
        
        # Build models list
        model_choices = []
        if current_openai_key:
            fetched_openai = await fetch_openai_models(current_openai_key, current_api_url)
            model_choices.extend(fetched_openai if fetched_openai else OPENAI_MODELS)
        if current_gemini_key:
            model_choices.extend(GEMINI_MODELS)
            
        if "custom" not in model_choices:
            model_choices.append("custom")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_OPENAI_API_KEY,
                    default=current_openai_key
                ): cv.string,
                vol.Optional(
                    CONF_GEMINI_API_KEY,
                    default=current_gemini_key
                ): cv.string,
                vol.Optional(
                    CONF_API_URL,
                    default=current_api_url
                ): cv.string,
                vol.Optional(
                    CONF_GEMINI_API_URL,
                    default=current_gemini_url
                ): cv.string,
                vol.Optional(
                    CONF_MODEL,
                    default=self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)
                ): cv.string,  # String fallback
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
