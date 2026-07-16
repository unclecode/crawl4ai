# 🐳 Using Docker (Legacy)

Crawl4AI is available as Docker images for easy deployment. You can either pull directly from Docker Hub (recommended) or build from the repository.

---

<details>
<summary>🐳 <strong>Option 1: Docker Hub (Recommended)</strong></summary>

Choose the appropriate image based on your platform and needs:

### For AMD64 (Regular Linux/Windows):
```bash
# Basic version (recommended)
docker pull unclecode/crawl4ai:basic-amd64
docker run -p 11235:11235 unclecode/crawl4ai:basic-amd64

# Full ML/LLM support
docker pull unclecode/crawl4ai:all-amd64
docker run -p 11235:11235 unclecode/crawl4ai:all-amd64

# With GPU support
docker pull unclecode/crawl4ai:gpu-amd64
docker run -p 11235:11235 unclecode/crawl4ai:gpu-amd64
```

### For ARM64 (M1/M2 Macs, ARM servers):
```bash
# Basic version (recommended)
docker pull unclecode/crawl4ai:basic-arm64
docker run -p 11235:11235 unclecode/crawl4ai:basic-arm64

# Full ML/LLM support
docker pull unclecode/crawl4ai:all-arm64
docker run -p 11235:11235 unclecode/crawl4ai:all-arm64

# With GPU support
docker pull unclecode/crawl4ai:gpu-arm64
docker run -p 11235:11235 unclecode/crawl4ai:gpu-arm64
```

Need more memory? Add `--shm-size`:
```bash
docker run --shm-size=2gb -p 11235:11235 unclecode/crawl4ai:basic-amd64
```

Test the installation:
```bash
curl http://localhost:11235/health
```

### For Raspberry Pi (32-bit) (coming soon):
```bash
# Pull and run basic version (recommended for Raspberry Pi)
docker pull unclecode/crawl4ai:basic-armv7
docker run -p 11235:11235 unclecode/crawl4ai:basic-armv7

# With increased shared memory if needed
docker run --shm-size=2gb -p 11235:11235 unclecode/crawl4ai:basic-armv7
```

Note: Due to hardware constraints, only the basic version is recommended for Raspberry Pi.

</details>

<details>
<summary>🐳 <strong>Option 2: Build from Repository</strong></summary>

Build the image locally based on your platform:

```bash
# Clone the repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai

# For AMD64 (Regular Linux/Windows)
docker build --platform linux/amd64 \
  --tag crawl4ai:local \
  --build-arg INSTALL_TYPE=basic \
  .

# For ARM64 (M1/M2 Macs, ARM servers)
docker build --platform linux/arm64 \
  --tag crawl4ai:local \
  --build-arg INSTALL_TYPE=basic \
  .
```

Build options:
- INSTALL_TYPE=basic (default): Basic crawling features
- INSTALL_TYPE=all: Full ML/LLM support
- ENABLE_GPU=true: Add GPU support

Example with all options:
```bash
docker build --platform linux/amd64 \
  --tag crawl4ai:local \
  --build-arg INSTALL_TYPE=all \
  --build-arg ENABLE_GPU=true \
  .
```

Run your local build:
```bash
# Regular run
docker run -p 11235:11235 crawl4ai:local

# With increased shared memory
docker run --shm-size=2gb -p 11235:11235 crawl4ai:local
```

Test the installation:
```bash
curl http://localhost:11235/health
```

</details>

<details>
<summary>🐳 <strong>Option 3: Using Docker Compose</strong></summary>

Docker Compose provides a more structured way to run Crawl4AI, especially when dealing with environment variables and multiple configurations.

```bash
# Clone the repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
```

### For AMD64 (Regular Linux/Windows):
```bash
# Build and run locally
docker-compose --profile local-amd64 up

# Run from Docker Hub
VERSION=basic docker-compose --profile hub-amd64 up   # Basic version
VERSION=all docker-compose --profile hub-amd64 up     # Full ML/LLM support
VERSION=gpu docker-compose --profile hub-amd64 up     # GPU support
```

### For ARM64 (M1/M2 Macs, ARM servers):
```bash
# Build and run locally
docker-compose --profile local-arm64 up

# Run from Docker Hub
VERSION=basic docker-compose --profile hub-arm64 up   # Basic version
VERSION=all docker-compose --profile hub-arm64 up     # Full ML/LLM support
VERSION=gpu docker-compose --profile hub-arm64 up     # GPU support
```

Environment variables (optional):
```bash
# Create a .env file
CRAWL4AI_API_TOKEN=your_token
OPENAI_API_KEY=your_openai_key
CLAUDE_API_KEY=your_claude_key
```

The compose file includes:
- Memory management (4GB limit, 1GB reserved)
- Shared memory volume for browser support
- Health checks
- Auto-restart policy
- All necessary port mappings

Test the installation:
```bash
curl http://localhost:11235/health
```

</details>

<details>
<summary>🚀 <strong>One-Click Deployment</strong></summary>

Deploy your own instance of Crawl4AI with one click:

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%203.svg)](https://www.digitalocean.com/?repo=https://github.com/unclecode/crawl4ai/tree/0.3.74&refcode=a0780f1bdb3d&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

> 💡 **Recommended specs**: 4GB RAM minimum. Select "professional-xs" or higher when deploying for stable operation.

The deploy will:
- Set up a Docker container with Crawl4AI
- Configure Playwright and all dependencies
- Start the FastAPI server on port `11235`
- Set up health checks and auto-deployment

</details>
