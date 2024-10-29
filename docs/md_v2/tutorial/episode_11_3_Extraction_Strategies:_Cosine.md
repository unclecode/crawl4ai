# Crawl4AI

## Episode 11: Extraction Strategies: JSON CSS, LLM, and Cosine

### Quick Intro
Introduce JSON CSS Extraction Strategy for structured data, LLM Extraction Strategy for intelligent parsing, and Cosine Strategy for clustering similar content. Demo: Use JSON CSS to scrape product details from an e-commerce site.

Here’s a structured outline for the **Cosine Similarity Strategy** video, covering key concepts, configuration, and a practical example.

---

### **10.3 Cosine Similarity Strategy**

#### **1. Introduction to Cosine Similarity Strategy**
   - The Cosine Similarity Strategy clusters content by semantic similarity, offering an efficient alternative to LLM-based extraction, especially when speed is a priority.
   - Ideal for grouping similar sections of text, this strategy is well-suited for pages with content sections that may need to be classified or tagged, like news articles, product descriptions, or reviews.

#### **2. Key Configuration Options**
   - **semantic_filter**: A keyword-based filter to focus on relevant content.
   - **word_count_threshold**: Minimum number of words per cluster, filtering out shorter, less meaningful clusters.
   - **max_dist**: Maximum allowable distance between elements in clusters, impacting cluster tightness.
   - **linkage_method**: Method for hierarchical clustering, such as `'ward'` (for well-separated clusters).
   - **top_k**: Specifies the number of top categories for each cluster.
   - **model_name**: Defines the model for embeddings, such as `sentence-transformers/all-MiniLM-L6-v2`.
   - **sim_threshold**: Minimum similarity threshold for filtering, allowing control over cluster relevance.

#### **3. How Cosine Similarity Clustering Works**
   - **Step 1**: Embeddings are generated for each text section, transforming them into vectors that capture semantic meaning.
   - **Step 2**: Hierarchical clustering groups similar sections based on cosine similarity, forming clusters with related content.
   - **Step 3**: Clusters are filtered based on word count, removing those below the `word_count_threshold`.
   - **Step 4**: Each cluster is then categorized with tags, if enabled, providing context to each grouped content section.

#### **4. Example Use Case: Clustering Blog Article Sections**
   - **Goal**: Group related sections of a blog or news page to identify distinct topics or discussion areas.
   - **Example HTML Sections**:
     ```text
     "The economy is showing signs of recovery, with markets up this quarter.",
     "In the sports world, several major teams are preparing for the upcoming season.",
     "New advancements in AI technology are reshaping the tech landscape.",
     "Market analysts are optimistic about continued growth in tech stocks."
     ```

   - **Code Setup**:
     ```python
     async def extract_blog_sections():
         extraction_strategy = CosineStrategy(
             word_count_threshold=15,
             max_dist=0.3,
             sim_threshold=0.2,
             model_name="sentence-transformers/all-MiniLM-L6-v2",
             top_k=2
         )
         async with AsyncWebCrawler() as crawler:
             url = "https://example.com/blog-page"
             result = await crawler.arun(
                 url=url,
                 extraction_strategy=extraction_strategy,
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - **word_count_threshold**: Ensures only clusters with meaningful content are included.
     - **sim_threshold**: Filters out clusters with low similarity, focusing on closely related sections.
     - **top_k**: Selects top tags, useful for identifying main topics.

#### **5. Applying Semantic Filtering with Cosine Similarity**
   - **Semantic Filter**: Filters sections based on relevance to a specific keyword, such as “technology” for tech articles.
   - **Example Code**:
     ```python
     extraction_strategy = CosineStrategy(
         semantic_filter="technology",
         word_count_threshold=10,
         max_dist=0.25,
         model_name="sentence-transformers/all-MiniLM-L6-v2"
     )
     ```
   - **Explanation**:
     - **semantic_filter**: Only sections with high similarity to the “technology” keyword will be included in the clustering, making it easy to focus on specific topics within a mixed-content page.

#### **6. Clustering Product Reviews by Similarity**
   - **Goal**: Organize product reviews by themes, such as “price,” “quality,” or “durability.”
   - **Example Reviews**:
     ```text
     "The quality of this product is outstanding and well worth the price.",
     "I found the product to be durable but a bit overpriced.",
     "Great value for the money and long-lasting.",
     "The build quality is good, but I expected a lower price point."
     ```

   - **Code Setup**:
     ```python
     async def extract_product_reviews():
         extraction_strategy = CosineStrategy(
             word_count_threshold=20,
             max_dist=0.35,
             sim_threshold=0.25,
             model_name="sentence-transformers/all-MiniLM-L6-v2"
         )
         async with AsyncWebCrawler() as crawler:
             url = "https://example.com/product-reviews"
             result = await crawler.arun(
                 url=url,
                 extraction_strategy=extraction_strategy,
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - This configuration clusters similar reviews, grouping feedback by common themes, helping businesses understand customer sentiments around particular product aspects.

#### **7. Performance Advantages of Cosine Strategy**
   - **Speed**: The Cosine Similarity Strategy is faster than LLM-based extraction, as it doesn’t rely on API calls to external LLMs.
   - **Local Processing**: The strategy runs locally with pre-trained sentence embeddings, ideal for high-throughput scenarios where cost and latency are concerns.
   - **Comparison**: With a well-optimized local model, this method can perform clustering on large datasets quickly, making it suitable for tasks requiring rapid, repeated analysis.

#### **8. Full Code Example for Clustering News Articles**
   - **Code**:
     ```python
     async def main():
         await extract_blog_sections()
         await extract_product_reviews()
     
     if __name__ == "__main__":
         asyncio.run(main())
     ```

#### **9. Wrap Up & Next Steps**
   - Recap the efficiency and effectiveness of Cosine Similarity for clustering related content quickly.
   - Close with a reminder of Crawl4AI’s flexibility across extraction strategies, and prompt users to experiment with different settings to optimize clustering for their specific content.

---

This outline covers Cosine Similarity Strategy’s speed and effectiveness, providing examples that showcase its potential for clustering various content types efficiently.