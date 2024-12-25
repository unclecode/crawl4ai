```markdown
# Chunking Strategies

> Break large texts into manageable chunks for relevance and retrieval workflows.

Enables segmentation for similarity-based retrieval and integration into RAG pipelines.

## Why Use Chunking?

- Prepare text for cosine similarity scoring  
- Integrate into RAG systems  
- Support multiple segmentation methods (regex, sentences, topics, fixed-length, sliding windows)

## Methods of Chunking

- [Regex-Based Chunking]: Splits text on patterns (e.g., `\n\n`)
```python
class RegexChunking:
    def __init__(self, patterns=[r'\n\n']):
        self.patterns = patterns
    def chunk(self, text):
        parts = [text]
        for p in self.patterns:
            parts = [seg for pr in parts for seg in re.split(p, pr)]
        return parts
```

- [Sentence-Based Chunking]: Uses NLP (e.g., `nltk.sent_tokenize`) for sentence-level chunks
```python
from nltk.tokenize import sent_tokenize
class NlpSentenceChunking:
    def chunk(self, text):
        return sent_tokenize(text)
```

- [Topic-Based Segmentation]: Leverages `TextTilingTokenizer` for topic-level segments
```python
from nltk.tokenize import TextTilingTokenizer
class TopicSegmentationChunking:
    def __init__(self):
        self.tokenizer = TextTilingTokenizer()
    def chunk(self, text):
        return self.tokenizer.tokenize(text)
```

- [Fixed-Length Word Chunking]: Chunks by a fixed number of words
```python
class FixedLengthWordChunking:
    def __init__(self, chunk_size=100):
        self.chunk_size = chunk_size
    def chunk(self, text):
        w = text.split()
        return [' '.join(w[i:i+self.chunk_size]) for i in range(0, len(w), self.chunk_size)]
```

- [Sliding Window Chunking]: Overlapping chunks for context retention
```python
class SlidingWindowChunking:
    def __init__(self, window_size=100, step=50):
        self.window_size = window_size
        self.step = step
    def chunk(self, text):
        w = text.split()
        return [' '.join(w[i:i+self.window_size]) for i in range(0, max(len(w)-self.window_size+1, 1), self.step)]
```

## Combining Chunking with Cosine Similarity

- Extract relevant chunks based on a query
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CosineSimilarityExtractor:
    def __init__(self, query):
        self.query = query
        self.vectorizer = TfidfVectorizer()
    def find_relevant_chunks(self, chunks):
        X = self.vectorizer.fit_transform([self.query] + chunks)
        sims = cosine_similarity(X[0:1], X[1:]).flatten()
        return list(zip(chunks, sims))
```

## Optional

- [chuncking_strategies.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/chuncking_strategies.py)
```