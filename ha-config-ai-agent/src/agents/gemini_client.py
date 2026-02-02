"""Native Gemini API client for Gemini 3 and later models.

This module provides native Gemini API support using the google-genai SDK,
which is required for proper function calling with Gemini 3 models that
use the thought_signature mechanism.
"""

import json
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiClient:
    """Native Gemini API client for proper Gemini 3 function calling support."""

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
        self.model = model
        self.temperature = temperature
        
        # Initialize the client
        self.client = genai.Client(api_key=api_key)
        
        logger.info(f"Initialized native Gemini client with model: {model}")

    def _build_tools(self, tool_definitions: List[Dict]) -> List[types.Tool]:
        """Convert OpenAI-style tool definitions to Gemini format.
        
        Args:
            tool_definitions: List of tool definitions in OpenAI format
            
        Returns:
            List of Gemini Tool objects
        """
        function_declarations = []
        
        for tool in tool_definitions:
            if tool.get("type") == "function":
                func = tool["function"]
                
                # Convert parameters
                params = func.get("parameters", {})
                
                function_declarations.append(
                    types.FunctionDeclaration(
                        name=func["name"],
                        description=func.get("description", ""),
                        parameters=params
                    )
                )
        
        return [types.Tool(function_declarations=function_declarations)]

    def _build_contents(self, messages: List[Dict]) -> List[types.Content]:
        """Convert OpenAI-style messages to Gemini Content format.
        
        Args:
            messages: List of messages in OpenAI format
            
        Returns:
            List of Gemini Content objects
        """
        contents = []
        
        for msg in messages:
            role = msg.get("role", "user")
            
            # Map OpenAI roles to Gemini roles
            if role == "system":
                # System messages become user messages in Gemini
                # (system instruction is set separately)
                continue
            elif role == "assistant":
                gemini_role = "model"
            elif role == "tool":
                gemini_role = "tool"
            else:
                gemini_role = "user"
            
            parts = []
            
            # Handle content
            content = msg.get("content")
            if content:
                if isinstance(content, str):
                    parts.append(types.Part.from_text(text=content))
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(types.Part.from_text(text=item.get("text", "")))
            
            # Handle tool calls in assistant messages
            if role == "assistant" and "tool_calls" in msg:
                for tc in msg.get("tool_calls", []):
                    if tc.get("type") == "function":
                        func = tc.get("function", {})
                        args = func.get("arguments", "{}")
                        if isinstance(args, str):
                            args = json.loads(args)
                        
                        parts.append(types.Part.from_function_call(
                            name=func.get("name", ""),
                            args=args
                        ))
            
            # Handle tool responses
            if role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                content_str = msg.get("content", "{}")
                if isinstance(content_str, str):
                    try:
                        result = json.loads(content_str)
                    except json.JSONDecodeError:
                        result = {"result": content_str}
                else:
                    result = content_str
                
                # For tool responses, we need to find the function name
                # In Gemini, we create a function response part
                parts.append(types.Part.from_function_response(
                    name=tool_call_id.split("_")[0] if "_" in tool_call_id else "function",
                    response=result
                ))
            
            if parts:
                contents.append(types.Content(role=gemini_role, parts=parts))
        
        return contents

    def _get_system_instruction(self, messages: List[Dict]) -> Optional[str]:
        """Extract system instruction from messages.
        
        Args:
            messages: List of messages
            
        Returns:
            System instruction string or None
        """
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    texts = [item.get("text", "") for item in content if isinstance(item, dict)]
                    return " ".join(texts)
        return None

    async def generate_content_stream(
        self,
        messages: List[Dict],
        tools: List[Dict],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate content with streaming, handling tool calls.
        
        Args:
            messages: Conversation messages in OpenAI format
            tools: Tool definitions in OpenAI format
            
        Yields:
            Events with content, tool_calls, and usage information
        """
        try:
            # Build Gemini format
            contents = self._build_contents(messages)
            gemini_tools = self._build_tools(tools)
            system_instruction = self._get_system_instruction(messages)
            
            # Build config
            config = types.GenerateContentConfig(
                tools=gemini_tools,
                temperature=self.temperature,
            )
            
            if system_instruction:
                config.system_instruction = system_instruction
            
            logger.info(f"Calling Gemini API with model: {self.model}")
            logger.debug(f"Contents: {len(contents)} messages, Tools: {len(gemini_tools[0].function_declarations)} functions")
            
            # Generate with streaming
            accumulated_text = ""
            accumulated_tool_calls = []
            usage_info = {}
            
            async for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                # Check for text content
                if chunk.text:
                    accumulated_text += chunk.text
                    yield {
                        "type": "content",
                        "content": chunk.text
                    }
                
                # Check for function calls
                if chunk.function_calls:
                    for fc in chunk.function_calls:
                        tool_call = {
                            "id": f"{fc.name}_{len(accumulated_tool_calls)}",
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": json.dumps(fc.args) if fc.args else "{}"
                            }
                        }
                        accumulated_tool_calls.append(tool_call)
                        
                        yield {
                            "type": "tool_call",
                            "tool_call": tool_call
                        }
                
                # Check for usage metadata
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    usage_info = {
                        "prompt_tokens": getattr(chunk.usage_metadata, 'prompt_token_count', 0),
                        "completion_tokens": getattr(chunk.usage_metadata, 'candidates_token_count', 0),
                        "total_tokens": getattr(chunk.usage_metadata, 'total_token_count', 0),
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
            logger.error(f"Gemini API error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }

    async def generate_content(
        self,
        messages: List[Dict],
        tools: List[Dict],
    ) -> Dict[str, Any]:
        """Generate content without streaming.
        
        Args:
            messages: Conversation messages in OpenAI format
            tools: Tool definitions in OpenAI format
            
        Returns:
            Response with content, tool_calls, and usage
        """
        result = {
            "content": "",
            "tool_calls": [],
            "usage": {},
            "finish_reason": "stop"
        }
        
        async for event in self.generate_content_stream(messages, tools):
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
    """Check if a model name is a Gemini model.
    
    Args:
        model: Model name
        
    Returns:
        True if it's a Gemini model
    """
    return model.startswith("gemini-")


def is_gemini_3_model(model: str) -> bool:
    """Check if a model is Gemini 3 or later (requires native API).
    
    Args:
        model: Model name
        
    Returns:
        True if it's Gemini 3 or later
    """
    gemini_3_prefixes = ["gemini-3", "gemini-4", "gemini-5"]
    return any(model.startswith(prefix) for prefix in gemini_3_prefixes)
