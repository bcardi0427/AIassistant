"""Native Gemini API client for Gemini 3 and later models.

This module provides native Gemini API support using direct HTTP requests,
which is required for proper function calling with Gemini 3 models that
use the thought_signature mechanism.

Gemini 3+ enforces thought_signature pass-through:
1. When Gemini returns a function call, it includes thought_signature
2. We MUST echo that thought_signature back when sending the function response
3. If we don't, we get 400 INVALID_ARGUMENT
"""

import json
import logging
import aiohttp
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    """Native Gemini API client with proper thought_signature handling for Gemini 3+."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-flash-preview",
        temperature: Optional[float] = None,
    ):
        """Initialize the Gemini client.
        
        Args:
            api_key: Google API key
            model: Model name (e.g., gemini-3-flash-preview)
            temperature: Optional temperature for generation
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        
        # Endpoint for generateContent
        self.endpoint = f"{GEMINI_API_BASE}/models/{model}:generateContent"
        self.stream_endpoint = f"{GEMINI_API_BASE}/models/{model}:streamGenerateContent"
        
        logger.info(f"Initialized native Gemini client with model: {model}")
        logger.info(f"Endpoint: {self.endpoint}")

    def _build_tools(self, tool_definitions: List[Dict]) -> List[Dict]:
        """Convert OpenAI-style tool definitions to Gemini format.
        
        Args:
            tool_definitions: List of tool definitions in OpenAI format
            
        Returns:
            List of Gemini tool objects (as dicts for JSON)
        """
        function_declarations = []
        
        for tool in tool_definitions:
            if tool.get("type") == "function":
                func = tool["function"]
                
                # Convert parameters - Gemini uses same format but may need adjustments
                params = func.get("parameters", {})
                
                function_declarations.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": params
                })
        
        return [{"functionDeclarations": function_declarations}]

    def _build_contents(
        self, 
        messages: List[Dict],
        pending_thought_signatures: Dict[str, str] = None
    ) -> List[Dict]:
        """Convert OpenAI-style messages to Gemini Content format.
        
        Args:
            messages: List of messages in OpenAI format
            pending_thought_signatures: Map of function name to thought_signature
                                        that must be echoed back in function responses
            
        Returns:
            List of Gemini Content objects (as dicts for JSON)
        """
        contents = []
        pending_thought_signatures = pending_thought_signatures or {}
        
        for msg in messages:
            role = msg.get("role", "user")
            
            # Skip system messages (handled separately)
            if role == "system":
                continue
            
            # Map roles
            if role == "assistant":
                gemini_role = "model"
            elif role == "tool":
                gemini_role = "function"  # Gemini uses "function" role for tool responses
            else:
                gemini_role = "user"
            
            parts = []
            
            # Handle text content
            content = msg.get("content")
            if content and role != "tool":
                if isinstance(content, str):
                    parts.append({"text": content})
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append({"text": item.get("text", "")})
            
            # Handle function calls in model/assistant messages
            if role == "assistant" and "tool_calls" in msg:
                for tc in msg.get("tool_calls", []):
                    func = tc.get("function", {})
                    args_str = func.get("arguments", "{}")
                    if isinstance(args_str, str):
                        try:
                            args = json.loads(args_str)
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = args_str
                    
                    function_call = {
                        "functionCall": {
                            "name": func.get("name", ""),
                            "args": args
                        }
                    }
                    
                    # Include thought_signature if it was provided with this tool call
                    thought_sig = tc.get("thought_signature")
                    if thought_sig:
                        function_call["functionCall"]["thought_signature"] = thought_sig
                        # Store for later when we send the response
                        pending_thought_signatures[func.get("name", "")] = thought_sig
                    
                    parts.append(function_call)
            
            # Handle function/tool responses - CRITICAL: include thought_signature
            if role == "tool":
                func_name = msg.get("function_name", "")
                if not func_name:
                    # Try to extract from tool_call_id
                    tool_call_id = msg.get("tool_call_id", "")
                    func_name = tool_call_id.split("_")[0] if "_" in tool_call_id else tool_call_id
                
                content_str = msg.get("content", "{}")
                if isinstance(content_str, str):
                    try:
                        response_data = json.loads(content_str)
                    except json.JSONDecodeError:
                        response_data = {"result": content_str}
                else:
                    response_data = content_str
                
                function_response = {
                    "functionResponse": {
                        "name": func_name,
                        "response": response_data
                    }
                }
                
                # CRITICAL: Echo back the thought_signature
                thought_sig = msg.get("thought_signature") or pending_thought_signatures.get(func_name)
                if thought_sig:
                    function_response["functionResponse"]["thought_signature"] = thought_sig
                    logger.debug(f"Including thought_signature in function response for {func_name}")
                
                parts.append(function_response)
                gemini_role = "function"  # Ensure role is function for responses
            
            if parts:
                contents.append({"role": gemini_role, "parts": parts})
        
        return contents

    def _get_system_instruction(self, messages: List[Dict]) -> Optional[Dict]:
        """Extract system instruction from messages.
        
        Args:
            messages: List of messages
            
        Returns:
            System instruction dict or None
        """
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return {"parts": [{"text": content}]}
                elif isinstance(content, list):
                    texts = [item.get("text", "") for item in content if isinstance(item, dict)]
                    return {"parts": [{"text": " ".join(texts)}]}
        return None

    async def generate_content_stream(
        self,
        messages: List[Dict],
        tools: List[Dict],
        pending_thought_signatures: Dict[str, str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate content with streaming, handling tool calls and thought_signature.
        
        Args:
            messages: Conversation messages in OpenAI format
            tools: Tool definitions in OpenAI format
            pending_thought_signatures: Thought signatures from previous function calls
            
        Yields:
            Events with content, tool_calls, and usage information
        """
        pending_thought_signatures = pending_thought_signatures or {}
        
        try:
            # Build request body
            contents = self._build_contents(messages, pending_thought_signatures)
            gemini_tools = self._build_tools(tools)
            system_instruction = self._get_system_instruction(messages)
            
            request_body = {
                "contents": contents,
                "tools": gemini_tools
            }
            
            if system_instruction:
                request_body["systemInstruction"] = system_instruction
            
            if self.temperature is not None:
                request_body["generationConfig"] = {
                    "temperature": self.temperature
                }
            
            # Add API key to URL
            url = f"{self.stream_endpoint}?key={self.api_key}&alt=sse"
            
            logger.info(f"Calling Gemini API (streaming): {self.model}")
            logger.debug(f"Request body: {json.dumps(request_body, indent=2)[:1000]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error {response.status}: {error_text}")
                        yield {
                            "type": "error",
                            "error": f"API error {response.status}: {error_text[:500]}"
                        }
                        return
                    
                    accumulated_text = ""
                    accumulated_tool_calls = []
                    usage_info = {}
                    
                    # Parse SSE stream
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if not line or line.startswith(':'):
                            continue
                        
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            
                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            
                            # Process candidates
                            for candidate in chunk.get("candidates", []):
                                content_obj = candidate.get("content", {})
                                
                                for part in content_obj.get("parts", []):
                                    # Handle text
                                    if "text" in part:
                                        text = part["text"]
                                        accumulated_text += text
                                        yield {
                                            "type": "content",
                                            "content": text
                                        }
                                    
                                    # Handle function calls - CAPTURE thought_signature
                                    if "functionCall" in part:
                                        fc = part["functionCall"]
                                        func_name = fc.get("name", "")
                                        
                                        tool_call = {
                                            "id": f"{func_name}_{len(accumulated_tool_calls)}",
                                            "type": "function",
                                            "function": {
                                                "name": func_name,
                                                "arguments": json.dumps(fc.get("args", {}))
                                            }
                                        }
                                        
                                        # CRITICAL: Capture thought_signature for later
                                        thought_sig = fc.get("thought_signature")
                                        if thought_sig:
                                            tool_call["thought_signature"] = thought_sig
                                            logger.info(f"Captured thought_signature for {func_name}")
                                        
                                        accumulated_tool_calls.append(tool_call)
                                        
                                        yield {
                                            "type": "tool_call",
                                            "tool_call": tool_call
                                        }
                            
                            # Check for usage metadata
                            if "usageMetadata" in chunk:
                                usage = chunk["usageMetadata"]
                                usage_info = {
                                    "prompt_tokens": usage.get("promptTokenCount", 0),
                                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                                    "total_tokens": usage.get("totalTokenCount", 0),
                                }
                    
                    # Yield completion event
                    yield {
                        "type": "complete",
                        "content": accumulated_text,
                        "tool_calls": accumulated_tool_calls,
                        "usage": usage_info,
                        "finish_reason": "tool_calls" if accumulated_tool_calls else "stop"
                    }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }

    async def generate_content(
        self,
        messages: List[Dict],
        tools: List[Dict],
        pending_thought_signatures: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Generate content without streaming.
        
        Args:
            messages: Conversation messages in OpenAI format
            tools: Tool definitions in OpenAI format
            pending_thought_signatures: Thought signatures from previous function calls
            
        Returns:
            Response with content, tool_calls, and usage
        """
        result = {
            "content": "",
            "tool_calls": [],
            "usage": {},
            "finish_reason": "stop"
        }
        
        async for event in self.generate_content_stream(messages, tools, pending_thought_signatures):
            if event["type"] == "content":
                result["content"] += event.get("content", "")
            elif event["type"] == "tool_call":
                result["tool_calls"].append(event["tool_call"])
            elif event["type"] == "complete":
                result["usage"] = event.get("usage", {})
                result["finish_reason"] = event.get("finish_reason", "stop")
            elif event["type"] == "error":
                raise Exception(event.get("error", "Unknown error"))
        
        return result


def is_gemini_model(model: str) -> bool:
    """Check if a model name is a Gemini model."""
    return model.startswith("gemini-")


def is_gemini_3_model(model: str) -> bool:
    """Check if a model is Gemini 3 or later (requires native API with thought_signature)."""
    gemini_3_prefixes = ["gemini-3", "gemini-4", "gemini-5"]
    return any(model.startswith(prefix) for prefix in gemini_3_prefixes)
