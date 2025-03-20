from abc import ABC, abstractmethod
import re
from collections import Counter
import string
from .model_loader import load_nltk_punkt

# Define the abstract base class for chunking strategies
class ChunkingStrategy(ABC):
    """
    Abstract base class for chunking strategies.
    """

    @abstractmethod
    def chunk(self, text: str) -> list:
        """
        Abstract method to chunk the given text.

        Args:
            text (str): The text to chunk.

        Returns:
            list: A list of chunks.
        """
        pass


# Create an identity chunking strategy f(x) = [x]
class IdentityChunking(ChunkingStrategy):
    """
    Chunking strategy that returns the input text as a single chunk.
    """

    def chunk(self, text: str) -> list:
        return [text]


# Regex-based chunking
class RegexChunking(ChunkingStrategy):
    """
    Chunking strategy that splits text based on regular expression patterns.
    """

    def __init__(self, patterns=None, **kwargs):
        """
        Initialize the RegexChunking object.

        Args:
            patterns (list): A list of regular expression patterns to split text.
        """
        if patterns is None:
            patterns = [r"\n\n"]  # Default split pattern
        self.patterns = patterns

    def chunk(self, text: str) -> list:
        paragraphs = [text]
        for pattern in self.patterns:
            new_paragraphs = []
            for paragraph in paragraphs:
                new_paragraphs.extend(re.split(pattern, paragraph))
            paragraphs = new_paragraphs
        return paragraphs


# NLP-based sentence chunking
class NlpSentenceChunking(ChunkingStrategy):
    """
    Chunking strategy that splits text into sentences using NLTK's sentence tokenizer.
    """

    def __init__(self, **kwargs):
        """
        Initialize the NlpSentenceChunking object.
        """
        from crawl4ai.le.legacy.model_loader import load_nltk_punkt
        load_nltk_punkt()

    def chunk(self, text: str) -> list:
        # Improved regex for sentence splitting
        # sentence_endings = re.compile(
        #     r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<![A-Z][A-Z]\.)(?<![A-Za-z]\.)(?<=\.|\?|\!|\n)\s'
        # )
        # sentences = sentence_endings.split(text)
        # sens =  [sent.strip() for sent in sentences if sent]
        from nltk.tokenize import sent_tokenize

        sentences = sent_tokenize(text)
        sens = [sent.strip() for sent in sentences]

        return list(set(sens))


# Topic-based segmentation using TextTiling
class TopicSegmentationChunking(ChunkingStrategy):
    """
    Chunking strategy that segments text into topics using NLTK's TextTilingTokenizer.

    How it works:
    1. Segment the text into topics using TextTilingTokenizer
    2. Extract keywords for each topic segment
    """

    def __init__(self, num_keywords=3, **kwargs):
        """
        Initialize the TopicSegmentationChunking object.

        Args:
            num_keywords (int): The number of keywords to extract for each topic segment.
        """
        import nltk as nl

        self.tokenizer = nl.tokenize.TextTilingTokenizer()
        self.num_keywords = num_keywords

    def chunk(self, text: str) -> list:
        # Use the TextTilingTokenizer to segment the text
        segmented_topics = self.tokenizer.tokenize(text)
        return segmented_topics

    def extract_keywords(self, text: str) -> list:
        # Tokenize and remove stopwords and punctuation
        import nltk as nl

        tokens = nl.toknize.word_tokenize(text)
        tokens = [
            token.lower()
            for token in tokens
            if token not in nl.corpus.stopwords.words("english")
            and token not in string.punctuation
        ]

        # Calculate frequency distribution
        freq_dist = Counter(tokens)
        keywords = [word for word, freq in freq_dist.most_common(self.num_keywords)]
        return keywords

    def chunk_with_topics(self, text: str) -> list:
        # Segment the text into topics
        segments = self.chunk(text)
        # Extract keywords for each topic segment
        segments_with_topics = [
            (segment, self.extract_keywords(segment)) for segment in segments
        ]
        return segments_with_topics


# Fixed-length word chunks
class FixedLengthWordChunking(ChunkingStrategy):
    """
    Chunking strategy that splits text into fixed-length word chunks.

    How it works:
    1. Split the text into words
    2. Create chunks of fixed length
    3. Return the list of chunks
    """

    def __init__(self, chunk_size=100, **kwargs):
        """
        Initialize the fixed-length word chunking strategy with the given chunk size.

        Args:
            chunk_size (int): The size of each chunk in words.
        """
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list:
        words = text.split()
        return [
            " ".join(words[i : i + self.chunk_size])
            for i in range(0, len(words), self.chunk_size)
        ]


# Sliding window chunking
class SlidingWindowChunking(ChunkingStrategy):
    """
    Chunking strategy that splits text into overlapping word chunks.

    How it works:
    1. Split the text into words
    2. Create chunks of fixed length
    3. Return the list of chunks
    """

    def __init__(self, window_size=100, step=50, **kwargs):
        """
        Initialize the sliding window chunking strategy with the given window size and
        step size.

        Args:
            window_size (int): The size of the sliding window in words.
            step (int): The step size for sliding the window in words.
        """
        self.window_size = window_size
        self.step = step

    def chunk(self, text: str) -> list:
        words = text.split()
        chunks = []

        if len(words) <= self.window_size:
            return [text]

        for i in range(0, len(words) - self.window_size + 1, self.step):
            chunk = " ".join(words[i : i + self.window_size])
            chunks.append(chunk)

        # Handle the last chunk if it doesn't align perfectly
        if i + self.window_size < len(words):
            chunks.append(" ".join(words[-self.window_size :]))

        return chunks


class OverlappingWindowChunking(ChunkingStrategy):
    """
    Chunking strategy that splits text into overlapping word chunks.

    How it works:
    1. Split the text into words using whitespace
    2. Create chunks of fixed length equal to the window size
    3. Slide the window by the overlap size
    4. Return the list of chunks
    """

    def __init__(self, window_size=1000, overlap=100, **kwargs):
        """
        Initialize the overlapping window chunking strategy with the given window size and
        overlap size.

        Args:
            window_size (int): The size of the window in words.
            overlap (int): The size of the overlap between consecutive chunks in words.
        """
        self.window_size = window_size
        self.overlap = overlap

    def chunk(self, text: str) -> list:
        words = text.split()
        chunks = []

        if len(words) <= self.window_size:
            return [text]

        start = 0
        while start < len(words):
            end = start + self.window_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            if end >= len(words):
                break

            start = end - self.overlap

        return chunks
