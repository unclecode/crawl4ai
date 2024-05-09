import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Default provider
DEFAULT_PROVIDER = "openai/gpt-4-turbo"

# Provider-model dictionary
PROVIDER_MODELS = {
    "groq/llama3-70b-8192": os.getenv("GROQ_API_KEY", "YOUR_GROQ_TOKEN"),
    "groq/llama3-8b-8192": os.getenv("GROQ_API_KEY", "YOUR_GROQ_TOKEN"),
    "openai/gpt-3.5-turbo": os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_TOKEN"),
    "openai/gpt-4-turbo": os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_TOKEN"),
    "anthropic/claude-3-haiku-20240307": os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_TOKEN"),
    "anthropic/claude-3-opus-20240229": os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_TOKEN"),
    "anthropic/claude-3-sonnet-20240229": os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_TOKEN"),
}

# Chunk token threshold
CHUNK_TOKEN_THRESHOLD = 1000

# Threshold for the minimum number of word in a HTML tag to be considered 
MIN_WORD_THRESHOLD = 5
