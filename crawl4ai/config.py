import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Default provider, ONLY used when the extraction strategy is LLMExtractionStrategy
DEFAULT_PROVIDER = "openai/gpt-4o"
DEFAULT_PROVIDER_API_KEY = "OPENAI_API_KEY"
MODEL_REPO_BRANCH = "new-release-0.0.2"
# Provider-model dictionary, ONLY used when the extraction strategy is LLMExtractionStrategy
PROVIDER_MODELS = {
    "ollama/llama3": "no-token-needed",  # Any model from Ollama no need for API token
    "groq/llama3-70b-8192": os.getenv("GROQ_API_KEY"),
    "groq/llama3-8b-8192": os.getenv("GROQ_API_KEY"),
    "openai/gpt-4o-mini": os.getenv("OPENAI_API_KEY"),
    "openai/gpt-4o": os.getenv("OPENAI_API_KEY"),
    "openai/o1-mini": os.getenv("OPENAI_API_KEY"),
    "openai/o1-preview": os.getenv("OPENAI_API_KEY"),
    "openai/o3-mini": os.getenv("OPENAI_API_KEY"),
    "openai/o3-mini-high": os.getenv("OPENAI_API_KEY"),
    "anthropic/claude-3-haiku-20240307": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic/claude-3-opus-20240229": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic/claude-3-sonnet-20240229": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic/claude-3-5-sonnet-20240620": os.getenv("ANTHROPIC_API_KEY"),
    "gemini/gemini-pro": os.getenv("GEMINI_API_KEY"),
    'gemini/gemini-1.5-pro': os.getenv("GEMINI_API_KEY"),
    'gemini/gemini-2.0-flash': os.getenv("GEMINI_API_KEY"),
    'gemini/gemini-2.0-flash-exp': os.getenv("GEMINI_API_KEY"),
    'gemini/gemini-2.0-flash-lite-preview-02-05': os.getenv("GEMINI_API_KEY"),
    "deepseek/deepseek-chat": os.getenv("DEEPSEEK_API_KEY"),
}
PROVIDER_MODELS_PREFIXES = {
    "ollama": "no-token-needed",  # Any model from Ollama no need for API token
    "groq": os.getenv("GROQ_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
}

# Chunk token threshold
CHUNK_TOKEN_THRESHOLD = 2**11  # 2048 tokens
OVERLAP_RATE = 0.1
WORD_TOKEN_RATE = 1.3

# Threshold for the minimum number of word in a HTML tag to be considered
MIN_WORD_THRESHOLD = 1
IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD = 1

IMPORTANT_ATTRS = ["src", "href", "alt", "title", "width", "height"]
ONLY_TEXT_ELIGIBLE_TAGS = [
    "b",
    "i",
    "u",
    "span",
    "del",
    "ins",
    "sub",
    "sup",
    "strong",
    "em",
    "code",
    "kbd",
    "var",
    "s",
    "q",
    "abbr",
    "cite",
    "dfn",
    "time",
    "small",
    "mark",
]
SOCIAL_MEDIA_DOMAINS = [
    "facebook.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "instagram.com",
    "pinterest.com",
    "tiktok.com",
    "snapchat.com",
    "reddit.com",
]

# Threshold for the Image extraction - Range is 1 to 6
# Images are scored based on point based system, to filter based on usefulness. Points are assigned
# to each image based on the following aspects.
# If either height or width exceeds 150px
# If image size is greater than 10Kb
# If alt property is set
# If image format is in jpg, png or webp
# If image is in the first half of the total images extracted from the page
IMAGE_SCORE_THRESHOLD = 2

MAX_METRICS_HISTORY = 1000

NEED_MIGRATION = True
URL_LOG_SHORTEN_LENGTH = 30
SHOW_DEPRECATION_WARNINGS = True
SCREENSHOT_HEIGHT_TRESHOLD = 10000
PAGE_TIMEOUT = 60000
DOWNLOAD_PAGE_TIMEOUT = 60000

# Global user settings with descriptions and default values
USER_SETTINGS = {
    "DEFAULT_LLM_PROVIDER": {
        "default": "openai/gpt-4o",
        "description": "Default LLM provider in 'company/model' format (e.g., 'openai/gpt-4o', 'anthropic/claude-3-sonnet')",
        "type": "string"
    },
    "DEFAULT_LLM_PROVIDER_TOKEN": {
        "default": "",
        "description": "API token for the default LLM provider",
        "type": "string",
        "secret": True
    },
    "VERBOSE": {
        "default": False,
        "description": "Enable verbose output for all commands",
        "type": "boolean"
    },
    "BROWSER_HEADLESS": {
        "default": True,
        "description": "Run browser in headless mode by default",
        "type": "boolean"
    },
    "BROWSER_TYPE": {
        "default": "chromium",
        "description": "Default browser type (chromium or firefox)",
        "type": "string",
        "options": ["chromium", "firefox"]
    },
    "CACHE_MODE": {
        "default": "bypass",
        "description": "Default cache mode (bypass, use, or refresh)",
        "type": "string",
        "options": ["bypass", "use", "refresh"]
    },
    "USER_AGENT_MODE": {
        "default": "default",
        "description": "Default user agent mode (default, random, or mobile)",
        "type": "string",
        "options": ["default", "random", "mobile"]
    }
}
