import os
import asyncio
from google import genai
from google.genai import types

async def main():
    client = genai.Client()
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents='What is the weather in Tokyo?',
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name='get_weather',
                    description='Get weather in location',
                    parameters={'type': 'OBJECT', 'properties': {'location': {'type': 'STRING'}}}
                )
            ])]
        )
    )
    print("Response text:", response.text)
    print("Response parts:", response.parts)
    print("Response function_calls:", response.function_calls)
    if response.function_calls:
        print("First call dir:", dir(response.function_calls[0]))

if __name__ == '__main__':
    asyncio.run(main())
