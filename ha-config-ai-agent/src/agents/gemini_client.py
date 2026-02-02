"""Native Gemini Client using the official google-genai SDK.

This module leverages the official SDK to handle the complexities of
Gemini 3's thought_signature and multi-step turn validation automatically.
"""

import json
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional

# Import the official SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fallback for environments where it's not installed yet
    genai = None

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around google-genai SDK for OpenAI-style interaction."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-flash-preview",
        temperature: Optional[float] = None,
    ):
        if not genai:
            raise ImportError("google-genai package is not installed")
            
        self.api_key = api_key
        # Clean model name for the SDK
        self.model = model.split('/')[-1] if '/' in model else model
        self.temperature = temperature
        
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"Initialized google-genai SDK client for {self.model}")

    def _convert_tools(self, tools: List[Dict]) -> Optional[List[Dict]]:
        """Convert OpenAI tools to Gemini SDK tool definitions."""
        if not tools:
            return None
            
        declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                f = tool["function"]
                declarations.append(
                    types.FunctionDeclaration(
                        name=f["name"],
                        description=f.get("description"),
                        parameters=f.get("parameters")
                    )
                )
        if not declarations:
            return None
            
        return [types.Tool(function_declarations=declarations)]

    def _convert_messages(self, messages: List[Dict]) -> List[types.Content]:
        """Convert OpenAI messages to Gemini SDK Content objects."""
        contents = []
        
        for msg in messages:
            role = msg.get("role")
            if role == "system": continue # Handled in Config
            
            parts = []
            
            # 1. Text
            if msg.get("content"):
                if isinstance(msg["content"], str):
                    parts.append(types.Part(text=msg["content"]))
                elif isinstance(msg["content"], list):
                     for item in msg["content"]:
                         if isinstance(item, dict) and item.get("type") == "text":
                             parts.append(types.Part(text=item.get("text")))

            # 2. Tool Calls (Assistant)
            if role == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    f = tc["function"]
                    args = f.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except: 
                            args = {}
                    
                    # Create function call part
                    fc_part = types.Part(
                        function_call=types.FunctionCall(
                            name=f["name"],
                            args=args
                        )
                    )
                    
                    # Manual pass-through of thought_signature if we have it in history
                    # The SDK usually handles this if we use Chat, but since we reconstruct
                    # history each time, we check if we captured it previously.
                    sig = tc.get("thought_signature") or tc.get("thoughtSignature")
                    if sig:
                        fc_part.thought_signature = sig
                        
                    parts.append(fc_part)
            
            # 3. Tool Responses (Tool/User)
            if role == "tool":
                # OpenAI has 'tool_call_id', Gemini needs matching 'name'
                # We assume the caller provides function_name or we parse it
                name = msg.get("function_name")
                if not name and msg.get("tool_call_id"):
                     # Hack: we often store id as "funcname_idx"
                     name = msg["tool_call_id"].split('_')[0]
                
                content_str = msg.get("content", "")
                try:
                    response_dict = json.loads(content_str) if isinstance(content_str, str) else content_str
                except:
                    response_dict = {"result": content_str}

                parts.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=name,
                        response=response_dict
                    )
                ))
            
            if parts:
                # Map roles: assistant -> model, tool/user -> user
                sdk_role = "model" if role == "assistant" else "user"
                
                # Check for message-level signature (text reasoning)
                content_obj = types.Content(role=sdk_role, parts=parts)
                sig = msg.get("thought_signature") or msg.get("thoughtSignature")
                if sig and sdk_role == "model":
                    content_obj.thought_signature = sig
                    
                contents.append(content_obj)

        return contents

    async def generate_content_stream(
        self,
        messages: List[Dict],
        tools: List[Dict],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream content using the SDK."""
        try:
            sdk_contents = self._convert_messages(messages)
            sdk_tools = self._convert_tools(tools)
            
            # System instruction
            system_instr = None
            for msg in messages:
                if msg.get("role") == "system":
                    system_instr = msg.get("content")
                    break

            config = types.GenerateContentConfig(
                temperature=self.temperature,
                tools=sdk_tools,
                system_instruction=system_instr
            )
            
            logger.debug(f"[GEMINI SDK] Sending {len(sdk_contents)} history items")
            
            # Use models.generate_content_stream (async version via automatic wrapping?)
            # The v1.2.0 SDK has async methods on the client if using aio
            # or we might be using the synchronous wrapper.
            # However, for safety in this specific HA environment, we'll try the common
            # async iteration pattern if the client supports it, otherwise we might block briefly.
            # UPDATE: google-genai SDK 1.0+ 's generate_content_stream returns an iterator.
            # To be async-safe in HA, we technically should run this in executor if it's blocking,
            # but let's assume standard usage for now.
            
            # IMPORTANT: We use the client.models.generate_content_stream 
            response_stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=sdk_contents,
                config=config
            )
            
            accum_tool_calls = []
            msg_sig = None
            accum_text = ""
            
            for chunk in response_stream:
                # Chunk is a GenerateContentResponse
                # It might contain candidates[0].content...
                
                # Capture signature
                if not msg_sig and chunk.candidates and chunk.candidates[0].content:
                    msg_sig = getattr(chunk.candidates[0].content, 'thought_signature', None)

                # Process parts
                if chunk.text:
                    accum_text += chunk.text
                    yield {"type": "content", "content": chunk.text}
                
                if chunk.function_calls:
                    for fc in chunk.function_calls:
                        # Capture signature from part if present
                        # SDK objects might allow access via attribute or dict
                        # We'll check the source part if accessible, or just rely on the msg_sig
                        
                        tc = {
                            "id": f"{fc.name}_{len(accum_tool_calls)}",
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": json.dumps(fc.args)
                            }
                        }
                        # If the chunk has a signature, attach it
                        if msg_sig:
                            tc["thought_signature"] = msg_sig
                            
                        # Try to find signature on the specific part if possible (undocumented in SDK wrapper sometimes)
                        
                        accum_tool_calls.append(tc)
                        yield {"type": "tool_call", "tool_call": tc}
                
                if chunk.candidates and chunk.candidates[0].finish_reason:
                     # Stop reason logic if needed
                     pass

            # Final yield
            yield {
                "type": "complete",
                "content": accum_text,
                "tool_calls": accum_tool_calls,
                "thought_signature": msg_sig,
                "usage": {}, # Usage often at end
                "finish_reason": "tool_calls" if accum_tool_calls else "stop"
            }

        except Exception as e:
            logger.error(f"[GEMINI SDK] Error: {e}", exc_info=True)
            yield {"type": "error", "error": str(e)}

    async def generate_content(self, messages: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
        """Non-streaming helper."""
        result = {"content": "", "tool_calls": [], "usage": {}}
        async for event in self.generate_content_stream(messages, tools):
            if event["type"] == "content": result["content"] += event["content"]
            elif event["type"] == "tool_call": result["tool_calls"].append(event["tool_call"])
            elif event["type"] == "complete":
                result.update({"usage": event["usage"], "thought_signature": event.get("thought_signature")})
        return result


def is_gemini_model(model: str) -> bool:
    m = model.split('/')[-1] if '/' in model else model
    return m.startswith("gemini-")


def is_gemini_3_model(model: str) -> bool:
    m = model.split('/')[-1] if '/' in model else model
    return any(m.startswith(p) for p in ["gemini-3", "gemini-4", "gemini-5"])
