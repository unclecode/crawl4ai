# Crawl4AI

## Episode 8: Media Handling: Images, Videos, and Audio

### Quick Intro
Showcase Crawl4AI’s media extraction capabilities, including lazy-loaded media and metadata. Demo: Crawl a multimedia page, extract images, and show metadata (alt text, context, relevance score).

Here’s a clear and focused outline for the **Media Handling: Images, Videos, and Audio** video:

---

### **Media Handling: Images, Videos, and Audio**

1) **Overview of Media Extraction in Crawl4AI**:

   - Crawl4AI can detect and extract different types of media (images, videos, and audio) along with useful metadata.
   - This functionality is essential for gathering visual content from multimedia-heavy pages like e-commerce sites, news articles, and social media feeds.

2) **Image Extraction and Metadata**:

   - Crawl4AI captures images with detailed metadata, including:
     - **Source URL**: The direct URL to the image.
     - **Alt Text**: Image description if available.
     - **Relevance Score**: A score (0–10) indicating how relevant the image is to the main content.
     - **Context**: Text surrounding the image on the page.
   - **Example**:
     ```python
     result = await crawler.arun(url="https://example.com")
     
     for image in result.media["images"]:
         print(f"Source: {image['src']}")
         print(f"Alt Text: {image['alt']}")
         print(f"Relevance Score: {image['score']}")
         print(f"Context: {image['context']}")
     ```
   - This example shows how to access each image’s metadata, making it easy to filter for the most relevant visuals.

3) **Handling Lazy-Loaded Images**:

   - Crawl4AI automatically supports lazy-loaded images, which are commonly used to optimize webpage loading.
   - **Example with Wait for Lazy-Loaded Content**:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         wait_for="css:img[data-src]",  # Wait for lazy-loaded images
         delay_before_return_html=2.0   # Allow extra time for images to load
     )
     ```
   - This setup waits for lazy-loaded images to appear, ensuring they are fully captured.

4) **Video Extraction and Metadata**:

   - Crawl4AI captures video elements, including:
     - **Source URL**: The video’s direct URL.
     - **Type**: Format of the video (e.g., MP4).
     - **Thumbnail**: A poster or thumbnail image if available.
     - **Duration**: Video length, if metadata is provided.
   - **Example**:
     ```python
     for video in result.media["videos"]:
         print(f"Video Source: {video['src']}")
         print(f"Type: {video['type']}")
         print(f"Thumbnail: {video.get('poster')}")
         print(f"Duration: {video.get('duration')}")
     ```
   - This allows users to gather video content and relevant details for further processing or analysis.

5) **Audio Extraction and Metadata**:

   - Audio elements can also be extracted, with metadata like:
     - **Source URL**: The audio file’s direct URL.
     - **Type**: Format of the audio file (e.g., MP3).
     - **Duration**: Length of the audio, if available.
   - **Example**:
     ```python
     for audio in result.media["audios"]:
         print(f"Audio Source: {audio['src']}")
         print(f"Type: {audio['type']}")
         print(f"Duration: {audio.get('duration')}")
     ```
   - Useful for sites with podcasts, sound bites, or other audio content.

6) **Filtering Media by Relevance**:

   - Use metadata like relevance score to filter only the most useful media content:
     ```python
     relevant_images = [img for img in result.media["images"] if img['score'] > 5]
     ```
   - This is especially helpful for content-heavy pages where you only want media directly related to the main content.

7) **Example: Full Media Extraction with Content Filtering**:

   - Full example extracting images, videos, and audio along with filtering by relevance:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com",
             word_count_threshold=10,  # Filter content blocks for relevance
             exclude_external_images=True  # Only keep internal images
         )
         
         # Display media summaries
         print(f"Relevant Images: {len(relevant_images)}")
         print(f"Videos: {len(result.media['videos'])}")
         print(f"Audio Clips: {len(result.media['audios'])}")
     ```
   - This example shows how to capture and filter various media types, focusing on what’s most relevant.

8) **Wrap Up & Next Steps**:

   - Recap the comprehensive media extraction capabilities, emphasizing how metadata helps users focus on relevant content.
   - Tease the next video: **Link Analysis and Smart Filtering** to explore how Crawl4AI handles internal, external, and social media links for more focused data gathering.

---

This outline provides users with a complete guide to handling images, videos, and audio in Crawl4AI, using metadata to enhance relevance and precision in multimedia extraction.