# Make sure to install the required packageschainlit and groq
import os, time
from openai import AsyncOpenAI
import chainlit as cl
import re
import requests
from io import BytesIO
from chainlit.element import ElementBased
from groq import Groq

# Import threadpools to run the crawl_url function in a separate thread
from concurrent.futures import ThreadPoolExecutor

client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))

# Instrument the OpenAI client
cl.instrument_openai()

settings = {
    "model": "llama3-8b-8192",
    "temperature": 0.5,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

def extract_urls(text):
    url_pattern = re.compile(r'(https?://\S+)')
    return url_pattern.findall(text)

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

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("session", {
        "history": [],
        "context": {}
    })  
    await cl.Message(
        content="Welcome to the chat! How can I assist you today?"
    ).send()

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
    
    # for url in urls:
    #     # Crawl the content of each URL and add it to the session context with a reference number
    #     ref_number = f"REF_{len(user_session['context']) + 1}"
    #     crawled_content = crawl_url(url)
    #     user_session["context"][ref_number] = {
    #         "url": url,
    #         "content": crawled_content
    #     }

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


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.AudioChunk):
    if chunk.isStart:
        buffer = BytesIO()
        # This is required for whisper to recognize the file type
        buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
        # Initialize the session for a new audio stream
        cl.user_session.set("audio_buffer", buffer)
        cl.user_session.set("audio_mime_type", chunk.mimeType)

    # Write the chunks to a buffer and transcribe the whole audio at the end
    cl.user_session.get("audio_buffer").write(chunk.data)

    pass

@cl.step(type="tool")
async def speech_to_text(audio_file):
    cli = Groq()
    
    # response = cli.audio.transcriptions.create(
    #     file=audio_file, #(filename, file.read()),
    #     model="whisper-large-v3",
    # )
    
    response = await client.audio.transcriptions.create(
        model="whisper-large-v3", file=audio_file
    )

    return response.text


@cl.on_audio_end
async def on_audio_end(elements: list[ElementBased]):
    # Get the audio buffer from the session
    audio_buffer: BytesIO = cl.user_session.get("audio_buffer")
    audio_buffer.seek(0)  # Move the file pointer to the beginning
    audio_file = audio_buffer.read()
    audio_mime_type: str = cl.user_session.get("audio_mime_type")

    # input_audio_el = cl.Audio(
    #     mime=audio_mime_type, content=audio_file, name=audio_buffer.name
    # )
    # await cl.Message(
    #     author="You", 
    #     type="user_message",
    #     content="",
    #     elements=[input_audio_el, *elements]
    # ).send()
    
    # answer_message = await cl.Message(content="").send()
    
    
    start_time = time.time()
    whisper_input = (audio_buffer.name, audio_file, audio_mime_type)
    transcription = await speech_to_text(whisper_input)
    end_time = time.time()
    print(f"Transcription took {end_time - start_time} seconds")
    
    user_msg = cl.Message(
        author="You", 
        type="user_message",
        content=transcription
    )
    await user_msg.send()
    await on_message(user_msg)

    # images = [file for file in elements if "image" in file.mime]

    # text_answer = await generate_text_answer(transcription, images)
    
    # output_name, output_audio = await text_to_speech(text_answer, audio_mime_type)
    
    # output_audio_el = cl.Audio(
    #     name=output_name,
    #     auto_play=True,
    #     mime=audio_mime_type,
    #     content=output_audio,
    # )
    
    # answer_message.elements = [output_audio_el]
    
    # answer_message.content = transcription
    # await answer_message.update()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)


