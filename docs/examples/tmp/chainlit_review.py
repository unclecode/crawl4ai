from openai import AsyncOpenAI
from chainlit.types import ThreadDict
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
client = AsyncOpenAI()

# Instrument the OpenAI client
cl.instrument_openai()

settings = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.5,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

@cl.action_callback("action_button")
async def on_action(action: cl.Action):
    print("The user clicked on the action button!")

    return "Thank you for clicking on the action button!"

@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="GPT-3.5",
            markdown_description="The underlying LLM model is **GPT-3.5**.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="GPT-4",
            markdown_description="The underlying LLM model is **GPT-4**.",
            icon="https://picsum.photos/250",
        ),
    ]

@cl.on_chat_start
async def on_chat_start():
    
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"],
                initial_index=0,
            ),
            Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
            Slider(
                id="Temperature",
                label="OpenAI - Temperature",
                initial=1,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="SAI_Steps",
                label="Stability AI - Steps",
                initial=30,
                min=10,
                max=150,
                step=1,
                description="Amount of inference steps performed on image generation.",
            ),
            Slider(
                id="SAI_Cfg_Scale",
                label="Stability AI - Cfg_Scale",
                initial=7,
                min=1,
                max=35,
                step=0.1,
                description="Influences how strongly your generation is guided to match your prompt.",
            ),
            Slider(
                id="SAI_Width",
                label="Stability AI - Image Width",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
            Slider(
                id="SAI_Height",
                label="Stability AI - Image Height",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
        ]
    ).send()
    
    chat_profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"starting chat using the {chat_profile} chat profile"
    ).send()
    
    print("A new chat session has started!")
    cl.user_session.set("session", {
        "history": [],
        "context": []
    })  
    
    image = cl.Image(url="https://c.tenor.com/uzWDSSLMCmkAAAAd/tenor.gif", name="cat image", display="inline")

    # Attach the image to the message
    await cl.Message(
        content="You are such a good girl, aren't you?!",
        elements=[image],
    ).send()
    
    text_content = "Hello, this is a text element."
    elements = [
        cl.Text(name="simple_text", content=text_content, display="inline")
    ]

    await cl.Message(
        content="Check out this text element!",
        elements=elements,
    ).send()
    
    elements = [
        cl.Audio(path="./assets/audio.mp3", display="inline"),
    ]
    await cl.Message(
        content="Here is an audio file",
        elements=elements,
    ).send()
    
    await cl.Avatar(
        name="Tool 1",
        url="https://avatars.githubusercontent.com/u/128686189?s=400&u=a1d1553023f8ea0921fba0debbe92a8c5f840dd9&v=4",
    ).send()
    
    await cl.Message(
        content="This message should not have an avatar!", author="Tool 0"
    ).send()
    
    await cl.Message(
        content="This message should have an avatar!", author="Tool 1"
    ).send()
    
    elements = [
        cl.File(
            name="quickstart.py",
            path="./quickstart.py",
            display="inline",
        ),
    ]

    await cl.Message(
        content="This message has a file element", elements=elements
    ).send()
    
    # Sending an action button within a chatbot message
    actions = [
        cl.Action(name="action_button", value="example_value", description="Click me!")
    ]

    await cl.Message(content="Interact with this action button:", actions=actions).send()
    
    # res = await cl.AskActionMessage(
    #     content="Pick an action!",
    #     actions=[
    #         cl.Action(name="continue", value="continue", label="✅ Continue"),
    #         cl.Action(name="cancel", value="cancel", label="❌ Cancel"),
    #     ],
    # ).send()

    # if res and res.get("value") == "continue":
    #     await cl.Message(
    #         content="Continue!",
    #     ).send()
    
    # import plotly.graph_objects as go
    # fig = go.Figure(
    #     data=[go.Bar(y=[2, 1, 3])],
    #     layout_title_text="An example figure",
    # )
    # elements = [cl.Plotly(name="chart", figure=fig, display="inline")]

    # await cl.Message(content="This message has a chart", elements=elements).send()
    
    # Sending a pdf with the local file path
    # elements = [
    #   cl.Pdf(name="pdf1", display="inline", path="./pdf1.pdf")
    # ]

    # cl.Message(content="Look at this local pdf!", elements=elements).send()    

@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)
    
@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")

@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("The user resumed a previous chat session!")




# @cl.on_message
async def on_message(message: cl.Message):
    cl.user_session.get("session")["history"].append({
        "role": "user",
        "content": message.content
    })    
    response = await client.chat.completions.create(
        messages=[
            {
                "content": "You are a helpful bot",
                "role": "system"
            },
            *cl.user_session.get("session")["history"]
        ],
        **settings
    )
    

    # Add assitanr message to the history
    cl.user_session.get("session")["history"].append({
        "role": "assistant",
        "content": response.choices[0].message.content
    })
    
    # msg.content = response.choices[0].message.content
    # await msg.update()
    
    # await cl.Message(content=response.choices[0].message.content).send()

@cl.on_message
async def on_message(message: cl.Message):
    cl.user_session.get("session")["history"].append({
        "role": "user",
        "content": message.content
    })    

    msg = cl.Message(content="")
    await msg.send()    
    
    stream = await client.chat.completions.create(
        messages=[
            {
                "content": "You are a helpful bot",
                "role": "system"
            },
            *cl.user_session.get("session")["history"]
        ],
        stream = True, 
        **settings
    )
    
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)
    
    # Add assitanr message to the history
    cl.user_session.get("session")["history"].append({
        "role": "assistant",
        "content": msg.content
    })    
    await msg.update()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)