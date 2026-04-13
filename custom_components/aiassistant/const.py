"""Constants for the AIassistant integration."""

DOMAIN = "aiassistant"

# Configuration constants
CONF_OPENAI_API_KEY = "openai_api_key"
CONF_GEMINI_API_KEY = "gemini_api_key"
CONF_API_URL = "api_url"
CONF_GEMINI_API_URL = "gemini_api_url"
CONF_MODEL = "model"
CONF_LOG_LEVEL = "log_level"
CONF_TEMPERATURE = "temperature"
CONF_SYSTEM_PROMPT_FILE = "system_prompt_file"
CONF_ENABLE_CACHE_CONTROL = "enable_cache_control"
CONF_USAGE_TRACKING = "usage_tracking"

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-5.2",
    "gpt-5.2-turbo",
    "gpt-5.2-lite",
    "gpt-5.2-mini",
    "gpt-5.2-premium",
]

GEMINI_MODELS = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

# Default values
DEFAULT_API_URL = "https://api.openai.com/v1"
DEFAULT_GEMINI_API_URL = "https://generativelanguage.googleapis.com"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_LOG_LEVEL = "info"
DEFAULT_USAGE_TRACKING = "stream_options"
