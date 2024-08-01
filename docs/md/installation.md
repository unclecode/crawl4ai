# Installation 💻

There are three ways to use Crawl4AI:

1. As a library (Recommended)
2. As a local server (Docker) or using the REST API
3. As a Google Colab notebook.    

## Library Installation

Crawl4AI offers flexible installation options to suit various use cases. Choose the option that best fits your needs:

- **Default Installation** (Basic functionality):
```bash
virtualenv venv
source venv/bin/activate
pip install "crawl4ai @ git+https://github.com/unclecode/crawl4ai.git"
```
Use this for basic web crawling and scraping tasks.

- **Installation with PyTorch** (For advanced text clustering):
```bash
virtualenv venv
source venv/bin/activate
pip install "crawl4ai[torch] @ git+https://github.com/unclecode/crawl4ai.git"
```
Choose this if you need the CosineSimilarity cluster strategy.

- **Installation with Transformers** (For summarization and Hugging Face models):
```bash
virtualenv venv
source venv/bin/activate
pip install "crawl4ai[transformer] @ git+https://github.com/unclecode/crawl4ai.git"
```
Opt for this if you require text summarization or plan to use Hugging Face models.

- **Full Installation** (All features):
```bash
virtualenv venv
source venv/bin/activate
pip install "crawl4ai[all] @ git+https://github.com/unclecode/crawl4ai.git"
```
This installs all dependencies for full functionality.

- **Development Installation** (For contributors):
```bash
virtualenv venv
source venv/bin/activate
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e ".[all]"
```
Use this if you plan to modify the source code.

💡 After installation, if you have used "torch", "transformer" or "all", it's recommended to run the following CLI command to load the required models. This is optional but will boost the performance and speed of the crawler. You need to do this only once, this is only for when you install using []
```bash
crawl4ai-download-models
```

## Using Docker for Local Server

Crawl4AI can be run as a local server using Docker. The Dockerfile supports different installation options to cater to various use cases. Here's how you can build and run the Docker image:

### Default Installation

The default installation includes the basic Crawl4AI package without additional dependencies or pre-downloaded models.

```bash
# For Mac users (M1/M2)
docker build --platform linux/amd64 -t crawl4ai .

# For other users
docker build -t crawl4ai .

# Run the container
docker run -d -p 8000:80 crawl4ai
```

### Full Installation (All Dependencies and Models)

This option installs all dependencies and downloads the models.

```bash
# For Mac users (M1/M2)
docker build --platform linux/amd64 --build-arg INSTALL_OPTION=all -t crawl4ai:all .

# For other users
docker build --build-arg INSTALL_OPTION=all -t crawl4ai:all .

# Run the container
docker run -d -p 8000:80 crawl4ai:all
```

### Torch Installation

This option installs torch-related dependencies and downloads the models.

```bash
# For Mac users (M1/M2)
docker build --platform linux/amd64 --build-arg INSTALL_OPTION=torch -t crawl4ai:torch .

# For other users
docker build --build-arg INSTALL_OPTION=torch -t crawl4ai:torch .

# Run the container
docker run -d -p 8000:80 crawl4ai:torch
```

### Transformer Installation

This option installs transformer-related dependencies and downloads the models.

```bash
# For Mac users (M1/M2)
docker build --platform linux/amd64 --build-arg INSTALL_OPTION=transformer -t crawl4ai:transformer .

# For other users
docker build --build-arg INSTALL_OPTION=transformer -t crawl4ai:transformer .

# Run the container
docker run -d -p 8000:80 crawl4ai:transformer
```

### Notes

- The `--platform linux/amd64` flag is necessary for Mac users with M1/M2 chips to ensure compatibility.
- The `-t` flag tags the image with a name (and optionally a tag in the 'name:tag' format).
- The `-d` flag runs the container in detached mode.
- The `-p 8000:80` flag maps port 8000 on the host to port 80 in the container.

Choose the installation option that best suits your needs. The default installation is suitable for basic usage, while the other options provide additional capabilities for more advanced use cases.

## Using Google Colab


You can also use Crawl4AI in a Google Colab notebook for easy setup and experimentation. Simply open the following Colab notebook and follow the instructions: 

    ⚠️ This collab is a bit outdated. I'm updating it with the newest versions, so please refer to the website for the latest documentation. This will be updated in a few days, and you'll have the latest version here. Thank you so much.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)