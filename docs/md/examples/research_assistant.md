# Research Assistant Example with AsyncWebCrawler

This example demonstrates how to build an advanced research assistant using `Chainlit`, `Crawl4AI`'s `AsyncWebCrawler`, and various AI services. The assistant can crawl web pages asynchronously, answer questions based on the crawled content, and handle audio inputs.

## Step-by-Step Guide

1. **Install Required Packages**

    Ensure you have the necessary packages installed:

    ```bash
    pip install chainlit groq openai crawl4ai
    ```

2. **Import Libraries**

    ```python
    import os
    import time
    import asyncio
    from openai import AsyncOpenAI
    import chainlit as cl
    import re
    from io import BytesIO
    from chainlit.element import ElementBased
    from groq import Groq
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import NoExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking

    client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))

    # Instrument the OpenAI client
    cl.instrument_openai()
    ```

3. **Set Configuration**

    ```python
    settings = {
        "model": "llama3-8b-8192",
        "temperature": 0.5,
        "max_tokens": 500,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    ```

4. **Define Utility Functions**

    ```python
    def extract_urls(text):
        url_pattern = re.compile(r'(https?://\S+)')
        return url_pattern.findall(text)

    async def crawl_urls(urls):
        async with AsyncWebCrawler(verbose=True) as crawler:
            results = await crawler.arun_many(
                urls=urls,
                word_count_threshold=10,
                extraction_strategy=NoExtractionStrategy(),
                chunking_strategy=RegexChunking(),
                bypass_cache=True
            )
        return [result.markdown for result in results if result.success]
    ```

5. **Initialize Chat Start Event**

    ```python
    @cl.on_chat_start
    async def on_chat_start():
        cl.user_session.set("session", {
            "history": [],
            "context": {}
        })  
        await cl.Message(content="Welcome to the chat! How can I assist you today?").send()
    ```

6. **Handle Incoming Messages**

    ```python
    @cl.on_message
    async def on_message(message: cl.Message):
        user_session = cl.user_session.get("session")

        # Extract URLs from the user's message
        urls = extract_urls(message.content)

        if urls:
            crawled_contents = await crawl_urls(urls)
            for url, content in zip(urls, crawled_contents):
                ref_number = f"REF_{len(user_session['context']) + 1}"
                user_session["context"][ref_number] = {
                    "url": url,
                    "content": content
                }

        user_session["history"].append({
            "role": "user",
            "content": message.content
        })

        # Create a system message that includes the context
        context_messages = [
            f'<appendix ref="{ref}">\n{data["content"]}\n</appendix>'
            for ref, data in user_session["context"].items()
        ]
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful bot. Use the following context for answering questions. "
                "Refer to the sources using the REF number in square brackets, e.g., [1], only if the source is given in the appendices below.\n\n"
                "If the question requires any information from the provided appendices or context, refer to the sources. "
                "If not, there is no need to add a references section. "
                "At the end of your response, provide a reference section listing the URLs and their REF numbers only if sources from the appendices were used.\n\n"
                "\n\n".join(context_messages)
            ) if context_messages else "You are a helpful assistant."
        }

        msg = cl.Message(content="")
        await msg.send()

        # Get response from the LLM
        stream = await client.chat.completions.create(
            messages=[system_message, *user_session["history"]],
            stream=True,
            **settings
        )

        assistant_response = ""
        async for part in stream:
            if token := part.choices[0].delta.content:
                assistant_response += token
                await msg.stream_token(token)

        # Add assistant message to the history
        user_session["history"].append({
            "role": "assistant",
            "content": assistant_response
        })
        await msg.update()

        # Append the reference section to the assistant's response
        if user_session["context"]:
            reference_section = "\n\nReferences:\n"
            for ref, data in user_session["context"].items():
                reference_section += f"[{ref.split('_')[1]}]: {data['url']}\n"
            msg.content += reference_section
            await msg.update()
    ```

7. **Handle Audio Input**

    ```python
    @cl.on_audio_chunk
    async def on_audio_chunk(chunk: cl.AudioChunk):
        if chunk.isStart:
            buffer = BytesIO()
            buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
            cl.user_session.set("audio_buffer", buffer)
            cl.user_session.set("audio_mime_type", chunk.mimeType)
        cl.user_session.get("audio_buffer").write(chunk.data)

    @cl.step(type="tool")
    async def speech_to_text(audio_file):
        response = await client.audio.transcriptions.create(
            model="whisper-large-v3", file=audio_file
        )
        return response.text

    @cl.on_audio_end
    async def on_audio_end(elements: list[ElementBased]):
        audio_buffer: BytesIO = cl.user_session.get("audio_buffer")
        audio_buffer.seek(0)
        audio_file = audio_buffer.read()
        audio_mime_type: str = cl.user_session.get("audio_mime_type")
        
        start_time = time.time()
        transcription = await speech_to_text((audio_buffer.name, audio_file, audio_mime_type))
        end_time = time.time()
        print(f"Transcription took {end_time - start_time} seconds")
        
        user_msg = cl.Message(author="You", type="user_message", content=transcription)
        await user_msg.send()
        await on_message(user_msg)
    ```

8. **Run the Chat Application**

    ```python
    if __name__ == "__main__":
        from chainlit.cli import run_chainlit
        run_chainlit(__file__)
    ```

## Explanation

- **Libraries and Configuration**: We import necessary libraries, including `AsyncWebCrawler` from `crawl4ai`.
- **Utility Functions**: 
  - `extract_urls`: Uses regex to find URLs in messages.
  - `crawl_urls`: An asynchronous function that uses `AsyncWebCrawler` to fetch content from multiple URLs concurrently.
- **Chat Start Event**: Initializes the chat session and sends a welcome message.
- **Message Handling**: 
  - Extracts URLs from user messages.
  - Asynchronously crawls the URLs using `AsyncWebCrawler`.
  - Updates chat history and context with crawled content.
  - Generates a response using the LLM, incorporating the crawled context.
- **Audio Handling**: Captures, buffers, and transcribes audio input, then processes the transcription as text.
- **Running the Application**: Starts the Chainlit server for interaction with the assistant.

## Key Improvements

1. **Asynchronous Web Crawling**: Using `AsyncWebCrawler` allows for efficient, concurrent crawling of multiple URLs.
2. **Improved Context Management**: The assistant now maintains a context of crawled content, allowing for more informed responses.
3. **Dynamic Reference System**: The assistant can refer to specific sources in its responses and provide a reference section.
4. **Seamless Audio Integration**: The ability to handle audio inputs makes the assistant more versatile and user-friendly.

This updated Research Assistant showcases how to create a powerful, interactive tool that can efficiently fetch and process web content, handle various input types, and provide informed responses based on the gathered information.