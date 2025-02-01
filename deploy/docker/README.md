# Crawl4AI Docker Setup

## Quick Start
1. Build the Docker image:
   ```bash
   docker build -t crawl4ai-server:prod .
   ```

2. Run the container:
   ```bash
   docker run -d -p 8000:8000 \
     --env-file .llm.env \
     --name crawl4ai \
     crawl4ai-server:prod
   ```

---

## Configuration Options

### 1. **Using .llm.env File**
Create a `.llm.env` file with your API keys:
```bash
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=your-deepseek-key
```

Run with:
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  crawl4ai-server:prod
```

### 2. **Direct Environment Variables**
Pass keys directly:
```bash
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY="sk-your-key" \
  -e DEEPSEEK_API_KEY="your-deepseek-key" \
  crawl4ai-server:prod
```

### 3. **Copy Host Environment Variables**
Use the `--copy-env` flag to copy `.llm.env` from the host:
```bash
docker run -d -p 8000:8000 \
  --copy-env \
  crawl4ai-server:prod
```

### 4. **Advanced: Docker Compose**
Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  crawl4ai:
    image: crawl4ai-server:prod
    ports:
      - "8000:8000"
    env_file:
      - .llm.env
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

---

## Supported Environment Variables
| Variable               | Description                          |
|------------------------|--------------------------------------|
| `OPENAI_API_KEY`       | OpenAI API key                       |
| `DEEPSEEK_API_KEY`     | DeepSeek API key                     |
| `ANTHROPIC_API_KEY`    | Anthropic API key                    |
| `GROQ_API_KEY`         | Groq API key                         |
| `TOGETHER_API_KEY`     | Together API key                     |
| `LLAMA_CLOUD_API_KEY`  | Llama Cloud API key                  |
| `COHERE_API_KEY`       | Cohere API key                       |
| `MISTRAL_API_KEY`      | Mistral API key                      |
| `PERPLEXITY_API_KEY`   | Perplexity API key                   |
| `VERTEXAI_PROJECT_ID`  | Google Vertex AI project ID          |
| `VERTEXAI_LOCATION`    | Google Vertex AI location            |

---

## Healthcheck
The container includes a healthcheck:
```bash
curl http://localhost:8000/health
```

---

## Troubleshooting
1. **Missing Keys**: Ensure all required keys are set in `.llm.env`.
2. **Permissions**: Run `chmod +x docker-entrypoint.sh` if permissions are denied.
3. **Logs**: Check logs with:
   ```bash
   docker logs crawl4ai
   ```

---

## Security Best Practices
- Never commit `.llm.env` to version control.
- Use Docker secrets in production (Swarm/K8s).
- Rotate keys regularly.


