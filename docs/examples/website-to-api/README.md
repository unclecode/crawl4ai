# Web Scraper API with Custom Model Support

A powerful web scraping API that converts any website into structured data using AI. Features a beautiful minimalist frontend interface and support for custom LLM models!

## Features

- **AI-Powered Scraping**: Provide a URL and plain English query to extract structured data
- **Beautiful Frontend**: Modern minimalist black-and-white interface with smooth UX
- **Custom Model Support**: Use any LLM provider (OpenAI, Gemini, Anthropic, etc.) with your own API keys
- **Model Management**: Save, list, and manage multiple model configurations via web interface
- **Dual Scraping Approaches**: Choose between Schema-based (faster) or LLM-based (more flexible) extraction
- **API Request History**: Automatic saving and display of all API requests with cURL commands
- **Schema Caching**: Intelligent caching of generated schemas for faster subsequent requests
- **Duplicate Prevention**: Avoids saving duplicate requests (same URL + query)
- **RESTful API**: Easy-to-use HTTP endpoints for all operations

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python app.py
```

The server will start on `http://localhost:8000` with a beautiful web interface!

### 3. Using the Web Interface

Once the server is running, open your browser and go to `http://localhost:8000` to access the modern web interface!

#### Pages:
- **Scrape Data**: Enter URLs and queries to extract structured data
- **Models**: Manage your AI model configurations (add, list, delete)
- **API Requests**: View history of all scraping requests with cURL commands

#### Features:
- **Minimalist Design**: Clean black-and-white theme inspired by modern web apps
- **Real-time Results**: See extracted data in formatted JSON
- **Copy to Clipboard**: Easy copying of results
- **Toast Notifications**: User-friendly feedback
- **Dual Scraping Modes**: Choose between Schema-based and LLM-based approaches

## Model Management

### Adding Models via Web Interface

1. Go to the **Models** page
2. Enter your model details:
   - **Provider**: LLM provider (e.g., `gemini/gemini-2.5-flash`, `openai/gpt-4o`)
   - **API Token**: Your API key for the provider
3. Click "Add Model"

### API Usage for Model Management

#### Save a Model Configuration

```bash
curl -X POST "http://localhost:8000/models" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini/gemini-2.5-flash",
    "api_token": "your-api-key-here"
  }'
```

#### List Saved Models

```bash
curl -X GET "http://localhost:8000/models"
```

#### Delete a Model Configuration

```bash
curl -X DELETE "http://localhost:8000/models/my-gemini"
```

## Scraping Approaches

### 1. Schema-based Scraping (Faster)
- Generates CSS selectors for targeted extraction
- Caches schemas for repeated requests
- Faster execution for structured websites

### 2. LLM-based Scraping (More Flexible)
- Direct LLM extraction without schema generation
- More flexible for complex or dynamic content
- Better for unstructured data extraction

## Supported LLM Providers

The API supports any LLM provider that crawl4ai supports, including:

- **Google Gemini**: `gemini/gemini-2.5-flash`, `gemini/gemini-pro`
- **OpenAI**: `openai/gpt-4`, `openai/gpt-3.5-turbo`
- **Anthropic**: `anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`
- **And more...**

## API Endpoints

### Core Endpoints

- `POST /scrape` - Schema-based scraping
- `POST /scrape-with-llm` - LLM-based scraping
- `GET /schemas` - List cached schemas
- `POST /clear-cache` - Clear schema cache
- `GET /health` - Health check

### Model Management Endpoints

- `GET /models` - List saved model configurations
- `POST /models` - Save a new model configuration
- `DELETE /models/{model_name}` - Delete a model configuration

### API Request History

- `GET /saved-requests` - List all saved API requests
- `DELETE /saved-requests/{request_id}` - Delete a saved request

## Request/Response Examples

### Scrape Request

```json
{
  "url": "https://example.com",
  "query": "Extract the product name, price, and description",
  "model_name": "my-custom-model"
}
```

### Scrape Response

```json
{
  "success": true,
  "url": "https://example.com",
  "query": "Extract the product name, price, and description",
  "extracted_data": {
    "product_name": "Example Product",
    "price": "$99.99",
    "description": "This is an example product description"
  },
  "schema_used": { ... },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Model Configuration Request

```json
{
  "provider": "gemini/gemini-2.5-flash",
  "api_token": "your-api-key-here"
}
```

## Testing

Run the test script to verify the model management functionality:

```bash
python test_models.py
```

## File Structure

```
parse_example/
├── api_server.py          # FastAPI server with all endpoints
├── web_scraper_lib.py     # Core scraping library
├── test_models.py         # Test script for model management
├── requirements.txt       # Dependencies
├── static/               # Frontend files
│   ├── index.html        # Main HTML interface
│   ├── styles.css        # CSS styles (minimalist theme)
│   └── script.js         # JavaScript functionality
├── schemas/              # Cached schemas
├── models/               # Saved model configurations
├── saved_requests/       # API request history
└── README.md            # This file
```

## Advanced Usage

### Using the Library Directly

```python
from web_scraper_lib import WebScraperAgent

# Initialize agent
agent = WebScraperAgent()

# Save a model configuration
agent.save_model_config(
    model_name="my-model",
    provider="openai/gpt-4",
    api_token="your-api-key"
)

# Schema-based scraping
result = await agent.scrape_data(
    url="https://example.com",
    query="Extract product information",
    model_name="my-model"
)

# LLM-based scraping
result = await agent.scrape_data_with_llm(
    url="https://example.com",
    query="Extract product information",
    model_name="my-model"
)
```

### Schema Caching

The system automatically caches generated schemas based on URL and query combinations:

- **First request**: Generates schema using AI
- **Subsequent requests**: Uses cached schema for faster extraction

### API Request History

All API requests are automatically saved with:
- Request details (URL, query, model used)
- Response data
- Timestamp
- cURL command for re-execution

### Duplicate Prevention

The system prevents saving duplicate requests:
- Same URL + query combinations are not saved multiple times
- Returns existing request ID for duplicates
- Keeps the API request history clean

## Error Handling

The API provides detailed error messages for common issues:

- Invalid URLs
- Missing model configurations
- API key errors
- Network timeouts
- Parsing errors
