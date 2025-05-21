# Prompt-Driven Web Crawler (`prompt_driven_crawler.py`)

## Description

This script performs a recursive crawl of a website starting from a given URL. It uses a user-provided prompt to guide an AI model (LLM) in extracting relevant information from the crawled pages. The extracted content is then saved as individual Markdown files, and a summary of all processed pages is stored in a JSON file.

The crawler navigates web pages up to a specified maximum depth, focusing on content relevant to the user's prompt.

## Prerequisites

1.  **Python**: Python 3.8 or newer installed.
2.  **`crawl4ai` Library**: This script relies on the `crawl4ai` library and its dependencies. These should be installed as per the main project's installation guide or `requirements.txt`.
3.  **OpenAI API Key**: You need an active OpenAI API key to use the LLM-based content extraction features. The script expects this key to be available as an environment variable.

## Setup

1.  **Install Dependencies**:
    Navigate to the root directory of this project (where the main `requirements.txt` is located) and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `crawl4ai` and other necessary packages, including the `openai` library.

2.  **Set OpenAI API Key**:
    You must set the `OPENAI_API_KEY` environment variable.
    *   For Linux/macOS:
        ```bash
        export OPENAI_API_KEY='your_actual_api_key_here'
        ```
    *   For Windows (Command Prompt):
        ```bash
        set OPENAI_API_KEY=your_actual_api_key_here
        ```
    *   For Windows (PowerShell):
        ```bash
        $env:OPENAI_API_KEY="your_actual_api_key_here"
        ```
    Replace `your_actual_api_key_here` with your actual OpenAI API key.

## Running the Script

Execute the script from the root directory of the project using a command like the following:

```bash
python docs/examples/prompt_driven_crawler.py "https://example.com/startpage" "Extract all information about upcoming product releases and their features" --output_dir ./my_crawl_output --max_depth 1
```

### Command-Line Arguments:

*   `start_url` (required): The initial URL from which the crawler will begin.
    *   Example: `"https://example.com/startpage"`
*   `user_prompt` (required): A textual description of the information you are looking to extract. This prompt guides the LLM.
    *   Example: `"Extract all information about upcoming product releases and their features"`
*   `--output_dir` (optional): The directory where the crawled data (Markdown files and JSON summary) will be saved.
    *   Default: `./crawled_output`
    *   Example: `--output_dir ./my_crawl_output`
*   `--max_depth` (optional): The maximum depth the crawler will navigate from the `start_url`. A depth of 0 means only the start URL is processed, a depth of 1 means the start URL and pages directly linked from it, and so on.
    *   Default: `2`
    *   Example: `--max_depth 1`

## Output

The script generates output in the directory specified by `--output_dir`:

1.  **Markdown Files**:
    *   Location: `[output_dir]/markdown/`
    *   For each crawled page deemed relevant and processed by the LLM, a Markdown file is created.
    *   The filename is a sanitized version of the page title or URL.
    *   These files contain the LLM-extracted content relevant to your prompt.

2.  **JSON Summary File**:
    *   Location: `[output_dir]/scraped_data.json`
    *   This file contains a JSON array of objects, where each object represents a successfully processed page. It includes:
        *   `url`: The URL of the crawled page.
        *   `prompt`: The user prompt used for this crawl.
        *   `markdown_file_path`: The absolute path to the saved Markdown file for this page.
        *   `title`: The title of the web page (or "N/A" if not found).
        *   `relevance_score`: The score assigned by the URL relevance scorer (if applicable).

Make sure your `OPENAI_API_KEY` is correctly set before running the script.
The script will create the output directory if it doesn't exist.
Check the console output for progress and any error messages.
