## Chunking Strategies 📚

Crawl4AI provides several powerful chunking strategies to divide text into manageable parts for further processing. Each strategy has unique characteristics and is suitable for different scenarios. Let's explore them one by one.

### RegexChunking

`RegexChunking` splits text using regular expressions. This is ideal for creating chunks based on specific patterns like paragraphs or sentences.

#### When to Use
- Great for structured text with consistent delimiters.
- Suitable for documents where specific patterns (e.g., double newlines, periods) indicate logical chunks.

#### Parameters
- `patterns` (list, optional): Regular expressions used to split the text. Default is to split by double newlines (`['\n\n']`).

#### Example
```python
from crawl4ai.chunking_strategy import RegexChunking

# Define patterns for splitting text
patterns = [r'\n\n', r'\. ']
chunker = RegexChunking(patterns=patterns)

# Sample text
text = "This is a sample text. It will be split into chunks.\n\nThis is another paragraph."

# Chunk the text
chunks = chunker.chunk(text)
print(chunks)
```

### NlpSentenceChunking

`NlpSentenceChunking` uses NLP models to split text into sentences, ensuring accurate sentence boundaries.

#### When to Use
- Ideal for texts where sentence boundaries are crucial.
- Useful for creating chunks that preserve grammatical structures.

#### Parameters
- None.

#### Example
```python
from crawl4ai.chunking_strategy import NlpSentenceChunking

chunker = NlpSentenceChunking()

# Sample text
text = "This is a sample text. It will be split into sentences. Here's another sentence."

# Chunk the text
chunks = chunker.chunk(text)
print(chunks)
```

### TopicSegmentationChunking

`TopicSegmentationChunking` employs the TextTiling algorithm to segment text into topic-based chunks. This method identifies thematic boundaries.

#### When to Use
- Perfect for long documents with distinct topics.
- Useful when preserving topic continuity is more important than maintaining text order.

#### Parameters
- `num_keywords` (int, optional): Number of keywords for each topic segment. Default is `3`.

#### Example
```python
from crawl4ai.chunking_strategy import TopicSegmentationChunking

chunker = TopicSegmentationChunking(num_keywords=3)

# Sample text
text = "This document contains several topics. Topic one discusses AI. Topic two covers machine learning."

# Chunk the text
chunks = chunker.chunk(text)
print(chunks)
```

### FixedLengthWordChunking

`FixedLengthWordChunking` splits text into chunks based on a fixed number of words. This ensures each chunk has approximately the same length.

#### When to Use
- Suitable for processing large texts where uniform chunk size is important.
- Useful when the number of words per chunk needs to be controlled.

#### Parameters
- `chunk_size` (int, optional): Number of words per chunk. Default is `100`.

#### Example
```python
from crawl4ai.chunking_strategy import FixedLengthWordChunking

chunker = FixedLengthWordChunking(chunk_size=10)

# Sample text
text = "This is a sample text. It will be split into chunks of fixed length."

# Chunk the text
chunks = chunker.chunk(text)
print(chunks)
```

### SlidingWindowChunking

`SlidingWindowChunking` uses a sliding window approach to create overlapping chunks. Each chunk has a fixed length, and the window slides by a specified step size.

#### When to Use
- Ideal for creating overlapping chunks to preserve context.
- Useful for tasks where context from adjacent chunks is needed.

#### Parameters
- `window_size` (int, optional): Number of words in each chunk. Default is `100`.
- `step` (int, optional): Number of words to slide the window. Default is `50`.

#### Example
```python
from crawl4ai.chunking_strategy import SlidingWindowChunking

chunker = SlidingWindowChunking(window_size=10, step=5)

# Sample text
text = "This is a sample text. It will be split using a sliding window approach to preserve context."

# Chunk the text
chunks = chunker.chunk(text)
print(chunks)
```

With these chunking strategies, you can choose the best method to divide your text based on your specific needs. Whether you need precise sentence boundaries, topic-based segmentation, or uniform chunk sizes, Crawl4AI has you covered. Happy chunking! 📝✨
