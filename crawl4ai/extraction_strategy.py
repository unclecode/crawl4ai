from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
import os

from .prompts import PROMPT_EXTRACT_BLOCKS, PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION, PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION, JSON_SCHEMA_BUILDER_XPATH
from .config import (
    DEFAULT_PROVIDER, PROVIDER_MODELS, 
    CHUNK_TOKEN_THRESHOLD,
    OVERLAP_RATE,
    WORD_TOKEN_RATE,
)
from .utils import *  # noqa: F403

from .utils import (
    sanitize_html,
    escape_json_string,
    perform_completion_with_backoff,
    extract_xml_data,
    split_and_parse_json_objects,
    sanitize_input_encode,
)
from .models import * # noqa: F403

from .models import TokenUsage

from .model_loader import * # noqa: F403
from .model_loader import (
    get_device,
    load_HF_embedding_model,
    load_text_multilabel_classifier,
    calculate_batch_size
)

from functools import partial
import math
import numpy as np
import re
from bs4 import BeautifulSoup
from lxml import html, etree


class ExtractionStrategy(ABC):
    """
    Abstract base class for all extraction strategies.
    """

    def __init__(self, input_format: str = "markdown", **kwargs):
        """
        Initialize the extraction strategy.

        Args:
            input_format: Content format to use for extraction.
                         Options: "markdown" (default), "html", "fit_markdown"
            **kwargs: Additional keyword arguments
        """
        self.input_format = input_format
        self.DEL = "<|DEL|>"
        self.name = self.__class__.__name__
        self.verbose = kwargs.get("verbose", False)

    @abstractmethod
    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract meaningful blocks or chunks from the given HTML.

        :param url: The URL of the webpage.
        :param html: The HTML content of the webpage.
        :return: A list of extracted blocks or chunks.
        """
        pass

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Process sections of text in parallel by default.

        :param url: The URL of the webpage.
        :param sections: List of sections (strings) to process.
        :return: A list of processed JSON blocks.
        """
        extracted_content = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.extract, url, section, **kwargs)
                for section in sections
            ]
            for future in as_completed(futures):
                extracted_content.extend(future.result())
        return extracted_content


