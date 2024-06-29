# Installation 💻

There are three ways to use Crawl4AI:
1. As a library (Recommended)
2. As a local server (Docker) or using the REST API
3. As a Google Colab notebook. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)

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

To run Crawl4AI as a local server using Docker:

```bash
# For Mac users
# docker build --platform linux/amd64 -t crawl4ai .
# For other users
# docker build -t crawl4ai .
docker run -d -p 8000:80 crawl4ai
```

## Using Google Colab

You can also use Crawl4AI in a Google Colab notebook for easy setup and experimentation. Simply open the following Colab notebook and follow the instructions: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)