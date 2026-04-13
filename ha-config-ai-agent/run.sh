#!/usr/bin/with-contenv bashio

# Disable Python output buffering for real-time streaming
export PYTHONUNBUFFERED=1

# Get API keys
export OPENAI_API_KEY=$(bashio::config 'openai_api_key' "")
export GEMINI_API_KEY=$(bashio::config 'gemini_api_key' "")
export OPENAI_API_URL=$(bashio::config 'api_url' "https://api.openai.com/v1")
export GEMINI_ENDPOINT=$(bashio::config 'gemini_api_url' "https://generativelanguage.googleapis.com")
export MODEL=$(bashio::config 'model' "gpt-4o")


# Other configuration
export LOG_LEVEL=$(bashio::config 'log_level' "info")
export SYSTEM_PROMPT_FILE=$(bashio::config 'system_prompt_file' "")
export TEMPERATURE=$(bashio::config 'temperature' "")
export ENABLE_CACHE_CONTROL=$(bashio::config 'enable_cache_control' "false")
export USAGE_TRACKING=$(bashio::config 'usage_tracking' "stream_options")

# Home Assistant configuration
export HA_CONFIG_DIR="/homeassistant"
export ADDONS_DIR="/addon_configs"
export BACKUP_DIR="/backup/config-agent"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Log startup
bashio::log.info "Starting AIassistant (Dual Provider Mode)..."
bashio::log.info "API URL: ${OPENAI_API_URL}"
bashio::log.info "Model: ${MODEL}"

bashio::log.info "HA Config: ${HA_CONFIG_DIR}"

# Start application
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --log-level "${LOG_LEVEL}" \
    --no-access-log \
    --timeout-keep-alive 300
