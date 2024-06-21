# Installation 💻

There are three ways to use Crawl4AI:
1. As a library (Recommended)
2. As a local server (Docker) or using the REST API
3. As a Google Colab notebook. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)

## Library Installation

To install Crawl4AI as a library, follow these steps:

1. Install the package from GitHub:
```
virtualenv venv
source venv/bin/activate
pip install "crawl4ai[all] @ git+https://github.com/unclecode/crawl4ai.git"
```

💡 Better to run the following CLI-command to load the required models. This is optional, but it will boost the performance and speed of the crawler. You need to do this only once.
```
crawl4ai-download-models
```

2. Alternatively, you can clone the repository and install the package locally:
```
virtualenv venv
source venv/bin/activate
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .[all]
```

## Using Docker for Local Server

3. Use Docker to run the local server:
```
# For Mac users
# docker build --platform linux/amd64 -t crawl4ai .
# For other users
# docker build -t crawl4ai .
docker run -d -p 8000:80 crawl4ai
```

## Using Google Colab

You can also use Crawl4AI in a Google Colab notebook for easy setup and experimentation. Simply open the following Colab notebook and follow the instructions: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)