class NoExtractionStrategy(ExtractionStrategy):
    """
    A strategy that does not extract any meaningful content from the HTML. It simply returns the entire HTML as a single block.
    """

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract meaningful blocks or chunks from the given HTML.
        """
        return [{"index": 0, "content": html}]

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        return [
            {"index": i, "tags": [], "content": section}
            for i, section in enumerate(sections)
        ]


#######################################################
# Strategies using clustering for text data extraction #
#######################################################


class CosineStrategy(ExtractionStrategy):
    """
    Extract meaningful blocks or chunks from the given HTML using cosine similarity.

    How it works:
    1. Pre-filter documents using embeddings and semantic_filter.
    2. Perform clustering using cosine similarity.
    3. Organize texts by their cluster labels, retaining order.
    4. Filter clusters by word count.
    5. Extract meaningful blocks or chunks from the filtered clusters.

    Attributes:
        semantic_filter (str): A keyword filter for document filtering.
        word_count_threshold (int): Minimum number of words per cluster.
        max_dist (float): The maximum cophenetic distance on the dendrogram to form clusters.
        linkage_method (str): The linkage method for hierarchical clustering.
        top_k (int): Number of top categories to extract.
        model_name (str): The name of the sentence-transformers model.
        sim_threshold (float): The similarity threshold for clustering.
    """

    def __init__(
        self,
        semantic_filter=None,
        word_count_threshold=10,
        max_dist=0.2,
        linkage_method="ward",
        top_k=3,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        sim_threshold=0.3,
        **kwargs,
    ):
        """
        Initialize the strategy with clustering parameters.

        Args:
            semantic_filter (str): A keyword filter for document filtering.
            word_count_threshold (int): Minimum number of words per cluster.
            max_dist (float): The maximum cophenetic distance on the dendrogram to form clusters.
            linkage_method (str): The linkage method for hierarchical clustering.
            top_k (int): Number of top categories to extract.
        """
        super().__init__(**kwargs)

        import numpy as np

        self.semantic_filter = semantic_filter
        self.word_count_threshold = word_count_threshold
        self.max_dist = max_dist
        self.linkage_method = linkage_method
        self.top_k = top_k
        self.sim_threshold = sim_threshold
        self.timer = time.time()
        self.verbose = kwargs.get("verbose", False)

        self.buffer_embeddings = np.array([])
        self.get_embedding_method = "direct"

        self.device = get_device()
        # import torch
        # self.device = torch.device('cpu')

        self.default_batch_size = calculate_batch_size(self.device)

        if self.verbose:
            print(f"[LOG] Loading Extraction Model for {self.device.type} device.")

        # if False and self.device.type == "cpu":
        #     self.model = load_onnx_all_MiniLM_l6_v2()
        #     self.tokenizer = self.model.tokenizer
        #     self.get_embedding_method = "direct"
        # else:

        self.tokenizer, self.model = load_HF_embedding_model(model_name)
        self.model.to(self.device)
        self.model.eval()

        self.get_embedding_method = "batch"

        self.buffer_embeddings = np.array([])

        # if model_name == "bert-base-uncased":
        #     self.tokenizer, self.model = load_bert_base_uncased()
        #     self.model.eval()  # Ensure the model is in evaluation mode
        #     self.get_embedding_method = "batch"
        # elif model_name == "BAAI/bge-small-en-v1.5":
        #     self.tokenizer, self.model = load_bge_small_en_v1_5()
        #     self.model.eval()  # Ensure the model is in evaluation mode
        #     self.get_embedding_method = "batch"
        # elif model_name == "sentence-transformers/all-MiniLM-L6-v2":
        #     self.model = load_onnx_all_MiniLM_l6_v2()
        #     self.tokenizer = self.model.tokenizer
        #     self.get_embedding_method = "direct"

        if self.verbose:
            print(f"[LOG] Loading Multilabel Classifier for {self.device.type} device.")

        self.nlp, _ = load_text_multilabel_classifier()
        # self.default_batch_size = 16 if self.device.type == 'cpu' else 64

        if self.verbose:
            print(
                f"[LOG] Model loaded {model_name}, models/reuters, took "
                + str(time.time() - self.timer)
                + " seconds"
            )

    def filter_documents_embeddings(
        self, documents: List[str], semantic_filter: str, at_least_k: int = 20
    ) -> List[str]:
        """
        Filter and sort documents based on the cosine similarity of their embeddings with the semantic_filter embedding.

        Args:
            documents (List[str]): A list of document texts.
            semantic_filter (str): A keyword filter for document filtering.
            at_least_k (int): The minimum number of documents to return.

        Returns:
            List[str]: A list of filtered and sorted document texts.
        """

        if not semantic_filter:
            return documents

        if len(documents) < at_least_k:
            at_least_k = len(documents) // 2

        from sklearn.metrics.pairwise import cosine_similarity

        # Compute embedding for the keyword filter
        query_embedding = self.get_embeddings([semantic_filter])[0]

        # Compute embeddings for the documents
        document_embeddings = self.get_embeddings(documents)

        # Calculate cosine similarity between the query embedding and document embeddings
        similarities = cosine_similarity(
            [query_embedding], document_embeddings
        ).flatten()

        # Filter documents based on the similarity threshold
        filtered_docs = [
            (doc, sim)
            for doc, sim in zip(documents, similarities)
            if sim >= self.sim_threshold
        ]

        # If the number of filtered documents is less than at_least_k, sort remaining documents by similarity
        if len(filtered_docs) < at_least_k:
            remaining_docs = [
                (doc, sim)
                for doc, sim in zip(documents, similarities)
                if sim < self.sim_threshold
            ]
            remaining_docs.sort(key=lambda x: x[1], reverse=True)
            filtered_docs.extend(remaining_docs[: at_least_k - len(filtered_docs)])

        # Extract the document texts from the tuples
        filtered_docs = [doc for doc, _ in filtered_docs]

        return filtered_docs[:at_least_k]

    def get_embeddings(
        self, sentences: List[str], batch_size=None, bypass_buffer=False
    ):
        """
        Get BERT embeddings for a list of sentences.

        Args:
            sentences (List[str]): A list of text chunks (sentences).

        Returns:
            NumPy array of embeddings.
        """
        # if self.buffer_embeddings.any() and not bypass_buffer:
        #     return self.buffer_embeddings

        if self.device.type in ["cpu", "gpu", "cuda", "mps"]:
            import torch

            # Tokenize sentences and convert to tensor
            if batch_size is None:
                batch_size = self.default_batch_size

            all_embeddings = []
            for i in range(0, len(sentences), batch_size):
                batch_sentences = sentences[i : i + batch_size]
                encoded_input = self.tokenizer(
                    batch_sentences, padding=True, truncation=True, return_tensors="pt"
                )
                encoded_input = {
                    key: tensor.to(self.device) for key, tensor in encoded_input.items()
                }

                # Ensure no gradients are calculated
                with torch.no_grad():
                    model_output = self.model(**encoded_input)

                # Get embeddings from the last hidden state (mean pooling)
                embeddings = model_output.last_hidden_state.mean(dim=1).cpu().numpy()
                all_embeddings.append(embeddings)

            self.buffer_embeddings = np.vstack(all_embeddings)
        elif self.device.type == "cpu":
            # self.buffer_embeddings = self.model(sentences)
            if batch_size is None:
                batch_size = self.default_batch_size

            all_embeddings = []
            for i in range(0, len(sentences), batch_size):
                batch_sentences = sentences[i : i + batch_size]
                embeddings = self.model(batch_sentences)
                all_embeddings.append(embeddings)

            self.buffer_embeddings = np.vstack(all_embeddings)
        return self.buffer_embeddings

    def hierarchical_clustering(self, sentences: List[str], embeddings=None):
        """
        Perform hierarchical clustering on sentences and return cluster labels.

        Args:
            sentences (List[str]): A list of text chunks (sentences).

        Returns:
            NumPy array of cluster labels.
        """
        # Get embeddings
        from scipy.cluster.hierarchy import linkage, fcluster
        from scipy.spatial.distance import pdist

        self.timer = time.time()
        embeddings = self.get_embeddings(sentences, bypass_buffer=True)
        # print(f"[LOG] 🚀 Embeddings computed in {time.time() - self.timer:.2f} seconds")
        # Compute pairwise cosine distances
        distance_matrix = pdist(embeddings, "cosine")
        # Perform agglomerative clustering respecting order
        linked = linkage(distance_matrix, method=self.linkage_method)
        # Form flat clusters
        labels = fcluster(linked, self.max_dist, criterion="distance")
        return labels

    def filter_clusters_by_word_count(
        self, clusters: Dict[int, List[str]]
    ) -> Dict[int, List[str]]:
        """
        Filter clusters to remove those with a word count below the threshold.

        Args:
            clusters (Dict[int, List[str]]): Dictionary of clusters.

        Returns:
            Dict[int, List[str]]: Filtered dictionary of clusters.
        """
        filtered_clusters = {}
        for cluster_id, texts in clusters.items():
            # Concatenate texts for analysis
            full_text = " ".join(texts)
            # Count words
            word_count = len(full_text.split())

            # Keep clusters with word count above the threshold
            if word_count >= self.word_count_threshold:
                filtered_clusters[cluster_id] = texts

        return filtered_clusters

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract clusters from HTML content using hierarchical clustering.

        Args:
            url (str): The URL of the webpage.
            html (str): The HTML content of the webpage.

        Returns:
            List[Dict[str, Any]]: A list of processed JSON blocks.
        """
        # Assume `html` is a list of text chunks for this strategy
        t = time.time()
        text_chunks = html.split(self.DEL)  # Split by lines or paragraphs as needed

        # Pre-filter documents using embeddings and semantic_filter
        text_chunks = self.filter_documents_embeddings(
            text_chunks, self.semantic_filter
        )

        if not text_chunks:
            return []

        # Perform clustering
        labels = self.hierarchical_clustering(text_chunks)
        # print(f"[LOG] 🚀 Clustering done in {time.time() - t:.2f} seconds")

        # Organize texts by their cluster labels, retaining order
        t = time.time()
        clusters = {}
        for index, label in enumerate(labels):
            clusters.setdefault(label, []).append(text_chunks[index])

        # Filter clusters by word count
        filtered_clusters = self.filter_clusters_by_word_count(clusters)

        # Convert filtered clusters to a sorted list of dictionaries
        cluster_list = [
            {"index": int(idx), "tags": [], "content": " ".join(filtered_clusters[idx])}
            for idx in sorted(filtered_clusters)
        ]

        if self.verbose:
            print(f"[LOG] 🚀 Assign tags using {self.device}")

        if self.device.type in ["gpu", "cuda", "mps", "cpu"]:
            labels = self.nlp([cluster["content"] for cluster in cluster_list])

            for cluster, label in zip(cluster_list, labels):
                cluster["tags"] = label
        # elif self.device.type == "cpu":
        #     # Process the text with the loaded model
        #     texts = [cluster['content'] for cluster in cluster_list]
        #     # Batch process texts
        #     docs = self.nlp.pipe(texts, disable=["tagger", "parser", "ner", "lemmatizer"])

        #     for doc, cluster in zip(docs, cluster_list):
        #         tok_k = self.top_k
        #         top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
        #         cluster['tags'] = [cat for cat, _ in top_categories]

        # for cluster in  cluster_list:
        #     doc = self.nlp(cluster['content'])
        #     tok_k = self.top_k
        #     top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
        #     cluster['tags'] = [cat for cat, _ in top_categories]

        if self.verbose:
            print(f"[LOG] 🚀 Categorization done in {time.time() - t:.2f} seconds")

        return cluster_list

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Process sections using hierarchical clustering.

        Args:
            url (str): The URL of the webpage.
            sections (List[str]): List of sections (strings) to process.

        Returns:
        """
        # This strategy processes all sections together

        return self.extract(url, self.DEL.join(sections), **kwargs)


#######################################################
# Strategies using LLM-based extraction for text data #
#######################################################
class LLMExtractionStrategy(ExtractionStrategy):
    """
    A strategy that uses an LLM to extract meaningful content from the HTML.

    Attributes:
        provider: The provider to use for extraction. It follows the format <provider_name>/<model_name>, e.g., "ollama/llama3.3".
        api_token: The API token for the provider.
        instruction: The instruction to use for the LLM model.
        schema: Pydantic model schema for structured data.
        extraction_type: "block" or "schema".
        chunk_token_threshold: Maximum tokens per chunk.
        overlap_rate: Overlap between chunks.
        word_token_rate: Word to token conversion rate.
        apply_chunking: Whether to apply chunking.
        base_url: The base URL for the API request.
        api_base: The base URL for the API request.
        extra_args: Additional arguments for the API request, such as temprature, max_tokens, etc.
        verbose: Whether to print verbose output.
        usages: List of individual token usages.
        total_usage: Accumulated token usage.
    """

    def __init__(
        self,
        provider: str = DEFAULT_PROVIDER,
        api_token: Optional[str] = None,
        instruction: str = None,
        schema: Dict = None,
        extraction_type="block",
        **kwargs,
    ):
        """
        Initialize the strategy with clustering parameters.

        Args:
            provider: The provider to use for extraction. It follows the format <provider_name>/<model_name>, e.g., "ollama/llama3.3".
            api_token: The API token for the provider.
            instruction: The instruction to use for the LLM model.
            schema: Pydantic model schema for structured data.
            extraction_type: "block" or "schema".
            chunk_token_threshold: Maximum tokens per chunk.
            overlap_rate: Overlap between chunks.
            word_token_rate: Word to token conversion rate.
            apply_chunking: Whether to apply chunking.
            base_url: The base URL for the API request.
            api_base: The base URL for the API request.
            extra_args: Additional arguments for the API request, such as temprature, max_tokens, etc.
            verbose: Whether to print verbose output.
            usages: List of individual token usages.
            total_usage: Accumulated token usage.

        """
        super().__init__(**kwargs)
        self.provider = provider
        self.api_token = (
            api_token
            or PROVIDER_MODELS.get(provider, "no-token")
            or os.getenv("OPENAI_API_KEY")
        )
        self.instruction = instruction
        self.extract_type = extraction_type
        self.schema = schema
        if schema:
            self.extract_type = "schema"

        self.chunk_token_threshold = kwargs.get(
            "chunk_token_threshold", CHUNK_TOKEN_THRESHOLD
        )
        self.overlap_rate = kwargs.get("overlap_rate", OVERLAP_RATE)
        self.word_token_rate = kwargs.get("word_token_rate", WORD_TOKEN_RATE)
        self.apply_chunking = kwargs.get("apply_chunking", True)
        self.base_url = kwargs.get("base_url", None)
        self.api_base = kwargs.get("api_base", kwargs.get("base_url", None))
        self.extra_args = kwargs.get("extra_args", {})
        if not self.apply_chunking:
            self.chunk_token_threshold = 1e9

        self.verbose = kwargs.get("verbose", False)
        self.usages = []  # Store individual usages
        self.total_usage = TokenUsage()  # Accumulated usage

        if not self.api_token:
            raise ValueError(
                "API token must be provided for LLMExtractionStrategy. Update the config.py or set OPENAI_API_KEY environment variable."
            )

    def extract(self, url: str, ix: int, html: str) -> List[Dict[str, Any]]:
        """
        Extract meaningful blocks or chunks from the given HTML using an LLM.

        How it works:
        1. Construct a prompt with variables.
        2. Make a request to the LLM using the prompt.
        3. Parse the response and extract blocks or chunks.

        Args:
            url: The URL of the webpage.
            ix: Index of the block.
            html: The HTML content of the webpage.

        Returns:
            A list of extracted blocks or chunks.
        """
        if self.verbose:
            # print("[LOG] Extracting blocks from URL:", url)
            print(f"[LOG] Call LLM for {url} - block index: {ix}")

        variable_values = {
            "URL": url,
            "HTML": escape_json_string(sanitize_html(html)),
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        if self.instruction:
            variable_values["REQUEST"] = self.instruction
            prompt_with_variables = PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION

        if self.extract_type == "schema" and self.schema:
            variable_values["SCHEMA"] = json.dumps(self.schema, indent=2)
            prompt_with_variables = PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION

        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )

        response = perform_completion_with_backoff(
            self.provider,
            prompt_with_variables,
            self.api_token,
            base_url=self.api_base or self.base_url,
            extra_args=self.extra_args,
        )  # , json_response=self.extract_type == "schema")
        # Track usage
        usage = TokenUsage(
            completion_tokens=response.usage.completion_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens,
            completion_tokens_details=response.usage.completion_tokens_details.__dict__
            if response.usage.completion_tokens_details
            else {},
            prompt_tokens_details=response.usage.prompt_tokens_details.__dict__
            if response.usage.prompt_tokens_details
            else {},
        )
        self.usages.append(usage)

        # Update totals
        self.total_usage.completion_tokens += usage.completion_tokens
        self.total_usage.prompt_tokens += usage.prompt_tokens
        self.total_usage.total_tokens += usage.total_tokens

        try:
            blocks = extract_xml_data(["blocks"], response.choices[0].message.content)[
                "blocks"
            ]
            blocks = json.loads(blocks)
            for block in blocks:
                block["error"] = False
        except Exception:
            parsed, unparsed = split_and_parse_json_objects(
                response.choices[0].message.content
            )
            blocks = parsed
            if unparsed:
                blocks.append(
                    {"index": 0, "error": True, "tags": ["error"], "content": unparsed}
                )

        if self.verbose:
            print(
                "[LOG] Extracted",
                len(blocks),
                "blocks from URL:",
                url,
                "block index:",
                ix,
            )
        return blocks

    def _merge(self, documents, chunk_token_threshold, overlap):
        """
        Merge documents into sections based on chunk_token_threshold and overlap.
        """
        # chunks = []
        sections = []
        total_tokens = 0

        # Calculate the total tokens across all documents
        for document in documents:
            total_tokens += len(document.split(" ")) * self.word_token_rate

        # Calculate the number of sections needed
        num_sections = math.floor(total_tokens / chunk_token_threshold)
        if num_sections < 1:
            num_sections = 1  # Ensure there is at least one section
        adjusted_chunk_threshold = total_tokens / num_sections

        total_token_so_far = 0
        current_chunk = []

        for document in documents:
            tokens = document.split(" ")
            token_count = len(tokens) * self.word_token_rate

            if total_token_so_far + token_count <= adjusted_chunk_threshold:
                current_chunk.extend(tokens)
                total_token_so_far += token_count
            else:
                # Ensure to handle the last section properly
                if len(sections) == num_sections - 1:
                    current_chunk.extend(tokens)
                    continue

                # Add overlap if specified
                if overlap > 0 and current_chunk:
                    overlap_tokens = current_chunk[-overlap:]
                    current_chunk.extend(overlap_tokens)

                sections.append(" ".join(current_chunk))
                current_chunk = tokens
                total_token_so_far = token_count

        # Add the last chunk
        if current_chunk:
            sections.append(" ".join(current_chunk))

        return sections

    def run(self, url: str, sections: List[str]) -> List[Dict[str, Any]]:
        """
        Process sections sequentially with a delay for rate limiting issues, specifically for LLMExtractionStrategy.

        Args:
            url: The URL of the webpage.
            sections: List of sections (strings) to process.

        Returns:
            A list of extracted blocks or chunks.
        """

        merged_sections = self._merge(
            sections,
            self.chunk_token_threshold,
            overlap=int(self.chunk_token_threshold * self.overlap_rate),
        )
        extracted_content = []
        if self.provider.startswith("groq/"):
            # Sequential processing with a delay
            for ix, section in enumerate(merged_sections):
                extract_func = partial(self.extract, url)
                extracted_content.extend(
                    extract_func(ix, sanitize_input_encode(section))
                )
                time.sleep(0.5)  # 500 ms delay between each processing
        else:
            # Parallel processing using ThreadPoolExecutor
            # extract_func = partial(self.extract, url)
            # for ix, section in enumerate(merged_sections):
            #     extracted_content.append(extract_func(ix, section))

            with ThreadPoolExecutor(max_workers=4) as executor:
                extract_func = partial(self.extract, url)
                futures = [
                    executor.submit(extract_func, ix, sanitize_input_encode(section))
                    for ix, section in enumerate(merged_sections)
                ]

                for future in as_completed(futures):
                    try:
                        extracted_content.extend(future.result())
                    except Exception as e:
                        if self.verbose:
                            print(f"Error in thread execution: {e}")
                        # Add error information to extracted_content
                        extracted_content.append(
                            {
                                "index": 0,
                                "error": True,
                                "tags": ["error"],
                                "content": str(e),
                            }
                        )

        return extracted_content

    def show_usage(self) -> None:
        """Print a detailed token usage report showing total and per-request usage."""
        print("\n=== Token Usage Summary ===")
        print(f"{'Type':<15} {'Count':>12}")
        print("-" * 30)
        print(f"{'Completion':<15} {self.total_usage.completion_tokens:>12,}")
        print(f"{'Prompt':<15} {self.total_usage.prompt_tokens:>12,}")
        print(f"{'Total':<15} {self.total_usage.total_tokens:>12,}")

        print("\n=== Usage History ===")
        print(f"{'Request #':<10} {'Completion':>12} {'Prompt':>12} {'Total':>12}")
        print("-" * 48)
        for i, usage in enumerate(self.usages, 1):
            print(
                f"{i:<10} {usage.completion_tokens:>12,} {usage.prompt_tokens:>12,} {usage.total_tokens:>12,}"
            )


#######################################################
# New extraction strategies for JSON-based extraction #
#######################################################


class JsonElementExtractionStrategy(ExtractionStrategy):
    """
    Abstract base class for extracting structured JSON from HTML content.

    How it works:
    1. Parses HTML content using the `_parse_html` method.
    2. Uses a schema to define base selectors, fields, and transformations.
    3. Extracts data hierarchically, supporting nested fields and lists.
    4. Handles computed fields with expressions or functions.

    Attributes:
        DEL (str): Delimiter used to combine HTML sections. Defaults to '\n'.
        schema (Dict[str, Any]): The schema defining the extraction rules.
        verbose (bool): Enables verbose logging for debugging purposes.

    Methods:
        extract(url, html_content, *q, **kwargs): Extracts structured data from HTML content.
        _extract_item(element, fields): Extracts fields from a single element.
        _extract_single_field(element, field): Extracts a single field based on its type.
        _apply_transform(value, transform): Applies a transformation to a value.
        _compute_field(item, field): Computes a field value using an expression or function.
        run(url, sections, *q, **kwargs): Combines HTML sections and runs the extraction strategy.

    Abstract Methods:
        _parse_html(html_content): Parses raw HTML into a structured format (e.g., BeautifulSoup or lxml).
        _get_base_elements(parsed_html, selector): Retrieves base elements using a selector.
        _get_elements(element, selector): Retrieves child elements using a selector.
        _get_element_text(element): Extracts text content from an element.
        _get_element_html(element): Extracts raw HTML from an element.
        _get_element_attribute(element, attribute): Extracts an attribute's value from an element.
    """

    DEL = "\n"

    def __init__(self, schema: Dict[str, Any], **kwargs):
        """
        Initialize the JSON element extraction strategy with a schema.

        Args:
            schema (Dict[str, Any]): The schema defining the extraction rules.
        """
        super().__init__(**kwargs)
        self.schema = schema
        self.verbose = kwargs.get("verbose", False)

    def extract(
        self, url: str, html_content: str, *q, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract structured data from HTML content.

        How it works:
        1. Parses the HTML content using the `_parse_html` method.
        2. Identifies base elements using the schema's base selector.
        3. Extracts fields from each base element using `_extract_item`.

        Args:
            url (str): The URL of the page being processed.
            html_content (str): The raw HTML content to parse and extract.
            *q: Additional positional arguments.
            **kwargs: Additional keyword arguments for custom extraction.

        Returns:
            List[Dict[str, Any]]: A list of extracted items, each represented as a dictionary.
        """

        parsed_html = self._parse_html(html_content)
        base_elements = self._get_base_elements(
            parsed_html, self.schema["baseSelector"]
        )

        results = []
        for element in base_elements:
            # Extract base element attributes
            item = {}
            if "baseFields" in self.schema:
                for field in self.schema["baseFields"]:
                    value = self._extract_single_field(element, field)
                    if value is not None:
                        item[field["name"]] = value

            # Extract child fields
            field_data = self._extract_item(element, self.schema["fields"])
            item.update(field_data)

            if item:
                results.append(item)

        return results

    @abstractmethod
    def _parse_html(self, html_content: str):
        """Parse HTML content into appropriate format"""
        pass

    @abstractmethod
    def _get_base_elements(self, parsed_html, selector: str):
        """Get all base elements using the selector"""
        pass

    @abstractmethod
    def _get_elements(self, element, selector: str):
        """Get child elements using the selector"""
        pass

    def _extract_field(self, element, field):
        try:
            if field["type"] == "nested":
                nested_elements = self._get_elements(element, field["selector"])
                nested_element = nested_elements[0] if nested_elements else None
                return (
                    self._extract_item(nested_element, field["fields"])
                    if nested_element
                    else {}
                )

            if field["type"] == "list":
                elements = self._get_elements(element, field["selector"])
                return [self._extract_list_item(el, field["fields"]) for el in elements]

            if field["type"] == "nested_list":
                elements = self._get_elements(element, field["selector"])
                return [self._extract_item(el, field["fields"]) for el in elements]

            return self._extract_single_field(element, field)
        except Exception as e:
            if self.verbose:
                print(f"Error extracting field {field['name']}: {str(e)}")
            return field.get("default")

    def _extract_single_field(self, element, field):
        """
        Extract a single field based on its type.

        How it works:
        1. Selects the target element using the field's selector.
        2. Extracts the field value based on its type (e.g., text, attribute, regex).
        3. Applies transformations if defined in the schema.

        Args:
            element: The base element to extract the field from.
            field (Dict[str, Any]): The field definition in the schema.

        Returns:
            Any: The extracted field value.
        """

        if "selector" in field:
            selected = self._get_elements(element, field["selector"])
            if not selected:
                return field.get("default")
            selected = selected[0]
        else:
            selected = element

        value = None
        if field["type"] == "text":
            value = self._get_element_text(selected)
        elif field["type"] == "attribute":
            value = self._get_element_attribute(selected, field["attribute"])
        elif field["type"] == "html":
            value = self._get_element_html(selected)
        elif field["type"] == "regex":
            text = self._get_element_text(selected)
            match = re.search(field["pattern"], text)
            value = match.group(1) if match else None

        if "transform" in field:
            value = self._apply_transform(value, field["transform"])

        return value if value is not None else field.get("default")

    def _extract_list_item(self, element, fields):
        item = {}
        for field in fields:
            value = self._extract_single_field(element, field)
            if value is not None:
                item[field["name"]] = value
        return item

    def _extract_item(self, element, fields):
        """
        Extracts fields from a given element.

        How it works:
        1. Iterates through the fields defined in the schema.
        2. Handles computed, single, and nested field types.
        3. Updates the item dictionary with extracted field values.

        Args:
            element: The base element to extract fields from.
            fields (List[Dict[str, Any]]): The list of fields to extract.

        Returns:
            Dict[str, Any]: A dictionary representing the extracted item.
        """

        item = {}
        for field in fields:
            if field["type"] == "computed":
                value = self._compute_field(item, field)
            else:
                value = self._extract_field(element, field)
            if value is not None:
                item[field["name"]] = value
        return item

    def _apply_transform(self, value, transform):
        """
        Apply a transformation to a value.

        How it works:
        1. Checks the transformation type (e.g., `lowercase`, `strip`).
        2. Applies the transformation to the value.
        3. Returns the transformed value.

        Args:
            value (str): The value to transform.
            transform (str): The type of transformation to apply.

        Returns:
            str: The transformed value.
        """

        if transform == "lowercase":
            return value.lower()
        elif transform == "uppercase":
            return value.upper()
        elif transform == "strip":
            return value.strip()
        return value

    def _compute_field(self, item, field):
        try:
            if "expression" in field:
                return eval(field["expression"], {}, item)
            elif "function" in field:
                return field["function"](item)
        except Exception as e:
            if self.verbose:
                print(f"Error computing field {field['name']}: {str(e)}")
            return field.get("default")

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Run the extraction strategy on a combined HTML content.

        How it works:
        1. Combines multiple HTML sections using the `DEL` delimiter.
        2. Calls the `extract` method with the combined HTML.

        Args:
            url (str): The URL of the page being processed.
            sections (List[str]): A list of HTML sections.
            *q: Additional positional arguments.
            **kwargs: Additional keyword arguments for custom extraction.

        Returns:
            List[Dict[str, Any]]: A list of extracted items.
        """

        combined_html = self.DEL.join(sections)
        return self.extract(url, combined_html, **kwargs)

    @abstractmethod
    def _get_element_text(self, element) -> str:
        """Get text content from element"""
        pass

    @abstractmethod
    def _get_element_html(self, element) -> str:
        """Get HTML content from element"""
        pass

    @abstractmethod
    def _get_element_attribute(self, element, attribute: str):
        """Get attribute value from element"""
        pass

    @staticmethod
    def generate_schema(
        html: str,
        schema_type: str = "CSS", # or XPATH
        query: str = None,
        provider: str = "gpt-4o",
        api_token: str = os.getenv("OPENAI_API_KEY"),
        **kwargs
    ) -> dict:
        """
        Generate extraction schema from HTML content and optional query.
        
        Args:
            html (str): The HTML content to analyze
            query (str, optional): Natural language description of what data to extract
            provider (str): LLM provider to use 
            api_token (str): API token for LLM provider
            prompt (str, optional): Custom prompt template to use
            **kwargs: Additional args passed to perform_completion_with_backoff
            
        Returns:
            dict: Generated schema following the JsonElementExtractionStrategy format
        """
        from .prompts import JSON_SCHEMA_BUILDER
        from .utils import perform_completion_with_backoff
        
        # Use default or custom prompt
        prompt_template = JSON_SCHEMA_BUILDER if schema_type == "CSS" else JSON_SCHEMA_BUILDER_XPATH
        
        # Build the prompt
        system_message = {
            "role": "system", 
            "content": "You are a specialized HTML schema generator. Analyze the HTML and generate a JSON schema that follows the specified format. Only output valid JSON schema, nothing else."
        }
        
        user_message = {
            "role": "user",
            "content": f"""
                Instructions:
                {prompt_template}

                HTML to analyze:
                ```html
                {html}
                ```

                {"Extract the following data: " + query if query else "Please analyze the HTML structure and create the most appropriate schema for data extraction."}
                """
        }

        try:
            # Call LLM with backoff handling
            response = perform_completion_with_backoff(
                provider=provider,
                prompt_with_variables="\n\n".join([system_message["content"], user_message["content"]]),
                json_response = True,                
                api_token=api_token,
                **kwargs
            )
            
            # Extract and return schema
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            raise Exception(f"Failed to generate schema: {str(e)}")


class JsonCssExtractionStrategy(JsonElementExtractionStrategy):
    """
    Concrete implementation of `JsonElementExtractionStrategy` using CSS selectors.

    How it works:
    1. Parses HTML content with BeautifulSoup.
    2. Selects elements using CSS selectors defined in the schema.
    3. Extracts field data and applies transformations as defined.

    Attributes:
        schema (Dict[str, Any]): The schema defining the extraction rules.
        verbose (bool): Enables verbose logging for debugging purposes.

    Methods:
        _parse_html(html_content): Parses HTML content into a BeautifulSoup object.
        _get_base_elements(parsed_html, selector): Selects base elements using a CSS selector.
        _get_elements(element, selector): Selects child elements using a CSS selector.
        _get_element_text(element): Extracts text content from a BeautifulSoup element.
        _get_element_html(element): Extracts the raw HTML content of a BeautifulSoup element.
        _get_element_attribute(element, attribute): Retrieves an attribute value from a BeautifulSoup element.
    """

    def __init__(self, schema: Dict[str, Any], **kwargs):
        kwargs["input_format"] = "html"  # Force HTML input
        super().__init__(schema, **kwargs)

    def _parse_html(self, html_content: str):
        return BeautifulSoup(html_content, "html.parser")

    def _get_base_elements(self, parsed_html, selector: str):
        return parsed_html.select(selector)

    def _get_elements(self, element, selector: str):
        # Return all matching elements using select() instead of select_one()
        # This ensures that we get all elements that match the selector, not just the first one
        return element.select(selector)

    def _get_element_text(self, element) -> str:
        return element.get_text(strip=True)

    def _get_element_html(self, element) -> str:
        return str(element)

    def _get_element_attribute(self, element, attribute: str):
        return element.get(attribute)


class JsonXPathExtractionStrategy(JsonElementExtractionStrategy):
    """
    Concrete implementation of `JsonElementExtractionStrategy` using XPath selectors.

    How it works:
    1. Parses HTML content into an lxml tree.
    2. Selects elements using XPath expressions.
    3. Converts CSS selectors to XPath when needed.

    Attributes:
        schema (Dict[str, Any]): The schema defining the extraction rules.
        verbose (bool): Enables verbose logging for debugging purposes.

    Methods:
        _parse_html(html_content): Parses HTML content into an lxml tree.
        _get_base_elements(parsed_html, selector): Selects base elements using an XPath selector.
        _css_to_xpath(css_selector): Converts a CSS selector to an XPath expression.
        _get_elements(element, selector): Selects child elements using an XPath selector.
        _get_element_text(element): Extracts text content from an lxml element.
        _get_element_html(element): Extracts the raw HTML content of an lxml element.
        _get_element_attribute(element, attribute): Retrieves an attribute value from an lxml element.
    """

    def __init__(self, schema: Dict[str, Any], **kwargs):
        kwargs["input_format"] = "html"  # Force HTML input
        super().__init__(schema, **kwargs)

    def _parse_html(self, html_content: str):
        return html.fromstring(html_content)

    def _get_base_elements(self, parsed_html, selector: str):
        return parsed_html.xpath(selector)

    def _css_to_xpath(self, css_selector: str) -> str:
        """Convert CSS selector to XPath if needed"""
        if "/" in css_selector:  # Already an XPath
            return css_selector
        return self._basic_css_to_xpath(css_selector)

    def _basic_css_to_xpath(self, css_selector: str) -> str:
        """Basic CSS to XPath conversion for common cases"""
        if " > " in css_selector:
            parts = css_selector.split(" > ")
            return "//" + "/".join(parts)
        if " " in css_selector:
            parts = css_selector.split(" ")
            return "//" + "//".join(parts)
        return "//" + css_selector

    def _get_elements(self, element, selector: str):
        xpath = self._css_to_xpath(selector)
        if not xpath.startswith("."):
            xpath = "." + xpath
        return element.xpath(xpath)

    def _get_element_text(self, element) -> str:
        return "".join(element.xpath(".//text()")).strip()

    def _get_element_html(self, element) -> str:
        return etree.tostring(element, encoding="unicode")

    def _get_element_attribute(self, element, attribute: str):
        return element.get(attribute)

