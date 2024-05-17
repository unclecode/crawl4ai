from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, time
# from optimum.intel import IPEXModel
from .prompts import PROMPT_EXTRACT_BLOCKS, PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION
from .config import *
from .utils import *
from functools import partial
from .model_loader import *


import numpy as np
class ExtractionStrategy(ABC):
    """
    Abstract base class for all extraction strategies.
    """
    
    def __init__(self, **kwargs):
        self.DEL = "<|DEL|>"
        self.name = self.__class__.__name__

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
            futures = [executor.submit(self.extract, url, section, **kwargs) for section in sections]
            for future in as_completed(futures):
                extracted_content.extend(future.result())
        return extracted_content    
class NoExtractionStrategy(ExtractionStrategy):
    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        return [{"index": 0, "content": html}]
    
    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        return [{"index": i, "tags": [], "content": section} for i, section in enumerate(sections)]
   
class LLMExtractionStrategy(ExtractionStrategy):
    def __init__(self, provider: str = DEFAULT_PROVIDER, api_token: Optional[str] = None, instruction:str = None, **kwargs):
        """
        Initialize the strategy with clustering parameters.

        :param provider: The provider to use for extraction.
        :param api_token: The API token for the provider.
        :param instruction: The instruction to use for the LLM model.
        """
        super().__init__()    
        self.provider = provider
        self.api_token = api_token or PROVIDER_MODELS.get(provider, None) or os.getenv("OPENAI_API_KEY")
        self.instruction = instruction
        
        if not self.api_token:
            raise ValueError("API token must be provided for LLMExtractionStrategy. Update the config.py or set OPENAI_API_KEY environment variable.")
        
            
    def extract(self, url: str, ix:int, html: str) -> List[Dict[str, Any]]:
        # print("[LOG] Extracting blocks from URL:", url)
        print(f"[LOG] Call LLM for {url} - block index: {ix}")
        variable_values = {
            "URL": url,
            "HTML": escape_json_string(sanitize_html(html)),
        }
        
        if self.instruction:
            variable_values["REQUEST"] = self.instruction

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS if not self.instruction else PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION
        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )
        
        response = perform_completion_with_backoff(self.provider, prompt_with_variables, self.api_token)
        try:
            blocks = extract_xml_data(["blocks"], response.choices[0].message.content)['blocks']
            blocks = json.loads(blocks)
            for block in blocks:
                block['error'] = False
        except Exception as e:
            print("Error extracting blocks:", str(e))
            parsed, unparsed = split_and_parse_json_objects(response.choices[0].message.content)
            blocks = parsed
            if unparsed:
                blocks.append({
                    "index": 0,
                    "error": True,
                    "tags": ["error"],
                    "content": unparsed
                })
        
        print("[LOG] Extracted", len(blocks), "blocks from URL:", url, "block index:", ix)
        return blocks
    
    def _merge(self, documents):
        chunks = []
        sections = []
        total_token_so_far = 0

        for document in documents:
            if total_token_so_far < CHUNK_TOKEN_THRESHOLD:
                chunk = document.split(' ')
                total_token_so_far += len(chunk) * 1.3
                chunks.append(document)
            else:
                sections.append('\n\n'.join(chunks))
                chunks = [document]
                total_token_so_far = len(document.split(' ')) * 1.3 
                
        if chunks:
            sections.append('\n\n'.join(chunks))
            
        return sections       

    def run(self, url: str, sections: List[str]) -> List[Dict[str, Any]]:
        """
        Process sections sequentially with a delay for rate limiting issues, specifically for LLMExtractionStrategy.
        """
        
        merged_sections = self._merge(sections)
        extracted_content = []
        if self.provider.startswith("groq/"):
            # Sequential processing with a delay
            for ix, section in enumerate(merged_sections):
                extracted_content.extend(self.extract(ix, url, section))
                time.sleep(0.5)  # 500 ms delay between each processing
        else:
            # Parallel processing using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=4) as executor:
                extract_func = partial(self.extract, url)
                futures = [executor.submit(extract_func, ix, section) for ix, section in enumerate(merged_sections)]
                
                for future in as_completed(futures):
                    extracted_content.extend(future.result())

        
        return extracted_content        
  
