# Chunking Strategies
Chunking strategies are critical for dividing large texts into manageable parts, enabling effective content processing and extraction. These strategies are foundational in cosine similarity-based extraction techniques, which allow users to retrieve only the most relevant chunks of content for a given query. Additionally, they facilitate direct integration into RAG (Retrieval-Augmented Generation) systems for structured and scalable workflows.

### Why Use Chunking?
1. **Cosine Similarity and Query Relevance**: Prepares chunks for semantic similarity analysis.
2. **RAG System Integration**: Seamlessly processes and stores chunks for retrieval.
3. **Structured Processing**: Allows for diverse segmentation methods, such as sentence-based, topic-based, or windowed approaches.

### Methods of Chunking

#### 1. Regex-Based Chunking
Splits text based on regular expression patterns, useful for coarse segmentation.

**Code Example**:
```python
class RegexChunking:
    def __init__(self, patterns=None):
        self.patterns = patterns or [r'\n\n']  # Default pattern for paragraphs

    def chunk(self, text):
        paragraphs = [text]
        for pattern in self.patterns:
            paragraphs = [seg for p in paragraphs for seg in re.split(pattern, p)]
        return paragraphs

# Example Usage
text = """This is the first paragraph.

This is the second paragraph."""
chunker = RegexChunking()
print(chunker.chunk(text))
```

#### 2. Sentence-Based Chunking
Divides text into sentences using NLP tools, ideal for extracting meaningful statements.

**Code Example**:
```python
from nltk.tokenize import sent_tokenize

class NlpSentenceChunking:
    def chunk(self, text):
        sentences = sent_tokenize(text)
        return [sentence.strip() for sentence in sentences]

# Example Usage
text = "This is sentence one. This is sentence two."
chunker = NlpSentenceChunking()
print(chunker.chunk(text))
```

#### 3. Topic-Based Segmentation
Uses algorithms like TextTiling to create topic-coherent chunks.

**Code Example**:
```python
from nltk.tokenize import TextTilingTokenizer

class TopicSegmentationChunking:
    def __init__(self):
        self.tokenizer = TextTilingTokenizer()

    def chunk(self, text):
        return self.tokenizer.tokenize(text)

# Example Usage
text = """This is an introduction.
This is a detailed discussion on the topic."""
chunker = TopicSegmentationChunking()
print(chunker.chunk(text))
```

#### 4. Fixed-Length Word Chunking
Segments text into chunks of a fixed word count.

**Code Example**:
```python
class FixedLengthWordChunking:
    def __init__(self, chunk_size=100):
        self.chunk_size = chunk_size

    def chunk(self, text):
        words = text.split()
        return [' '.join(words[i:i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]

# Example Usage
text = "This is a long text with many words to be chunked into fixed sizes."
chunker = FixedLengthWordChunking(chunk_size=5)
print(chunker.chunk(text))
```

#### 5. Sliding Window Chunking
Generates overlapping chunks for better contextual coherence.

**Code Example**:
```python
class SlidingWindowChunking:
    def __init__(self, window_size=100, step=50):
        self.window_size = window_size
        self.step = step

    def chunk(self, text):
        words = text.split()
        chunks = []
        for i in range(0, len(words) - self.window_size + 1, self.step):
            chunks.append(' '.join(words[i:i + self.window_size]))
        return chunks

# Example Usage
text = "This is a long text to demonstrate sliding window chunking."
chunker = SlidingWindowChunking(window_size=5, step=2)
print(chunker.chunk(text))
```

### Combining Chunking with Cosine Similarity
To enhance the relevance of extracted content, chunking strategies can be paired with cosine similarity techniques. Here’s an example workflow:

**Code Example**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CosineSimilarityExtractor:
    def __init__(self, query):
        self.query = query
        self.vectorizer = TfidfVectorizer()

    def find_relevant_chunks(self, chunks):
        vectors = self.vectorizer.fit_transform([self.query] + chunks)
        similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        return [(chunks[i], similarities[i]) for i in range(len(chunks))]

# Example Workflow
text = """This is a sample document. It has multiple sentences. 
We are testing chunking and similarity."""

chunker = SlidingWindowChunking(window_size=5, step=3)
chunks = chunker.chunk(text)
query = "testing chunking"
extractor = CosineSimilarityExtractor(query)
relevant_chunks = extractor.find_relevant_chunks(chunks)

print(relevant_chunks)
```
