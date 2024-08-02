# Installation 💻

There are three ways to use Crawl4AI:

1. As a library (Recommended).
2. As a local server (Docker) or using the REST API.
3. As a local server (Docker) using the pre-built image from Docker Hub.

## Option 1: Library Installation

You can try this Colab for a quick start: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1sJPAmeLj5PMrg2VgOwMJ2ubGIcK0cJeX#scrollTo=g1RrmI4W_rPk)

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

## Option 2: Using Docker for Local Server

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

## Option 3: Using the Pre-built Image from Docker Hub

You can use pre-built Crawl4AI images from Docker Hub, which are available for all platforms (Mac, Linux, Windows). We have official images as well as a community-contributed image (Thanks to https://github.com/FractalMind):

### Default Installation

```bash

# Pull the image

docker pull unclecode/crawl4ai:latest

# Run the container

docker run -d -p 8000:80 unclecode/crawl4ai:latest

```

### Community-Contributed Image

A stable version of Crawl4AI is also available, created and maintained by a community member:

```bash

# Pull the community-contributed image

docker pull ryser007/crawl4ai:stable

# Run the container

docker run -d -p 8000:80 ryser007/crawl4ai:stable

```

We'd like to express our gratitude to GitHub user [@FractalMind](https://github.com/FractalMind) for creating and maintaining this stable version of the Crawl4AI Docker image. Community contributions like this are invaluable to the project.


### Testing the Installation

After running the container, you can test if it's working correctly:

- On Mac and Linux:

  ```bash

  curl http://localhost:8000

  ```

- On Windows (PowerShell):

  ```powershell

  Invoke-WebRequest -Uri http://localhost:8000

  ```

  Or open a web browser and navigate to http://localhost:8000