class CosineStrategy(ExtractionStrategy):
    def __init__(self, semantic_filter = None, word_count_threshold=10, max_dist=0.2, linkage_method='ward', top_k=3, model_name = 'BAAI/bge-small-en-v1.5', **kwargs):
        """
        Initialize the strategy with clustering parameters.

        :param semantic_filter: A keyword filter for document filtering.
        :param word_count_threshold: Minimum number of words per cluster.
        :param max_dist: The maximum cophenetic distance on the dendrogram to form clusters.
        :param linkage_method: The linkage method for hierarchical clustering.
        :param top_k: Number of top categories to extract.
        """
        super().__init__()
        
        self.semantic_filter = semantic_filter
        self.word_count_threshold = word_count_threshold
        self.max_dist = max_dist
        self.linkage_method = linkage_method
        self.top_k = top_k
        self.timer = time.time()
        
        self.buffer_embeddings = np.array([])

        if model_name == "bert-base-uncased":
            self.tokenizer, self.model = load_bert_base_uncased()
        elif model_name == "BAAI/bge-small-en-v1.5":
            self.tokenizer, self.model = load_bge_small_en_v1_5()

        self.nlp = load_text_multilabel_classifier()
        print(f"[LOG] Model loaded {model_name}, models/reuters, took " + str(time.time() - self.timer) + " seconds")

    def filter_documents_embeddings(self, documents: List[str], semantic_filter: str, threshold: float = 0.5) -> List[str]:
        """
        Filter documents based on the cosine similarity of their embeddings with the semantic_filter embedding.

        :param documents: List of text chunks (documents).
        :param semantic_filter: A string containing the keywords for filtering.
        :param threshold: Cosine similarity threshold for filtering documents.
        :return: Filtered list of documents.
        """
        from sklearn.metrics.pairwise import cosine_similarity
        if not semantic_filter:
            return documents
        # Compute embedding for the keyword filter
        query_embedding = self.get_embeddings([semantic_filter])[0]
        
        # Compute embeddings for the docu  ments
        document_embeddings = self.get_embeddings(documents)
        
        # Calculate cosine similarity between the query embedding and document embeddings
        similarities = cosine_similarity([query_embedding], document_embeddings).flatten()
        
        # Filter documents based on the similarity threshold
        filtered_docs = [doc for doc, sim in zip(documents, similarities) if sim >= threshold]
        
        return filtered_docs

    def get_embeddings(self, sentences: List[str], bypass_buffer=True):
        """
        Get BERT embeddings for a list of sentences.

        :param sentences: List of text chunks (sentences).
        :return: NumPy array of embeddings.
        """
        # if self.buffer_embeddings.any() and not bypass_buffer:
        #     return self.buffer_embeddings
        
        import torch 
        # Tokenize sentences and convert to tensor
        encoded_input = self.tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
        # Compute token embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)
            
        # Get embeddings from the last hidden state (mean pooling)
        embeddings = model_output.last_hidden_state.mean(1)
        self.buffer_embeddings = embeddings.numpy()
        return embeddings.numpy()

    def hierarchical_clustering(self, sentences: List[str]):
        """
        Perform hierarchical clustering on sentences and return cluster labels.

        :param sentences: List of text chunks (sentences).
        :return: NumPy array of cluster labels.
        """
        # Get embeddings
        from scipy.cluster.hierarchy import linkage, fcluster
        from scipy.spatial.distance import pdist
        self.timer = time.time()
        embeddings = self.get_embeddings(sentences, bypass_buffer=False)
        # print(f"[LOG] 🚀 Embeddings computed in {time.time() - self.timer:.2f} seconds")
        # Compute pairwise cosine distances
        distance_matrix = pdist(embeddings, 'cosine')
        # Perform agglomerative clustering respecting order
        linked = linkage(distance_matrix, method=self.linkage_method)
        # Form flat clusters
        labels = fcluster(linked, self.max_dist, criterion='distance')
        return labels

    def filter_clusters_by_word_count(self, clusters: Dict[int, List[str]]):
        """
        Filter clusters to remove those with a word count below the threshold.

        :param clusters: Dictionary of clusters.
        :return: Filtered dictionary of clusters.
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

        :param url: The URL of the webpage.
        :param html: The HTML content of the webpage.
        :return: A list of dictionaries representing the clusters.
        """
        # Assume `html` is a list of text chunks for this strategy
        t = time.time()
        text_chunks = html.split(self.DEL)  # Split by lines or paragraphs as needed
        
        # Pre-filter documents using embeddings and semantic_filter
        text_chunks = self.filter_documents_embeddings(text_chunks, self.semantic_filter)

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
        cluster_list = [{"index": int(idx), "tags" : [], "content": " ".join(filtered_clusters[idx])} for idx in sorted(filtered_clusters)]
        
        labels = self.nlp([cluster['content'] for cluster in cluster_list])
        
        for cluster, label in zip(cluster_list, labels):
            cluster['tags'] = label

        # Process the text with the loaded model
        # for cluster in  cluster_list:
        #     cluster['tags'] = self.nlp(cluster['content'])[0]['label']
            # doc = self.nlp(cluster['content'])
            # tok_k = self.top_k
            # top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
            # cluster['tags'] = [cat for cat, _ in top_categories]
        
        # print(f"[LOG] 🚀 Categorization done in {time.time() - t:.2f} seconds")
        
        return cluster_list

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Process sections using hierarchical clustering.

        :param url: The URL of the webpage.
        :param sections: List of sections (strings) to process.
        :param provider: The provider to be used for extraction (not used here).
        :param api_token: Optional API token for the provider (not used here).
        :return: A list of processed JSON blocks.
        """
        # This strategy processes all sections together
        
        return self.extract(url, self.DEL.join(sections), **kwargs)
    
class TopicExtractionStrategy(ExtractionStrategy):
    def __init__(self, num_keywords: int = 3, **kwargs):
        """
        Initialize the topic extraction strategy with parameters for topic segmentation.

        :param num_keywords: Number of keywords to represent each topic segment.
        """
        import nltk
        super().__init__()
        self.num_keywords = num_keywords
        self.tokenizer = nltk.TextTilingTokenizer()

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from a given text segment using simple frequency analysis.

        :param text: The text segment from which to extract keywords.
        :return: A list of keyword strings.
        """
        import nltk
        # Tokenize the text and compute word frequency
        words = nltk.word_tokenize(text)
        freq_dist = nltk.FreqDist(words)
        # Get the most common words as keywords
        keywords = [word for (word, _) in freq_dist.most_common(self.num_keywords)]
        return keywords

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract topics from HTML content using TextTiling for segmentation and keyword extraction.

        :param url: The URL of the webpage.
        :param html: The HTML content of the webpage.
        :param provider: The provider to be used for extraction (not used here).
        :param api_token: Optional API token for the provider (not used here).
        :return: A list of dictionaries representing the topics.
        """
        # Use TextTiling to segment the text into topics
        segmented_topics = html.split(self.DEL)  # Split by lines or paragraphs as needed

        # Prepare the output as a list of dictionaries
        topic_list = []
        for i, segment in enumerate(segmented_topics):
            # Extract keywords for each segment
            keywords = self.extract_keywords(segment)
            topic_list.append({
                "index": i,
                "content": segment,
                "keywords": keywords
            })

        return topic_list

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Process sections using topic segmentation and keyword extraction.

        :param url: The URL of the webpage.
        :param sections: List of sections (strings) to process.
        :param provider: The provider to be used for extraction (not used here).
        :param api_token: Optional API token for the provider (not used here).
        :return: A list of processed JSON blocks.
        """
        # Concatenate sections into a single text for coherent topic segmentation
        
        
        return self.extract(url, self.DEL.join(sections), **kwargs)
    
