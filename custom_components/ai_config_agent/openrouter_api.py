import asyncio
import logging
import time
from typing import Dict, Any, Optional

import requests

from .const import MODEL_COST_API_URL

_LOGGER = logging.getLogger(__name__)

# Cache for model costs
_MODEL_COSTS: Dict[str, Dict[str, Any]] = {}
_LAST_FETCH_TIME: float = 0
_CACHE_TIMEOUT: int = 3600  # Cache for 1 hour

async def _fetch_model_costs() -> None:
    """Fetch model costs from OpenRouter API and update cache."""
    global _MODEL_COSTS, _LAST_FETCH_TIME
    try:
        response = await asyncio.to_thread(requests.get, MODEL_COST_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        _MODEL_COSTS = {model["id"]: model for model in data.get("data", [])}
        _LAST_FETCH_TIME = time.monotonic()
        _LOGGER.debug("Successfully fetched OpenRouter model costs.")
    except requests.exceptions.RequestException as e:
        _LOGGER.error("Error fetching OpenRouter model costs: %s", e)
        _MODEL_COSTS = {} # Clear cache on error
    except Exception as e:
        _LOGGER.error("An unexpected error occurred while fetching model costs: %s", e)
        _MODEL_COSTS = {}

async def get_model_cost(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cost information for a given model ID.
    Fetches costs from the API if cache is stale or empty.
    """
    global _LAST_FETCH_TIME

    if not _MODEL_COSTS or (time.monotonic() - _LAST_FETCH_TIME) > _CACHE_TIMEOUT:
        _LOGGER.debug("Model cost cache is stale or empty, fetching new data.")
        await _fetch_model_costs()

    # Try exact match first
    if model_id in _MODEL_COSTS:
        return _MODEL_COSTS[model_id]

    # If no exact match, try suffix matching
    for key, model_info in _MODEL_COSTS.items():
        if key.endswith(model_id):
            _LOGGER.debug("Found model cost for '%s' using suffix match with '%s'", model_id, key)
            return model_info

    return None

def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the total cost for a given number of input and output tokens.
    Returns 0 if cost information for the model is not available.
    """
    model_info = asyncio.run(get_model_cost(model_id)) # Synchronous call to async function
    if not model_info:
        _LOGGER.warning("Cost information not found for model: %s", model_id)
        return 0.0

    input_cost_per_million = model_info.get("pricing", {}).get("prompt", 0)
    output_cost_per_million = model_info.get("pricing", {}).get("completion", 0)

    input_cost = (input_tokens / 1_000_000) * input_cost_per_million
    output_cost = (output_tokens / 1_000_000) * output_cost_per_million

    total_cost = input_cost + output_cost
    _LOGGER.debug("Calculated cost for model %s: input_tokens=%d, output_tokens=%d, total_cost=%f",
                  model_id, input_tokens, output_tokens, total_cost)
    return total_cost
