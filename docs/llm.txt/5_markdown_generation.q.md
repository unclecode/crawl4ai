markdown_generation: Converts web content into clean, structured Markdown format for AI processing | html to markdown, text conversion, content extraction | DefaultMarkdownGenerator()
markdown_config_options: Configure HTML to Markdown conversion with html2text options like ignore_links, escape_html, body_width | markdown settings, conversion options | html2text_config={"ignore_links": True, "body_width": 80}
content_filtering: Filter and clean web content using BM25 or Pruning strategies | content cleanup, noise removal | content_filter=BM25ContentFilter()
bm25_filtering: Score and filter content based on relevance to a user query | relevance filtering, query matching | BM25ContentFilter(user_query="ai", bm25_threshold=1.5)
pruning_filter: Remove boilerplate and noise using unsupervised clustering approach | content pruning, noise removal | PruningContentFilter(threshold=0.7, threshold_type="dynamic")
markdown_result_types: Access different markdown outputs including raw, cited, and filtered versions | markdown formats, output types | result.markdown_v2.{raw_markdown, markdown_with_citations, fit_markdown}
link_citations: Convert webpage links into citation-style references at document end | reference handling, link management | markdown_with_citations output format
content_scoring: Evaluate content blocks based on text density, link density, and tag importance | content metrics, scoring system | PruningContentFilter metrics
combined_filtering: Apply both pruning and BM25 filters for optimal content extraction | filter pipeline, multi-stage filtering | PruningContentFilter() followed by BM25ContentFilter()
markdown_generation_troubleshooting: Debug empty outputs and malformed content issues | error handling, debugging | Check HTML content and filter thresholds
performance_optimization: Cache results and adjust parameters for better processing speed | optimization, caching | Store intermediate results for reuse
rag_pipeline_integration: Use filtered markdown for retrieval-augmented generation systems | RAG, vector storage | Store fit_markdown in vector database
code_block_handling: Preserve and format code snippets in markdown output | code formatting, syntax | handle_code_in_pre=True option
authentication_handling: Process content from authenticated pages using session tokens | auth support, protected content | Provide session tokens before markdown generation
docker_deployment: Run markdown generation in containerized environment | deployment, containers | Include in Dockerfile configuration