class ContentSummarizationStrategy(ExtractionStrategy):
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6", **kwargs):
        """
        Initialize the content summarization strategy with a specific model.

        :param model_name: The model to use for summarization.
        """
        from transformers import pipeline
        self.summarizer = pipeline("summarization", model=model_name)

    def extract(self, url: str, text: str, provider: str = None, api_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Summarize a single section of text.

        :param url: The URL of the webpage.
        :param text: A section of text to summarize.
        :param provider: The provider to be used for extraction (not used here).
        :param api_token: Optional API token for the provider (not used here).
        :return: A dictionary with the summary.
        """
        try:
            summary = self.summarizer(text, max_length=130, min_length=30, do_sample=False)
            return {"summary": summary[0]['summary_text']}
        except Exception as e:
            print(f"Error summarizing text: {e}")
            return {"summary": text}  # Fallback to original text if summarization fails

    def run(self, url: str, sections: List[str], provider: str = None, api_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process each section in parallel to produce summaries.

        :param url: The URL of the webpage.
        :param sections: List of sections (strings) to summarize.
        :param provider: The provider to be used for extraction (not used here).
        :param api_token: Optional API token for the provider (not used here).
        :return: A list of dictionaries with summaries for each section.
        """
        # Use a ThreadPoolExecutor to summarize in parallel
        summaries = []
        with ThreadPoolExecutor() as executor:
            # Create a future for each section's summarization
            future_to_section = {executor.submit(self.extract, url, section, provider, api_token): i for i, section in enumerate(sections)}
            for future in as_completed(future_to_section):
                section_index = future_to_section[future]
                try:
                    summary_result = future.result()
                    summaries.append((section_index, summary_result))
                except Exception as e:
                    print(f"Error processing section {section_index}: {e}")
                    summaries.append((section_index, {"summary": sections[section_index]}))  # Fallback to original text

        # Sort summaries by the original section index to maintain order
        summaries.sort(key=lambda x: x[0])
        return [summary for _, summary in summaries]