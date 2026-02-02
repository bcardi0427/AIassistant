#!/usr/bin/with-contenv bashio

# Disable Python output buffering for real-time streaming
export PYTHONUNBUFFERED=1

# Get provider configuration
PROVIDER=$(bashio::config 'provider' "openai")

# Migration: Check for old openai_* keys (backward compatibility)
if bashio::config.exists 'openai_api_key' && ! bashio::config.exists 'api_key'; then
    bashio::log.warning "Found legacy openai_* configuration. Please update to new key names."
    export OPENAI_API_KEY=$(bashio::config 'openai_api_key')
    export OPENAI_API_URL=$(bashio::config 'openai_api_url')
    export OPENAI_MODEL=$(bashio::config 'openai_model')
else
    # Use new configuration keys
    export OPENAI_API_KEY=$(bashio::config 'api_key' "")
    export OPENAI_MODEL=$(bashio::config 'model' "gpt-4o")
    
    # Get API URL - if empty, determine from provider
    API_URL=$(bashio::config 'api_url' "")
    if [[ -z "$API_URL" ]]; then
        case "$PROVIDER" in
            "openai")
                API_URL="https://api.openai.com/v1"
                ;;
            "gemini")
                API_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
                ;;
            "anthropic")
                API_URL="https://api.anthropic.com/v1"
                ;;
            "openrouter")
                API_URL="https://openrouter.ai/api/v1"
                ;;
            "ollama")
                API_URL="http://localhost:11434/v1"
                ;;
            *)
                # Custom or unknown - use OpenAI as fallback
                API_URL="https://api.openai.com/v1"
                ;;
        esac
        bashio::log.info "Auto-configured API URL for provider '${PROVIDER}': ${API_URL}"
    fi
    export OPENAI_API_URL="$API_URL"
fi

# Other configuration
export LOG_LEVEL=$(bashio::config 'log_level' "info")
export SYSTEM_PROMPT_FILE=$(bashio::config 'system_prompt_file' "")
export TEMPERATURE=$(bashio::config 'temperature' "")
export ENABLE_CACHE_CONTROL=$(bashio::config 'enable_cache_control' "false")
export USAGE_TRACKING=$(bashio::config 'usage_tracking' "stream_options")

# Home Assistant configuration
export HA_CONFIG_DIR="/homeassistant"
export ADDON_CONFIG_DIR="/config"
export BACKUP_DIR="/backup/config-agent"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Log startup
bashio::log.info "Starting AI Configuration Agent..."
bashio::log.info "Provider: ${PROVIDER}"
bashio::log.info "API URL: ${OPENAI_API_URL}"
bashio::log.info "Model: ${OPENAI_MODEL}"
bashio::log.info "HA Config: ${HA_CONFIG_DIR}"

# Start application
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --log-level "${LOG_LEVEL}" \
    --no-access-log \
    --timeout-keep-alive 300
