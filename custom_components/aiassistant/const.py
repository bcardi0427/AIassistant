"""Constants for the AIassistant integration."""

DOMAIN = "aiassistant"

# Configuration constants
CONF_API_KEY = "api_key"
CONF_API_URL = "api_url"
CONF_MODEL = "model"
CONF_PROVIDER = "provider"
CONF_LOG_LEVEL = "log_level"
CONF_TEMPERATURE = "temperature"
CONF_SYSTEM_PROMPT_FILE = "system_prompt_file"
CONF_ENABLE_CACHE_CONTROL = "enable_cache_control"
CONF_USAGE_TRACKING = "usage_tracking"

# Provider options
PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_OLLAMA = "ollama"
PROVIDER_CUSTOM = "custom"

PROVIDERS = [
    PROVIDER_OPENAI,
    PROVIDER_GEMINI,
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENROUTER,
    PROVIDER_OLLAMA,
    PROVIDER_CUSTOM,
]

# Default API URLs for each provider
PROVIDER_URLS = {
    PROVIDER_OPENAI: "https://api.openai.com/v1",
    PROVIDER_GEMINI: "https://generativelanguage.googleapis.com/v1beta/openai/",
    PROVIDER_ANTHROPIC: "https://api.anthropic.com/v1",
    PROVIDER_OPENROUTER: "https://openrouter.ai/api/v1",
    PROVIDER_OLLAMA: "http://localhost:11434/v1",
    PROVIDER_CUSTOM: "",
}

# Popular models for each provider
PROVIDER_MODELS = {
    PROVIDER_OPENAI: [
        "gpt-5.2",  # Best general choice (early 2026)
        "gpt-5.2-turbo",  # Cheaper/faster variant
        "gpt-5.2-lite",  # Lower-cost for simple tasks
        "gpt-5.2-mini",  # Very low-cost minimal model
        "gpt-5.2-premium",  # Highest quality / longest context
    ],
    PROVIDER_GEMINI: [
        "gemini-3-flash-preview",  # Recommended for Gen 3 (early 2026)
        "gemini-2.5-flash",  # Stable production model
        "gemini-2.5-pro-preview-05-06",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ],
    PROVIDER_ANTHROPIC: [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
    ],
    PROVIDER_OPENROUTER: [
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct",
    ],
    PROVIDER_OLLAMA: [
        "llama3.3",
        "qwen2.5-coder",
        "deepseek-r1",
        "mistral",
    ],
    PROVIDER_CUSTOM: [],
}

# Default values
DEFAULT_PROVIDER = PROVIDER_OPENAI
DEFAULT_API_URL = PROVIDER_URLS[PROVIDER_OPENAI]
DEFAULT_MODEL = "gpt-4o"
DEFAULT_LOG_LEVEL = "info"
DEFAULT_USAGE_TRACKING = "stream_options"
