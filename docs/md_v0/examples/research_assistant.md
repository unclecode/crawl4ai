## Research Assistant Example

This example demonstrates how to build a research assistant using `Chainlit` and `Crawl4AI`. The assistant will be capable of crawling web pages for information and answering questions based on the crawled content. Additionally, it integrates speech-to-text functionality for audio inputs.

### Step-by-Step Guide

1. **Install Required Packages**

    Ensure you have the necessary packages installed. You need `chainlit`, `groq`, `requests`, and `openai`.

    ```bash
    pip install chainlit groq requests openai
    ```

2. **Import Libraries**

    Import all the necessary modules and initialize the OpenAI client.

    ```python
    import os
    import time
    from openai import AsyncOpenAI
    import chainlit as cl
    import re
    import requests
    from io import BytesIO
    from chainlit.element import ElementBased
    from groq import Groq

    from concurrent.futures import ThreadPoolExecutor

    client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))

    # Instrument the OpenAI client
    cl.instrument_openai()
    ```

3. **Set Configuration**

    Define the model settings for the assistant.

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

    - **Extract URLs from Text**: Use regex to find URLs in messages.

        ```python
        def extract_urls(text):
            url_pattern = re.compile(r'(https?://\S+)')
            return url_pattern.findall(text)
        ```

    - **Crawl URL**: Send a request to `Crawl4AI` to fetch the content of a URL.

        ```python
        def crawl_url(url):
            data = {
                "urls": [url],
                "include_raw_html": True,
                "word_count_threshold": 10,
                "extraction_strategy": "NoExtractionStrategy",
                "chunking_strategy": "RegexChunking"
            }
            response = requests.post("https://crawl4ai.com/crawl", json=data)
            response_data = response.json()
            response_data = response_data['results'][0]
            return response_data['markdown']
        ```

5. **Initialize Chat Start Event**

    Set up the initial chat message and user session.

    ```python
    @cl.on_chat_start
    async def on_chat_start():
        cl.user_session.set("session", {
            "history": [],
            "context": {}
        })  
        await cl.Message(
            content="Welcome to the chat! How can I assist you today?"
        ).send()
    ```

6. **Handle Incoming Messages**

    Process user messages, extract URLs, and crawl them concurrently. Update the chat history and system message.

    ```python
    @cl.on_message
    async def on_message(message: cl.Message):
        user_session = cl.user_session.get("session")

        # Extract URLs from the user's message
        urls = extract_urls(message.content)

        futures = []
        with ThreadPoolExecutor() as executor:
            for url in urls:
                futures.append(executor.submit(crawl_url, url))

        results = [future.result() for future in futures]

        for url, result in zip(urls, results):
            ref_number = f"REF_{len(user_session['context']) + 1}"
            user_session["context"][ref_number] = {
                "url": url,
                "content": result
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
        if context_messages:
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful bot. Use the following context for answering questions. "
                    "Refer to the sources using the REF number in square brackets, e.g., [1], only if the source is given in the appendices below.\n\n"
                    "If the question requires any information from the provided appendices or context, refer to the sources. "
                    "If not, there is no need to add a references section. "
                    "At the end of your response, provide a reference section listing the URLs and their REF numbers only if sources from the appendices were used.\n\n"
                    "\n\n".join(context_messages)
                )
            }
        else:
            system_message = {
                "role": "system",
                "content": "You are a helpful assistant."
            }

        msg = cl.Message(content="")
        await msg.send()

        # Get response from the LLM
        stream = await client.chat.completions.create(
            messages=[
                system_message,
                *user_session["history"]
            ],
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
        reference_section = "\n\nReferences:\n"
        for ref, data in user_session["context"].items():
            reference_section += f"[{ref.split('_')[1]}]: {data['url']}\n"

        msg.content += reference_section
        await msg.update()
    ```

7. **Handle Audio Input**

    Capture and transcribe audio input. Store the audio buffer and transcribe it when the audio ends.

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
        cli = Groq()
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
        
        user_msg = cl.Message(
            author="You", 
            type="user_message",
            content=transcription
        )
        await user_msg.send()
        await on_message(user_msg)
    ```

8. **Run the Chat Application**

    Start the Chainlit application.

    ```python
    if __name__ == "__main__":
        from chainlit.cli import run_chainlit
        run_chainlit(__file__)
    ```

### Explanation

- **Libraries and Configuration**: Import necessary libraries and configure the OpenAI client.
- **Utility Functions**: Define functions to extract URLs and crawl them.
- **Chat Start Event**: Initialize chat session and welcome message.
- **Message Handling**: Extract URLs, crawl them concurrently, and update chat history and context.
- **Audio Handling**: Capture, buffer, and transcribe audio input, then process the transcription as text.
- **Running the Application**: Start the Chainlit server to interact with the assistant.

This example showcases how to create an interactive research assistant that can fetch, process, and summarize web content, along with handling audio inputs for a seamless user experience.
