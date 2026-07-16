# Adaptive Crawling Examples

This directory contains examples demonstrating various aspects of Crawl4AI's Adaptive Crawling feature.

## Examples Overview

### 1. `basic_usage.py`
- Simple introduction to adaptive crawling
- Uses default statistical strategy
- Shows how to get crawl statistics and relevant content

### 2. `embedding_strategy.py` ⭐ NEW
- Demonstrates the embedding-based strategy for semantic understanding
- Shows query expansion and irrelevance detection
- Includes configuration for both local and API-based embeddings

### 3. `embedding_vs_statistical.py` ⭐ NEW
- Direct comparison between statistical and embedding strategies
- Helps you choose the right strategy for your use case
- Shows performance and accuracy trade-offs

### 4. `embedding_configuration.py` ⭐ NEW
- Advanced configuration options for embedding strategy
- Parameter tuning guide for different scenarios
- Examples for research, exploration, and quality-focused crawling

### 5. `advanced_configuration.py`
- Shows various configuration options for both strategies
- Demonstrates threshold tuning and performance optimization

### 6. `custom_strategies.py`
- How to implement your own crawling strategy
- Extends the base CrawlStrategy class
- Advanced use case for specialized requirements

### 7. `export_import_kb.py`
- Export crawled knowledge base to JSONL
- Import and continue crawling from saved state
- Useful for building persistent knowledge bases

## Quick Start

For your first adaptive crawling experience, run:

```bash
python basic_usage.py
```

To try the new embedding strategy with semantic understanding:

```bash
python embedding_strategy.py
```

To compare strategies and see which works best for your use case:

```bash
python embedding_vs_statistical.py
```

## Strategy Selection Guide

### Use Statistical Strategy (Default) When:
- Working with technical documentation
- Queries contain specific terms or code
- Speed is critical
- No API access available

### Use Embedding Strategy When:
- Queries are conceptual or ambiguous
- Need semantic understanding beyond exact matches
- Want to detect irrelevant content
- Working with diverse content sources

## Requirements

- Crawl4AI installed
- For embedding strategy with local models: `sentence-transformers`
- For embedding strategy with OpenAI: Set `OPENAI_API_KEY` environment variable

## Learn More

- [Adaptive Crawling Documentation](https://docs.crawl4ai.com/core/adaptive-crawling/)
- [Mathematical Framework](https://github.com/unclecode/crawl4ai/blob/main/PROGRESSIVE_CRAWLING.md)
- [Blog: The Adaptive Crawling Revolution](https://docs.crawl4ai.com/blog/adaptive-crawling-revolution/)