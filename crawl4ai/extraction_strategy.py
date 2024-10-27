from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, time
# from optimum.intel import IPEXModel
from .prompts import *
from .config import *
from .utils import *
from functools import partial
from .model_loader import *
import math
import numpy as np
from lxml import etree

class ExtractionStrategy(ABC):
    """
    Abstract base class for all extraction strategies.
    """
    
    def __init__(self, **kwargs):
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
    def __init__(self, 
                 provider: str = DEFAULT_PROVIDER, api_token: Optional[str] = None, 
                 instruction:str = None, schema:Dict = None, extraction_type = "block", **kwargs):
        """
        Initialize the strategy with clustering parameters.

        :param provider: The provider to use for extraction.
        :param api_token: The API token for the provider.
        :param instruction: The instruction to use for the LLM model.
        """
        super().__init__() 
        self.provider = provider
        self.api_token = api_token or PROVIDER_MODELS.get(provider, "no-token") or os.getenv("OPENAI_API_KEY")
        self.instruction = instruction
        self.extract_type = extraction_type
        self.schema = schema
        if schema:
            self.extract_type = "schema"
        
        self.chunk_token_threshold = kwargs.get("chunk_token_threshold", CHUNK_TOKEN_THRESHOLD)
        self.overlap_rate = kwargs.get("overlap_rate", OVERLAP_RATE)
        self.word_token_rate = kwargs.get("word_token_rate", WORD_TOKEN_RATE)
        self.apply_chunking = kwargs.get("apply_chunking", True)
        self.base_url = kwargs.get("base_url", None)
        self.api_base = kwargs.get("api_base", kwargs.get("base_url", None))
        self.extra_args = kwargs.get("extra_args", {})
        if not self.apply_chunking:
            self.chunk_token_threshold = 1e9
        
        self.verbose = kwargs.get("verbose", False)
        
        if not self.api_token:
            raise ValueError("API token must be provided for LLMExtractionStrategy. Update the config.py or set OPENAI_API_KEY environment variable.")
        
            
    def extract(self, url: str, ix:int, html: str) -> List[Dict[str, Any]]:
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
            extra_args = self.extra_args
            ) # , json_response=self.extract_type == "schema")
        try:
            blocks = extract_xml_data(["blocks"], response.choices[0].message.content)['blocks']
            blocks = json.loads(blocks)
            for block in blocks:
                block['error'] = False
        except Exception as e:
            parsed, unparsed = split_and_parse_json_objects(response.choices[0].message.content)
            blocks = parsed
            if unparsed:
                blocks.append({
                    "index": 0,
                    "error": True,
                    "tags": ["error"],
                    "content": unparsed
                })
        
        if self.verbose:
            print("[LOG] Extracted", len(blocks), "blocks from URL:", url, "block index:", ix)
        return blocks
    
    def _merge(self, documents, chunk_token_threshold, overlap):
        chunks = []
        sections = []
        total_tokens = 0

        # Calculate the total tokens across all documents
        for document in documents:
            total_tokens += len(document.split(' ')) * self.word_token_rate

        # Calculate the number of sections needed
        num_sections = math.floor(total_tokens / chunk_token_threshold)
        if num_sections < 1:
            num_sections = 1  # Ensure there is at least one section
        adjusted_chunk_threshold = total_tokens / num_sections

        total_token_so_far = 0
        current_chunk = []

        for document in documents:
            tokens = document.split(' ')
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
                
                sections.append(' '.join(current_chunk))
                current_chunk = tokens
                total_token_so_far = token_count

        # Add the last chunk
        if current_chunk:
            sections.append(' '.join(current_chunk))

        return sections


    def run(self, url: str, sections: List[str]) -> List[Dict[str, Any]]:
        """
        Process sections sequentially with a delay for rate limiting issues, specifically for LLMExtractionStrategy.
        """
        
        merged_sections = self._merge(
            sections, self.chunk_token_threshold,
            overlap= int(self.chunk_token_threshold * self.overlap_rate)
        )
        extracted_content = []
        if self.provider.startswith("groq/"):
            # Sequential processing with a delay
            for ix, section in enumerate(merged_sections):
                extract_func = partial(self.extract, url)
                extracted_content.extend(extract_func(ix, sanitize_input_encode(section)))
                time.sleep(0.5)  # 500 ms delay between each processing
        else:
            # Parallel processing using ThreadPoolExecutor
            # extract_func = partial(self.extract, url)
            # for ix, section in enumerate(merged_sections):
            #     extracted_content.append(extract_func(ix, section))            
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                extract_func = partial(self.extract, url)
                futures = [executor.submit(extract_func, ix, sanitize_input_encode(section)) for ix, section in enumerate(merged_sections)]
                
                for future in as_completed(futures):
                    try:
                        extracted_content.extend(future.result())
                    except Exception as e:
                        if self.verbose:
                            print(f"Error in thread execution: {e}")
                        # Add error information to extracted_content
                        extracted_content.append({
                            "index": 0,
                            "error": True,
                            "tags": ["error"],
                            "content": str(e)
                        })

        
        return extracted_content        
  
