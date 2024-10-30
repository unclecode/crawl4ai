# Crawl4AI

## Episode 13: Chunking Strategies for Large Text Processing

### Quick Intro
Explain Regex, NLP, and Fixed-Length chunking, and when to use each. Demo: Chunk a large article or document for processing by topics or sentences.

Here’s a structured outline for the **Chunking Strategies for Large Text Processing** video, emphasizing how chunking works within extraction and why it’s crucial for effective data aggregation.

Here’s a structured outline for the **Chunking Strategies for Large Text Processing** video, explaining each strategy, when to use it, and providing examples to illustrate.

---

### **12. Chunking Strategies for Large Text Processing**

#### **1. Introduction to Chunking in Crawl4AI**
   - **What is Chunking**: Chunking is the process of dividing large text into manageable sections or “chunks,” enabling efficient processing in extraction tasks.
   - **Why It’s Needed**:
     - When processing large text, feeding it directly into an extraction function (like `F(x)`) can overwhelm memory or token limits.
     - Chunking breaks down `x` (the text) into smaller pieces, which are processed sequentially or in parallel by the extraction function, with the final result being an aggregation of all chunks’ processed output.

#### **2. Key Chunking Strategies and Use Cases**
   - Crawl4AI offers various chunking strategies to suit different text structures, chunk sizes, and processing requirements.
   - **Choosing a Strategy**: Select based on the type of text (e.g., articles, transcripts) and extraction needs (e.g., simple splitting or context-sensitive processing).

#### **3. Strategy 1: Regex-Based Chunking**
   - **Description**: Uses regular expressions to split text based on specified patterns (e.g., paragraphs or section breaks).
   - **Use Case**: Ideal for dividing text by paragraphs or larger logical blocks where sections are clearly separated by line breaks or punctuation.
   - **Example**:
     - **Pattern**: `r'\n\n'` for double line breaks.
     ```python
     chunker = RegexChunking(patterns=[r'\n\n'])
     text_chunks = chunker.chunk(long_text)
     print(text_chunks)  # Output: List of paragraphs
     ```
   - **Pros**: Flexible for pattern-based chunking.
   - **Cons**: Limited to text with consistent formatting.

#### **4. Strategy 2: NLP Sentence-Based Chunking**
   - **Description**: Uses NLP to split text by sentences, ensuring grammatically complete segments.
   - **Use Case**: Useful for extracting individual statements, such as in news articles, quotes, or legal text.
   - **Example**:
     ```python
     chunker = NlpSentenceChunking()
     sentence_chunks = chunker.chunk(long_text)
     print(sentence_chunks)  # Output: List of sentences
     ```
   - **Pros**: Maintains sentence structure, ideal for tasks needing semantic completeness.
   - **Cons**: May create very small chunks, which could limit contextual extraction.

#### **5. Strategy 3: Topic-Based Segmentation Using TextTiling**
   - **Description**: Segments text into topics using TextTiling, identifying topic shifts and key segments.
   - **Use Case**: Ideal for long articles, reports, or essays where each section covers a different topic.
   - **Example**:
     ```python
     chunker = TopicSegmentationChunking(num_keywords=3)
     topic_chunks = chunker.chunk_with_topics(long_text)
     print(topic_chunks)  # Output: List of topic segments with keywords
     ```
   - **Pros**: Groups related content, preserving topical coherence.
   - **Cons**: Depends on identifiable topic shifts, which may not be present in all texts.

#### **6. Strategy 4: Fixed-Length Word Chunking**
   - **Description**: Splits text into chunks based on a fixed number of words.
   - **Use Case**: Ideal for text where exact segment size is required, such as processing word-limited documents for LLMs.
   - **Example**:
     ```python
     chunker = FixedLengthWordChunking(chunk_size=100)
     word_chunks = chunker.chunk(long_text)
     print(word_chunks)  # Output: List of 100-word chunks
     ```
   - **Pros**: Ensures uniform chunk sizes, suitable for token-based extraction limits.
   - **Cons**: May split sentences, affecting semantic coherence.

#### **7. Strategy 5: Sliding Window Chunking**
   - **Description**: Uses a fixed window size with a step, creating overlapping chunks to maintain context.
   - **Use Case**: Useful for maintaining context across sections, as with documents where context is needed for neighboring sections.
   - **Example**:
     ```python
     chunker = SlidingWindowChunking(window_size=100, step=50)
     window_chunks = chunker.chunk(long_text)
     print(window_chunks)  # Output: List of overlapping word chunks
     ```
   - **Pros**: Retains context across adjacent chunks, ideal for complex semantic extraction.
   - **Cons**: Overlap increases data size, potentially impacting processing time.

#### **8. Strategy 6: Overlapping Window Chunking**
   - **Description**: Similar to sliding windows but with a defined overlap, allowing chunks to share content at the edges.
   - **Use Case**: Suitable for handling long texts with essential overlapping information, like research articles or medical records.
   - **Example**:
     ```python
     chunker = OverlappingWindowChunking(window_size=1000, overlap=100)
     overlap_chunks = chunker.chunk(long_text)
     print(overlap_chunks)  # Output: List of overlapping chunks with defined overlap
     ```
   - **Pros**: Allows controlled overlap for consistent content coverage across chunks.
   - **Cons**: Redundant data in overlapping areas may increase computation.

#### **9. Practical Example: Using Chunking with an Extraction Strategy**
   - **Goal**: Combine chunking with an extraction strategy to process large text effectively.
   - **Example Code**:
     ```python
     from crawl4ai.extraction_strategy import LLMExtractionStrategy

     async def extract_large_text():
         # Initialize chunker and extraction strategy
         chunker = FixedLengthWordChunking(chunk_size=200)
         extraction_strategy = LLMExtractionStrategy(provider="openai/gpt-4", api_token="your_api_token")
         
         # Split text into chunks
         text_chunks = chunker.chunk(large_text)
         
         async with AsyncWebCrawler() as crawler:
             for chunk in text_chunks:
                 result = await crawler.arun(
                     url="https://example.com",
                     extraction_strategy=extraction_strategy,
                     content=chunk
                 )
                 print(result.extracted_content)
     ```

   - **Explanation**:
     - `chunker.chunk()`: Divides the `large_text` into smaller segments based on the chosen strategy.
     - `extraction_strategy`: Processes each chunk separately, and results are then aggregated to form the final output.

#### **10. Choosing the Right Chunking Strategy**
   - **Text Structure**: If text has clear sections (e.g., paragraphs, topics), use Regex or Topic Segmentation.
   - **Extraction Needs**: If context is crucial, consider Sliding or Overlapping Window Chunking.
   - **Processing Constraints**: For word-limited extractions (e.g., LLMs with token limits), Fixed-Length Word Chunking is often most effective.

#### **11. Wrap Up & Next Steps**
   - Recap the benefits of each chunking strategy and when to use them in extraction workflows.
   - Tease the next video: **Hooks and Custom Workflow with AsyncWebCrawler**, focusing on customizing crawler behavior with hooks for a fine-tuned extraction process.

---

This outline provides a complete understanding of chunking strategies, explaining each method’s strengths and best-use scenarios to help users process large texts effectively in Crawl4AI.