class CosineStrategy(ExtractionStrategy):
    def __init__(self, semantic_filter = None, word_count_threshold=10, max_dist=0.2, linkage_method='ward', top_k=3, model_name = 'sentence-transformers/all-MiniLM-L6-v2', sim_threshold = 0.3, **kwargs):
        """
        Initialize the strategy with clustering parameters.

        Args:
            semantic_filter (str): A keyword filter for document filtering.
            word_count_threshold (int): Minimum number of words per cluster.
            max_dist (float): The maximum cophenetic distance on the dendrogram to form clusters.
            linkage_method (str): The linkage method for hierarchical clustering.
            top_k (int): Number of top categories to extract.
        """
        super().__init__()
        
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
            print(f"[LOG] Model loaded {model_name}, models/reuters, took " + str(time.time() - self.timer) + " seconds")

    def filter_documents_embeddings(self, documents: List[str], semantic_filter: str, at_least_k: int = 20) -> List[str]:
        """
        Filter and sort documents based on the cosine similarity of their embeddings with the semantic_filter embedding.

        :param documents: List of text chunks (documents).
        :param semantic_filter: A string containing the keywords for filtering.
        :param threshold: Cosine similarity threshold for filtering documents.
        :param at_least_k: Minimum number of documents to return.
        :return: List of filtered documents, ensuring at least `at_least_k` documents.
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
        similarities = cosine_similarity([query_embedding], document_embeddings).flatten()
        
        # Filter documents based on the similarity threshold
        filtered_docs = [(doc, sim) for doc, sim in zip(documents, similarities) if sim >= self.sim_threshold]
        
        # If the number of filtered documents is less than at_least_k, sort remaining documents by similarity
        if len(filtered_docs) < at_least_k:
            remaining_docs = [(doc, sim) for doc, sim in zip(documents, similarities) if sim < self.sim_threshold]
            remaining_docs.sort(key=lambda x: x[1], reverse=True)
            filtered_docs.extend(remaining_docs[:at_least_k - len(filtered_docs)])
        
        # Extract the document texts from the tuples
        filtered_docs = [doc for doc, _ in filtered_docs]
        
        return filtered_docs[:at_least_k]
    
    def get_embeddings(self, sentences: List[str], batch_size=None, bypass_buffer=False):
        """
        Get BERT embeddings for a list of sentences.

        :param sentences: List of text chunks (sentences).
        :return: NumPy array of embeddings.
        """
        # if self.buffer_embeddings.any() and not bypass_buffer:
        #     return self.buffer_embeddings
        
        if self.device.type in [ "cpu", "gpu", "cuda", "mps"]:
            import torch 
            # Tokenize sentences and convert to tensor
            if batch_size is None:
                batch_size = self.default_batch_size
                        
            all_embeddings = []
            for i in range(0, len(sentences), batch_size):
                batch_sentences = sentences[i:i + batch_size]
                encoded_input = self.tokenizer(batch_sentences, padding=True, truncation=True, return_tensors='pt')
                encoded_input = {key: tensor.to(self.device) for key, tensor in encoded_input.items()}
                
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
                batch_sentences = sentences[i:i + batch_size]
                embeddings = self.model(batch_sentences)
                all_embeddings.append(embeddings)
                
            self.buffer_embeddings = np.vstack(all_embeddings)
        return self.buffer_embeddings

    def hierarchical_clustering(self, sentences: List[str], embeddings = None):
        """
        Perform hierarchical clustering on sentences and return cluster labels.

        :param sentences: List of text chunks (sentences).
        :return: NumPy array of cluster labels.
        """
        # Get embeddings
        from scipy.cluster.hierarchy import linkage, fcluster
        from scipy.spatial.distance import pdist
        self.timer = time.time()
        embeddings = self.get_embeddings(sentences, bypass_buffer=True)
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
        
        if self.verbose:
            print(f"[LOG] 🚀 Assign tags using {self.device}")
        
        if self.device.type in ["gpu", "cuda", "mps", "cpu"]:
            labels = self.nlp([cluster['content'] for cluster in cluster_list])
            
            for cluster, label in zip(cluster_list, labels):
                cluster['tags'] = label
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
  
class JsonCssExtractionStrategy(ExtractionStrategy):
    def __init__(self, schema: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.schema = schema

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        base_elements = soup.select(self.schema['baseSelector'])
        
        results = []
        for element in base_elements:
            item = self._extract_item(element, self.schema['fields'])
            if item:
                results.append(item)
        
        return results

    

    def _extract_field(self, element, field):
        try:
            if field['type'] == 'nested':
                nested_element = element.select_one(field['selector'])
                return self._extract_item(nested_element, field['fields']) if nested_element else {}
            
            if field['type'] == 'list':
                elements = element.select(field['selector'])
                return [self._extract_list_item(el, field['fields']) for el in elements]
            
            if field['type'] == 'nested_list':
                elements = element.select(field['selector'])
                return [self._extract_item(el, field['fields']) for el in elements]
            
            return self._extract_single_field(element, field)
        except Exception as e:
            if self.verbose:
                print(f"Error extracting field {field['name']}: {str(e)}")
            return field.get('default')

    def _extract_list_item(self, element, fields):
        item = {}
        for field in fields:
            value = self._extract_single_field(element, field)
            if value is not None:
                item[field['name']] = value
        return item
    
    def _extract_single_field(self, element, field):
        if 'selector' in field:
            selected = element.select_one(field['selector'])
            if not selected:
                return field.get('default')
        else:
            selected = element

        value = None
        if field['type'] == 'text':
            value = selected.get_text(strip=True)
        elif field['type'] == 'attribute':
            value = selected.get(field['attribute'])
        elif field['type'] == 'html':
            value = str(selected)
        elif field['type'] == 'regex':
            text = selected.get_text(strip=True)
            match = re.search(field['pattern'], text)
            value = match.group(1) if match else None

        if 'transform' in field:
            value = self._apply_transform(value, field['transform'])

        return value if value is not None else field.get('default')

    def _extract_item(self, element, fields):
        item = {}
        for field in fields:
            if field['type'] == 'computed':
                value = self._compute_field(item, field)
            else:
                value = self._extract_field(element, field)
            if value is not None:
                item[field['name']] = value
        return item
    
    def _apply_transform(self, value, transform):
        if transform == 'lowercase':
            return value.lower()
        elif transform == 'uppercase':
            return value.upper()
        elif transform == 'strip':
            return value.strip()
        return value

    def _compute_field(self, item, field):
        try:
            if 'expression' in field:
                return eval(field['expression'], {}, item)
            elif 'function' in field:
                return field['function'](item)
        except Exception as e:
            if self.verbose:
                print(f"Error computing field {field['name']}: {str(e)}")
            return field.get('default')

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        combined_html = self.DEL.join(sections)
        return self.extract(url, combined_html, **kwargs)
    
class JsonXPATHExtractionStrategy(ExtractionStrategy):
    def __init__(self, schema: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.schema = schema
        self.use_cssselect = self._check_cssselect()

    def _check_cssselect(self):
        try:
            import cssselect
            return True
        except ImportError:
            print("Warning: cssselect is not installed. Falling back to XPath for all selectors.")
            return False

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        self.soup = BeautifulSoup(html, 'lxml')
        self.tree = etree.HTML(str(self.soup))
        
        selector_type = 'xpath' if not self.use_cssselect else self.schema.get('selectorType', 'css')
        base_selector = self.schema.get('baseXPath' if selector_type == 'xpath' else 'baseSelector')
        base_elements = self._select_elements(base_selector, selector_type)
        
        results = []
        for element in base_elements:
            item = self._extract_item(element, self.schema['fields'])
            if item:
                results.append(item)
        
        return results

    def _select_elements(self, selector, selector_type, element=None):
        if selector_type == 'xpath' or not self.use_cssselect:
            return self.tree.xpath(selector) if element is None else element.xpath(selector)
        else:  # CSS
            return self.tree.cssselect(selector) if element is None else element.cssselect(selector)

    def _extract_field(self, element, field):
        try:
            selector_type = 'xpath' if not self.use_cssselect else field.get('selectorType', 'css')
            selector = field.get('xpathSelector' if selector_type == 'xpath' else 'selector')
            
            if field['type'] == 'nested':
                nested_element = self._select_elements(selector, selector_type, element)
                return self._extract_item(nested_element[0], field['fields']) if nested_element else {}
            
            if field['type'] == 'list':
                elements = self._select_elements(selector, selector_type, element)
                return [self._extract_list_item(el, field['fields']) for el in elements]
            
            if field['type'] == 'nested_list':
                elements = self._select_elements(selector, selector_type, element)
                return [self._extract_item(el, field['fields']) for el in elements]
            
            return self._extract_single_field(element, field)
        except Exception as e:
            if self.verbose:
                print(f"Error extracting field {field['name']}: {str(e)}")
            return field.get('default')

    def _extract_list_item(self, element, fields):
        item = {}
        for field in fields:
            value = self._extract_single_field(element, field)
            if value is not None:
                item[field['name']] = value
        return item
    
    def _extract_single_field(self, element, field):
        selector_type = field.get('selectorType', 'css')
        
        if 'selector' in field:
            selected = self._select_elements(field['selector'], selector_type, element)
            if not selected:
                return field.get('default')
            selected = selected[0]
        else:
            selected = element

        value = None
        if field['type'] == 'text':
            value = selected.text_content().strip() if hasattr(selected, 'text_content') else selected.text.strip()
        elif field['type'] == 'attribute':
            value = selected.get(field['attribute'])
        elif field['type'] == 'html':
            value = etree.tostring(selected, encoding='unicode')
        elif field['type'] == 'regex':
            text = selected.text_content().strip() if hasattr(selected, 'text_content') else selected.text.strip()
            match = re.search(field['pattern'], text)
            value = match.group(1) if match else None

        if 'transform' in field:
            value = self._apply_transform(value, field['transform'])

        return value if value is not None else field.get('default')

    def _extract_item(self, element, fields):
        item = {}
        for field in fields:
            if field['type'] == 'computed':
                value = self._compute_field(item, field)
            else:
                value = self._extract_field(element, field)
            if value is not None:
                item[field['name']] = value
        return item
    
    def _apply_transform(self, value, transform):
        if transform == 'lowercase':
            return value.lower()
        elif transform == 'uppercase':
            return value.upper()
        elif transform == 'strip':
            return value.strip()
        return value

    def _compute_field(self, item, field):
        try:
            if 'expression' in field:
                return eval(field['expression'], {}, item)
            elif 'function' in field:
                return field['function'](item)
        except Exception as e:
            if self.verbose:
                print(f"Error computing field {field['name']}: {str(e)}")
            return field.get('default')

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        combined_html = self.DEL.join(sections)
        return self.extract(url, combined_html, **kwargs)