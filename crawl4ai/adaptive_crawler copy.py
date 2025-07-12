"""
Adaptive Web Crawler for Crawl4AI

This module implements adaptive information foraging for efficient web crawling.
It determines when sufficient information has been gathered to answer a query,
avoiding unnecessary crawls while ensuring comprehensive coverage.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
import asyncio
import pickle
import os
import json
import math
from collections import defaultdict, Counter
import re
from pathlib import Path

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig, LinkPreviewConfig
from crawl4ai.models import Link, CrawlResult


@dataclass
class CrawlState:
    """Tracks the current state of adaptive crawling"""
    crawled_urls: Set[str] = field(default_factory=set)
    knowledge_base: List[CrawlResult] = field(default_factory=list)
    pending_links: List[Link] = field(default_factory=list)
    query: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Statistical tracking
    term_frequencies: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    document_frequencies: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    documents_with_terms: Dict[str, Set[int]] = field(default_factory=lambda: defaultdict(set))
    total_documents: int = 0
    
    # History tracking for saturation
    new_terms_history: List[int] = field(default_factory=list)
    crawl_order: List[str] = field(default_factory=list)
    
    # Embedding-specific tracking (only if strategy is embedding)
    kb_embeddings: Optional[Any] = None  # Will be numpy array
    query_embeddings: Optional[Any] = None  # Will be numpy array
    expanded_queries: List[str] = field(default_factory=list)
    coverage_shape: Optional[Any] = None  # Alpha shape
    semantic_gaps: List[Tuple[List[float], float]] = field(default_factory=list)  # Serializable
    embedding_model: str = ""
    
    def save(self, path: Union[str, Path]):
        """Save state to disk for persistence"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert CrawlResult objects to dicts for serialization
        state_dict = {
            'crawled_urls': list(self.crawled_urls),
            'knowledge_base': [self._crawl_result_to_dict(cr) for cr in self.knowledge_base],
            'pending_links': [link.model_dump() for link in self.pending_links],
            'query': self.query,
            'metrics': self.metrics,
            'term_frequencies': dict(self.term_frequencies),
            'document_frequencies': dict(self.document_frequencies),
            'documents_with_terms': {k: list(v) for k, v in self.documents_with_terms.items()},
            'total_documents': self.total_documents,
            'new_terms_history': self.new_terms_history,
            'crawl_order': self.crawl_order,
            # Embedding-specific fields (convert numpy arrays to lists for JSON)
            'kb_embeddings': self.kb_embeddings.tolist() if self.kb_embeddings is not None else None,
            'query_embeddings': self.query_embeddings.tolist() if self.query_embeddings is not None else None,
            'expanded_queries': self.expanded_queries,
            'semantic_gaps': self.semantic_gaps,
            'embedding_model': self.embedding_model
        }
        
        with open(path, 'w') as f:
            json.dump(state_dict, f, indent=2)
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'CrawlState':
        """Load state from disk"""
        path = Path(path)
        with open(path, 'r') as f:
            state_dict = json.load(f)
        
        state = cls()
        state.crawled_urls = set(state_dict['crawled_urls'])
        state.knowledge_base = [cls._dict_to_crawl_result(d) for d in state_dict['knowledge_base']]
        state.pending_links = [Link(**link_dict) for link_dict in state_dict['pending_links']]
        state.query = state_dict['query']
        state.metrics = state_dict['metrics']
        state.term_frequencies = defaultdict(int, state_dict['term_frequencies'])
        state.document_frequencies = defaultdict(int, state_dict['document_frequencies'])
        state.documents_with_terms = defaultdict(set, {k: set(v) for k, v in state_dict['documents_with_terms'].items()})
        state.total_documents = state_dict['total_documents']
        state.new_terms_history = state_dict['new_terms_history']
        state.crawl_order = state_dict['crawl_order']
        
        # Load embedding-specific fields (convert lists back to numpy arrays)
        import numpy as np
        state.kb_embeddings = np.array(state_dict['kb_embeddings']) if state_dict.get('kb_embeddings') is not None else None
        state.query_embeddings = np.array(state_dict['query_embeddings']) if state_dict.get('query_embeddings') is not None else None
        state.expanded_queries = state_dict.get('expanded_queries', [])
        state.semantic_gaps = state_dict.get('semantic_gaps', [])
        state.embedding_model = state_dict.get('embedding_model', '')
        
        return state
    
    @staticmethod
    def _crawl_result_to_dict(cr: CrawlResult) -> Dict:
        """Convert CrawlResult to serializable dict"""
        # Extract markdown content safely
        markdown_content = ""
        if hasattr(cr, 'markdown') and cr.markdown:
            if hasattr(cr.markdown, 'raw_markdown'):
                markdown_content = cr.markdown.raw_markdown
            else:
                markdown_content = str(cr.markdown)
        
        return {
            'url': cr.url,
            'content': markdown_content,
            'links': cr.links if hasattr(cr, 'links') else {},
            'metadata': cr.metadata if hasattr(cr, 'metadata') else {}
        }
    
    @staticmethod
    def _dict_to_crawl_result(d: Dict):
        """Convert dict back to CrawlResult"""
        # Create a mock object that has the minimal interface we need
        class MockMarkdown:
            def __init__(self, content):
                self.raw_markdown = content
        
        class MockCrawlResult:
            def __init__(self, url, content, links, metadata):
                self.url = url
                self.markdown = MockMarkdown(content)
                self.links = links
                self.metadata = metadata
        
        return MockCrawlResult(
            url=d['url'],
            content=d.get('content', ''),
            links=d.get('links', {}),
            metadata=d.get('metadata', {})
        )


@dataclass
class AdaptiveConfig:
    """Configuration for adaptive crawling"""
    confidence_threshold: float = 0.7
    max_depth: int = 5
    max_pages: int = 20
    top_k_links: int = 3
    min_gain_threshold: float = 0.1
    strategy: str = "statistical"  # statistical, embedding, llm
    
    # Advanced parameters
    saturation_threshold: float = 0.8
    consistency_threshold: float = 0.7
    coverage_weight: float = 0.4
    consistency_weight: float = 0.3
    saturation_weight: float = 0.3
    
    # Link scoring parameters
    relevance_weight: float = 0.5
    novelty_weight: float = 0.3
    authority_weight: float = 0.2
    
    # Persistence
    save_state: bool = False
    state_path: Optional[str] = None
    
    # Embedding strategy parameters
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_llm_config: Optional[Dict] = None  # Separate config for embeddings
    n_query_variations: int = 10
    coverage_threshold: float = 0.85
    alpha_shape_alpha: float = 0.5
    
    # Embedding confidence calculation parameters
    embedding_coverage_radius: float = 0.2  # Distance threshold for "covered" query points
    # Example: With radius=0.2, a query point is considered covered if ANY document 
    # is within cosine distance 0.2 (very similar). Smaller = stricter coverage requirement
    
    embedding_k_exp: float = 3.0  # Exponential decay factor for distance-to-score mapping
    # Example: score = exp(-k_exp * distance). With k_exp=1, distance 0.2 → score 0.82,
    # distance 0.5 → score 0.61. Higher k_exp = steeper decay = more emphasis on very close matches
    
    embedding_nearest_weight: float = 0.7  # Weight for nearest neighbor in hybrid scoring
    embedding_top_k_weight: float = 0.3  # Weight for top-k average in hybrid scoring
    # Example: If nearest doc has score 0.9 and top-3 avg is 0.6, final = 0.7*0.9 + 0.3*0.6 = 0.81
    # Higher nearest_weight = more focus on best match vs neighborhood density
    
    # Embedding link selection parameters  
    embedding_overlap_threshold: float = 0.85  # Similarity threshold for penalizing redundant links
    # Example: Links with >0.85 similarity to existing KB get penalized to avoid redundancy
    # Lower = more aggressive deduplication, Higher = allow more similar content
    
    # Embedding stopping criteria parameters
    embedding_min_relative_improvement: float = 0.1  # Minimum relative improvement to continue
    # Example: If confidence is 0.6, need improvement > 0.06 per batch to continue crawling
    # Lower = more patient crawling, Higher = stop earlier when progress slows
    
    embedding_validation_min_score: float = 0.4  # Minimum validation score to trust convergence
    # Example: Even if learning converged, keep crawling if validation score < 0.4
    # This prevents premature stopping when we haven't truly covered the query space
    
    # Quality confidence mapping parameters (for display to user)
    embedding_quality_min_confidence: float = 0.7  # Minimum confidence for validated systems
    embedding_quality_max_confidence: float = 0.95  # Maximum realistic confidence
    embedding_quality_scale_factor: float = 0.833  # Scaling factor for confidence mapping
    # Example: Validated system with learning_score=0.5 → confidence = 0.7 + (0.5-0.4)*0.833 = 0.78
    # These control how internal scores map to user-friendly confidence percentages
    
    def validate(self):
        """Validate configuration parameters"""
        assert 0 <= self.confidence_threshold <= 1, "confidence_threshold must be between 0 and 1"
        assert self.max_depth > 0, "max_depth must be positive"
        assert self.max_pages > 0, "max_pages must be positive"
        assert self.top_k_links > 0, "top_k_links must be positive"
        assert 0 <= self.min_gain_threshold <= 1, "min_gain_threshold must be between 0 and 1"
        
        # Check weights sum to 1
        weight_sum = self.coverage_weight + self.consistency_weight + self.saturation_weight
        assert abs(weight_sum - 1.0) < 0.001, f"Coverage weights must sum to 1, got {weight_sum}"
        
        weight_sum = self.relevance_weight + self.novelty_weight + self.authority_weight
        assert abs(weight_sum - 1.0) < 0.001, f"Link scoring weights must sum to 1, got {weight_sum}"
        
        # Validate embedding parameters
        assert 0 < self.embedding_coverage_radius < 1, "embedding_coverage_radius must be between 0 and 1"
        assert self.embedding_k_exp > 0, "embedding_k_exp must be positive"
        assert 0 <= self.embedding_nearest_weight <= 1, "embedding_nearest_weight must be between 0 and 1"
        assert 0 <= self.embedding_top_k_weight <= 1, "embedding_top_k_weight must be between 0 and 1"
        assert abs(self.embedding_nearest_weight + self.embedding_top_k_weight - 1.0) < 0.001, "Embedding weights must sum to 1"
        assert 0 <= self.embedding_overlap_threshold <= 1, "embedding_overlap_threshold must be between 0 and 1"
        assert 0 < self.embedding_min_relative_improvement < 1, "embedding_min_relative_improvement must be between 0 and 1"
        assert 0 <= self.embedding_validation_min_score <= 1, "embedding_validation_min_score must be between 0 and 1"
        assert 0 <= self.embedding_quality_min_confidence <= 1, "embedding_quality_min_confidence must be between 0 and 1"
        assert 0 <= self.embedding_quality_max_confidence <= 1, "embedding_quality_max_confidence must be between 0 and 1"
        assert self.embedding_quality_scale_factor > 0, "embedding_quality_scale_factor must be positive"


class CrawlStrategy(ABC):
    """Abstract base class for crawling strategies"""
    
    @abstractmethod
    async def calculate_confidence(self, state: CrawlState) -> float:
        """Calculate overall confidence that we have sufficient information"""
        pass
    
    @abstractmethod
    async def rank_links(self, state: CrawlState, config: AdaptiveConfig) -> List[Tuple[Link, float]]:
        """Rank pending links by expected information gain"""
        pass
    
    @abstractmethod
    async def should_stop(self, state: CrawlState, config: AdaptiveConfig) -> bool:
        """Determine if crawling should stop"""
        pass
    
    @abstractmethod
    async def update_state(self, state: CrawlState, new_results: List[CrawlResult]) -> None:
        """Update state with new crawl results"""
        pass


class StatisticalStrategy(CrawlStrategy):
    """Pure statistical approach - no LLM, no embeddings"""
    
    def __init__(self):
        self.idf_cache = {}
        self.bm25_k1 = 1.2  # BM25 parameter
        self.bm25_b = 0.75  # BM25 parameter
        
    async def calculate_confidence(self, state: CrawlState) -> float:
        """Calculate confidence using coverage, consistency, and saturation"""
        if not state.knowledge_base:
            return 0.0
            
        coverage = self._calculate_coverage(state)
        consistency = self._calculate_consistency(state)
        saturation = self._calculate_saturation(state)

        # Store individual metrics
        state.metrics['coverage'] = coverage
        state.metrics['consistency'] = consistency
        state.metrics['saturation'] = saturation

        # Weighted combination (weights from config not accessible here, using defaults)
        confidence = 0.4 * coverage + 0.3 * consistency + 0.3 * saturation
        
        return confidence
    
    def _calculate_coverage(self, state: CrawlState) -> float:
        """Coverage scoring - measures query term presence across knowledge base
        
        Returns a score between 0 and 1, where:
        - 0 means no query terms found
        - 1 means excellent coverage of all query terms
        """
        if not state.query or state.total_documents == 0:
            return 0.0
            
        query_terms = self._tokenize(state.query.lower())
        if not query_terms:
            return 0.0
            
        term_scores = []
        max_tf = max(state.term_frequencies.values()) if state.term_frequencies else 1
        
        for term in query_terms:
            tf = state.term_frequencies.get(term, 0)
            df = state.document_frequencies.get(term, 0)
            
            if df > 0:
                # Document coverage: what fraction of docs contain this term
                doc_coverage = df / state.total_documents
                
                # Frequency signal: normalized log frequency  
                freq_signal = math.log(1 + tf) / math.log(1 + max_tf) if max_tf > 0 else 0
                
                # Combined score: document coverage with frequency boost
                term_score = doc_coverage * (1 + 0.5 * freq_signal)
                term_scores.append(term_score)
            else:
                term_scores.append(0.0)
        
        # Average across all query terms
        coverage = sum(term_scores) / len(term_scores)
        
        # Apply square root curve to make score more intuitive
        # This helps differentiate between partial and good coverage
        return min(1.0, math.sqrt(coverage))
    
    def _calculate_consistency(self, state: CrawlState) -> float:
        """Information overlap between pages - high overlap suggests coherent topic coverage"""
        if len(state.knowledge_base) < 2:
            return 1.0  # Single or no documents are perfectly consistent
            
        # Calculate pairwise term overlap
        overlaps = []
        
        for i in range(len(state.knowledge_base)):
            for j in range(i + 1, len(state.knowledge_base)):
                # Get terms from both documents
                terms_i = set(self._get_document_terms(state.knowledge_base[i]))
                terms_j = set(self._get_document_terms(state.knowledge_base[j]))
                
                if terms_i and terms_j:
                    # Jaccard similarity
                    overlap = len(terms_i & terms_j) / len(terms_i | terms_j)
                    overlaps.append(overlap)
        
        if overlaps:
            # Average overlap as consistency measure
            consistency = sum(overlaps) / len(overlaps)
        else:
            consistency = 0.0
            
        return consistency
    
    def _calculate_saturation(self, state: CrawlState) -> float:
        """Diminishing returns indicator - are we still discovering new information?"""
        if not state.new_terms_history:
            return 0.0
            
        if len(state.new_terms_history) < 2:
            return 0.0  # Not enough history
            
        # Calculate rate of new term discovery
        recent_rate = state.new_terms_history[-1] if state.new_terms_history[-1] > 0 else 1
        initial_rate = state.new_terms_history[0] if state.new_terms_history[0] > 0 else 1
        
        # Saturation increases as rate decreases
        saturation = 1 - (recent_rate / initial_rate)
        
        return max(0.0, min(saturation, 1.0))
    
    async def rank_links(self, state: CrawlState, config: AdaptiveConfig) -> List[Tuple[Link, float]]:
        """Rank links by expected information gain"""
        scored_links = []
        
        for link in state.pending_links:
            # Skip already crawled URLs
            if link.href in state.crawled_urls:
                continue
                
            # Calculate component scores
            relevance = self._calculate_relevance(link, state)
            novelty = self._calculate_novelty(link, state)
            authority = 1.0
            # authority = self._calculate_authority(link)
            
            # Combined score
            score = (config.relevance_weight * relevance +
                    config.novelty_weight * novelty +
                    config.authority_weight * authority)
            
            scored_links.append((link, score))
        
        # Sort by score descending
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        return scored_links
    
    def _calculate_relevance(self, link: Link, state: CrawlState) -> float:
        """BM25 relevance score between link preview and query"""
        if not state.query or not link:
            return 0.0
            
        # Combine available text from link
        link_text = ' '.join(filter(None, [
            link.text or '',
            link.title or '',
            link.head_data.get('meta', {}).get('title', '') if link.head_data else '',
            link.head_data.get('meta', {}).get('description', '') if link.head_data else '',
            link.head_data.get('meta', {}).get('keywords', '') if link.head_data else ''
        ])).lower()
        
        if not link_text:
            return 0.0
            
        # Use contextual score if available (from BM25 scoring during crawl)
        # if link.contextual_score is not None:
        if link.contextual_score and link.contextual_score > 0:
            return link.contextual_score
            
        # Otherwise, calculate simple term overlap
        query_terms = set(self._tokenize(state.query.lower()))
        link_terms = set(self._tokenize(link_text))
        
        if not query_terms:
            return 0.0
            
        overlap = len(query_terms & link_terms) / len(query_terms)
        return overlap
    
    def _calculate_novelty(self, link: Link, state: CrawlState) -> float:
        """Estimate how much new information this link might provide"""
        if not state.knowledge_base:
            return 1.0  # First links are maximally novel
            
        # Get terms from link preview
        link_text = ' '.join(filter(None, [
            link.text or '',
            link.title or '',
            link.head_data.get('title', '') if link.head_data else '',
            link.head_data.get('description', '') if link.head_data else '',
            link.head_data.get('keywords', '') if link.head_data else ''
        ])).lower()
        
        link_terms = set(self._tokenize(link_text))
        if not link_terms:
            return 0.5  # Unknown novelty
            
        # Calculate what percentage of link terms are new
        existing_terms = set(state.term_frequencies.keys())
        new_terms = link_terms - existing_terms
        
        novelty = len(new_terms) / len(link_terms) if link_terms else 0.0
        
        return novelty
    
    def _calculate_authority(self, link: Link) -> float:
        """Simple authority score based on URL structure and link attributes"""
        score = 0.5  # Base score
        
        if not link.href:
            return 0.0
            
        url = link.href.lower()
        
        # Positive indicators
        if '/docs/' in url or '/documentation/' in url:
            score += 0.2
        if '/api/' in url or '/reference/' in url:
            score += 0.2
        if '/guide/' in url or '/tutorial/' in url:
            score += 0.1
            
        # Check for file extensions
        if url.endswith('.pdf'):
            score += 0.1
        elif url.endswith(('.jpg', '.png', '.gif')):
            score -= 0.3  # Reduce score for images
            
        # Use intrinsic score if available
        if link.intrinsic_score is not None:
            score = 0.7 * score + 0.3 * link.intrinsic_score
            
        return min(score, 1.0)
    
    async def should_stop(self, state: CrawlState, config: AdaptiveConfig) -> bool:
        """Determine if crawling should stop"""
        # Check confidence threshold
        confidence = state.metrics.get('confidence', 0.0)
        if confidence >= config.confidence_threshold:
            return True
            
        # Check resource limits
        if len(state.crawled_urls) >= config.max_pages:
            return True
            
        # Check if we have any links left
        if not state.pending_links:
            return True
            
        # Check saturation
        if state.metrics.get('saturation', 0.0) >= config.saturation_threshold:
            return True
            
        return False
    
    async def update_state(self, state: CrawlState, new_results: List[CrawlResult]) -> None:
        """Update state with new crawl results"""
        for result in new_results:
            # Track new terms
            old_term_count = len(state.term_frequencies)
            
            # Extract and process content - try multiple fields
            try:
                content = result.markdown.raw_markdown
            except AttributeError:
                print(f"Warning: CrawlResult {result.url} has no markdown content")
                content = ""
            # content = ""
            # if hasattr(result, 'extracted_content') and result.extracted_content:
            #     content = result.extracted_content
            # elif hasattr(result, 'markdown') and result.markdown:
            #     content = result.markdown.raw_markdown
            # elif hasattr(result, 'cleaned_html') and result.cleaned_html:
            #     content = result.cleaned_html
            # elif hasattr(result, 'html') and result.html:
            #     # Use raw HTML as last resort
            #     content = result.html
                
                
            terms = self._tokenize(content.lower())
            
            # Update term frequencies
            term_set = set()
            for term in terms:
                state.term_frequencies[term] += 1
                term_set.add(term)
            
            # Update document frequencies
            doc_id = state.total_documents
            for term in term_set:
                if term not in state.documents_with_terms[term]:
                    state.document_frequencies[term] += 1
                    state.documents_with_terms[term].add(doc_id)
            
            # Track new terms discovered
            new_term_count = len(state.term_frequencies)
            new_terms = new_term_count - old_term_count
            state.new_terms_history.append(new_terms)
            
            # Update document count
            state.total_documents += 1
            
            # Add to crawl order
            state.crawl_order.append(result.url)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - can be enhanced"""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        
        # Filter short tokens and stop words (basic)
        tokens = [t for t in tokens if len(t) > 2]
        
        return tokens
    
    def _get_document_terms(self, crawl_result: CrawlResult) -> List[str]:
        """Extract terms from a crawl result"""
        content = crawl_result.markdown.raw_markdown or ""
        return self._tokenize(content.lower())


class EmbeddingStrategy(CrawlStrategy):
    """Embedding-based adaptive crawling using semantic space coverage"""
    
    def __init__(self, embedding_model: str = None, llm_config: Dict = None):
        self.embedding_model = embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
        self.llm_config = llm_config
        self._embedding_cache = {}
        self._link_embedding_cache = {}  # Cache for link embeddings
        self._validation_passed = False  # Track if validation passed
        
        # Performance optimization caches
        self._distance_matrix_cache = None  # Cache for query-KB distances
        self._kb_embeddings_hash = None  # Track KB changes
        self._validation_embeddings_cache = None  # Cache validation query embeddings
        self._kb_similarity_threshold = 0.95  # Threshold for deduplication
        
    async def _get_embeddings(self, texts: List[str]) -> Any:
        """Get embeddings using configured method"""
        from .utils import get_text_embeddings
        embedding_llm_config = {
            'provider': 'openai/text-embedding-3-small',
            'api_token': os.getenv('OPENAI_API_KEY')
        }
        return await get_text_embeddings(
            texts, 
            embedding_llm_config,
            self.embedding_model
        )
    
    def _compute_distance_matrix(self, query_embeddings: Any, kb_embeddings: Any) -> Any:
        """Compute distance matrix using vectorized operations"""
        import numpy as np
        
        if kb_embeddings is None or len(kb_embeddings) == 0:
            return None
            
        # Ensure proper shapes
        if len(query_embeddings.shape) == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        if len(kb_embeddings.shape) == 1:
            kb_embeddings = kb_embeddings.reshape(1, -1)
            
        # Vectorized cosine distance: 1 - cosine_similarity
        # Normalize vectors
        query_norm = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        kb_norm = kb_embeddings / np.linalg.norm(kb_embeddings, axis=1, keepdims=True)
        
        # Compute cosine similarity matrix
        similarity_matrix = np.dot(query_norm, kb_norm.T)
        
        # Convert to distance
        distance_matrix = 1 - similarity_matrix
        
        return distance_matrix
    
    def _get_cached_distance_matrix(self, query_embeddings: Any, kb_embeddings: Any) -> Any:
        """Get distance matrix with caching"""
        import numpy as np
        
        if kb_embeddings is None or len(kb_embeddings) == 0:
            return None
            
        # Check if KB has changed
        kb_hash = hash(kb_embeddings.tobytes()) if kb_embeddings is not None else None
        
        if (self._distance_matrix_cache is None or 
            kb_hash != self._kb_embeddings_hash):
            # Recompute matrix
            self._distance_matrix_cache = self._compute_distance_matrix(query_embeddings, kb_embeddings)
            self._kb_embeddings_hash = kb_hash
            
        return self._distance_matrix_cache
        
    async def map_query_semantic_space(self, query: str, n_synthetic: int = 10) -> Any:
        """Generate a point cloud representing the semantic neighborhood of the query"""
        from .utils import perform_completion_with_backoff
        
        # Generate more variations than needed for train/val split
        n_total = int(n_synthetic * 1.3)  # Generate 30% more for validation
        
        # Generate variations using LLM
        prompt = f"""Generate {n_total} variations of this query that explore different aspects: '{query}'
        
        These should be queries a user might ask when looking for similar information.
        Include different phrasings, related concepts, and specific aspects.
        
        Return as a JSON array of strings."""
        
        # Use the LLM for query generation
        provider = self.llm_config.get('provider', 'openai/gpt-4o-mini') if self.llm_config else 'openai/gpt-4o-mini'
        api_token = self.llm_config.get('api_token') if self.llm_config else None
        
        # response = perform_completion_with_backoff(
        #     provider=provider,
        #     prompt_with_variables=prompt,
        #     api_token=api_token,
        #     json_response=True
        # )
        
        # variations = json.loads(response.choices[0].message.content)
        
        
        # # Mock data with more variations for split
        variations ={'queries': ['what are the best vegetables to use in fried rice?', 'how do I make vegetable fried rice from scratch?', 'can you provide a quick recipe for vegetable fried rice?', 'what cooking techniques are essential for perfect fried rice with vegetables?', 'how to add flavor to vegetable fried rice?', 'are there any tips for making healthy fried rice with vegetables?']}
        
        
        variations = {'queries': [
            'How do async and await work with coroutines in Python?',
            'What is the role of event loops in asynchronous programming?',
            'Can you explain the differences between async/await and traditional callback methods?',
            'How do coroutines interact with event loops in JavaScript?',
            'What are the benefits of using async await over promises in Node.js?',
            # 'How to manage multiple coroutines with an event loop?',
            # 'What are some common pitfalls when using async await with coroutines?',
            # 'How do different programming languages implement async await and event loops?',
            # 'What happens when an async function is called without await?',
            # 'How does the event loop handle blocking operations?',
            'Can you nest async functions and how does that affect the event loop?',
            'What is the performance impact of using async/await?'
        ]}
        
        # Split into train and validation
        # all_queries = [query] + variations['queries']
        
        # Randomly shuffle for proper train/val split (keeping original query in training)
        import random
        
        # Keep original query always in training
        other_queries = variations['queries'].copy()
        random.shuffle(other_queries)
        
        # Split: 80% for training, 20% for validation
        n_validation = max(2, int(len(other_queries) * 0.2))  # At least 2 for validation
        val_queries = other_queries[-n_validation:]
        train_queries = [query] + other_queries[:-n_validation]
        
        # Embed only training queries for now (faster)
        train_embeddings = await self._get_embeddings(train_queries)
        
        # Store validation queries for later (don't embed yet to save time)
        self._validation_queries = val_queries
        
        return train_embeddings, train_queries
    
    def compute_coverage_shape(self, query_points: Any, alpha: float = 0.5):
        """Find the minimal shape that covers all query points using alpha shape"""
        try:
            import numpy as np
            
            if len(query_points) < 3:
                return None
            
            # For high-dimensional embeddings (e.g., 384-dim, 768-dim), 
            # alpha shapes require exponentially more points than available.
            # Instead, use a statistical coverage model
            query_points = np.array(query_points)
            
            # Store coverage as centroid + radius model
            coverage = {
                'center': np.mean(query_points, axis=0),
                'std': np.std(query_points, axis=0),
                'points': query_points,
                'radius': np.max(np.linalg.norm(query_points - np.mean(query_points, axis=0), axis=1))
            }
            return coverage
        except Exception:
            # Fallback if computation fails
            return None
    
    def _sample_boundary_points(self, shape, n_samples: int = 20) -> List[Any]:
        """Sample points from the boundary of a shape"""
        import numpy as np
        
        # Simplified implementation - in practice would sample from actual shape boundary
        # For now, return empty list if shape is None
        if shape is None:
            return []
        
        # This is a placeholder - actual implementation would depend on shape type
        return []
        
    def find_coverage_gaps(self, kb_embeddings: Any, query_embeddings: Any) -> List[Tuple[Any, float]]:
        """Calculate gap distances for all query variations using vectorized operations"""
        import numpy as np
        
        gaps = []
        
        if kb_embeddings is None or len(kb_embeddings) == 0:
            # If no KB yet, all query points have maximum gap
            for q_emb in query_embeddings:
                gaps.append((q_emb, 1.0))
            return gaps
        
        # Use cached distance matrix
        distance_matrix = self._get_cached_distance_matrix(query_embeddings, kb_embeddings)
        
        if distance_matrix is None:
            # Fallback
            for q_emb in query_embeddings:
                gaps.append((q_emb, 1.0))
            return gaps
            
        # Find minimum distance for each query (vectorized)
        min_distances = np.min(distance_matrix, axis=1)
        
        # Create gaps list
        for i, q_emb in enumerate(query_embeddings):
            gaps.append((q_emb, min_distances[i]))
                
        return gaps
        
    async def select_links_for_expansion(
        self, 
        candidate_links: List[Link], 
        gaps: List[Tuple[Any, float]], 
        kb_embeddings: Any
    ) -> List[Tuple[Link, float]]:
        """Select links that most efficiently fill the gaps"""
        from .utils import cosine_distance, cosine_similarity, get_text_embeddings
        import numpy as np
        import hashlib
        
        scored_links = []
        
        # Prepare for embedding - separate cached vs uncached
        links_to_embed = []
        texts_to_embed = []
        link_embeddings_map = {}
        
        for link in candidate_links:
            # Extract text from link
            link_text = ' '.join(filter(None, [
                link.text or '',
                link.title or '',
                link.meta.get('description', '') if hasattr(link, 'meta') and link.meta else '',
                link.head_data.get('meta', {}).get('description', '') if link.head_data else ''
            ]))
            
            if not link_text.strip():
                continue
            
            # Create cache key from URL + text content
            cache_key = hashlib.md5(f"{link.href}:{link_text}".encode()).hexdigest()
            
            # Check cache
            if cache_key in self._link_embedding_cache:
                link_embeddings_map[link.href] = self._link_embedding_cache[cache_key]
            else:
                links_to_embed.append(link)
                texts_to_embed.append(link_text)
        
        # Batch embed only uncached links
        if texts_to_embed:
            embedding_llm_config = {
                'provider': 'openai/text-embedding-3-small',
                'api_token': os.getenv('OPENAI_API_KEY')
            }
            new_embeddings = await get_text_embeddings(texts_to_embed, embedding_llm_config, self.embedding_model)

            # Cache the new embeddings
            for link, text, embedding in zip(links_to_embed, texts_to_embed, new_embeddings):
                cache_key = hashlib.md5(f"{link.href}:{text}".encode()).hexdigest()
                self._link_embedding_cache[cache_key] = embedding
                link_embeddings_map[link.href] = embedding
        
        # Get coverage radius from config
        coverage_radius = self.config.embedding_coverage_radius if hasattr(self, 'config') else 0.2
        
        # Score each link
        for link in candidate_links:
            if link.href not in link_embeddings_map:
                continue  # Skip links without embeddings
                
            link_embedding = link_embeddings_map[link.href]
            
            if not gaps:
                score = 0.0
            else:
                # Calculate how many gaps this link helps with
                gaps_helped = 0
                total_improvement = 0
                
                for gap_point, gap_distance in gaps:
                    # Only consider gaps that actually need filling (outside coverage radius)
                    if gap_distance > coverage_radius:
                        new_distance = cosine_distance(link_embedding, gap_point)
                        if new_distance < gap_distance:
                            # This link helps this gap
                            improvement = gap_distance - new_distance
                            # Scale improvement - moving from 0.5 to 0.3 is valuable
                            scaled_improvement = improvement * 2  # Amplify the signal
                            total_improvement += scaled_improvement
                            gaps_helped += 1
                
                # Average improvement per gap that needs help
                gaps_needing_help = sum(1 for _, d in gaps if d > coverage_radius)
                if gaps_needing_help > 0:
                    gap_reduction_score = total_improvement / gaps_needing_help
                else:
                    gap_reduction_score = 0
                
                # Check overlap with existing KB (vectorized)
                if kb_embeddings is not None and len(kb_embeddings) > 0:
                    # Normalize embeddings
                    link_norm = link_embedding / np.linalg.norm(link_embedding)
                    kb_norm = kb_embeddings / np.linalg.norm(kb_embeddings, axis=1, keepdims=True)
                    
                    # Compute all similarities at once
                    similarities = np.dot(kb_norm, link_norm)
                    max_similarity = np.max(similarities)
                    
                    # Only penalize if very similar (above threshold)
                    overlap_threshold = self.config.embedding_overlap_threshold if hasattr(self, 'config') else 0.85
                    if max_similarity > overlap_threshold:
                        overlap_penalty = (max_similarity - overlap_threshold) * 2  # 0 to 0.3 range
                    else:
                        overlap_penalty = 0
                else:
                    overlap_penalty = 0
                
                # Final score - emphasize gap reduction
                score = gap_reduction_score * (1 - overlap_penalty)
                
                # Add contextual score boost if available
                if hasattr(link, 'contextual_score') and link.contextual_score:
                    score = score * 0.8 + link.contextual_score * 0.2
            
            scored_links.append((link, score))
            
        return sorted(scored_links, key=lambda x: x[1], reverse=True)

    async def calculate_confidence(self, state: CrawlState) -> float:
        """Coverage-based learning score (0–1)."""
        import numpy as np

        # Guard clauses
        if state.kb_embeddings is None or state.query_embeddings is None:
            return 0.0
        if len(state.kb_embeddings) == 0 or len(state.query_embeddings) == 0:
            return 0.0

        # Prepare L2-normalised arrays
        Q = np.asarray(state.query_embeddings, dtype=np.float32)
        D = np.asarray(state.kb_embeddings, dtype=np.float32)
        Q /= np.linalg.norm(Q, axis=1, keepdims=True) + 1e-8
        D /= np.linalg.norm(D, axis=1, keepdims=True) + 1e-8

        # Best cosine per query
        best = (Q @ D.T).max(axis=1)

        # Mean similarity or hit-rate above tau
        tau = getattr(self.config, 'coverage_tau', None)
        score = float((best >= tau).mean()) if tau is not None else float(best.mean())

        # Store quick metrics
        state.metrics['coverage_score'] = score
        state.metrics['avg_best_similarity'] = float(best.mean())
        state.metrics['median_best_similarity'] = float(np.median(best))

        return score


    
    # async def calculate_confidence(self, state: CrawlState) -> float:
    #     """Calculate learning score for adaptive crawling (used for stopping)"""
    #     import numpy as np
        
    #     if state.kb_embeddings is None or state.query_embeddings is None:
    #         return 0.0
        
    #     if len(state.kb_embeddings) == 0:
    #         return 0.0
            
    #     # Get cached distance matrix
    #     distance_matrix = self._get_cached_distance_matrix(state.query_embeddings, state.kb_embeddings)
        
    #     if distance_matrix is None:
    #         return 0.0
            
    #     # Vectorized analysis for all queries at once
    #     all_query_metrics = []
        
    #     for i in range(len(state.query_embeddings)):
    #         # Get distances for this query
    #         distances = distance_matrix[i]
    #         sorted_distances = np.sort(distances)
            
    #         # Store metrics for this query
    #         query_metric = {
    #             'min_distance': sorted_distances[0],
    #             'top_3_distances': sorted_distances[:3],
    #             'top_5_distances': sorted_distances[:5],
    #             'close_neighbors': np.sum(distances < 0.3),
    #             'very_close_neighbors': np.sum(distances < 0.2),
    #             'all_distances': distances
    #         }
    #         all_query_metrics.append(query_metric)
        
    #     # Hybrid approach with density (exponential base)
    #     k_exp = self.config.embedding_k_exp if hasattr(self, 'config') else 1.0
    #     coverage_scores_hybrid_exp = []
        
    #     for metric in all_query_metrics:
    #         # Base score from nearest neighbor
    #         nearest_score = np.exp(-k_exp * metric['min_distance'])
            
    #         # Top-k average (top 3)
    #         top_k = min(3, len(metric['all_distances']))
    #         top_k_avg = np.mean([np.exp(-k_exp * d) for d in metric['top_3_distances'][:top_k]])
            
    #         # Combine using configured weights
    #         nearest_weight = self.config.embedding_nearest_weight if hasattr(self, 'config') else 0.7
    #         top_k_weight = self.config.embedding_top_k_weight if hasattr(self, 'config') else 0.3
    #         hybrid_score = nearest_weight * nearest_score + top_k_weight * top_k_avg
    #         coverage_scores_hybrid_exp.append(hybrid_score)
        
    #     learning_score = np.mean(coverage_scores_hybrid_exp)
        
    #     # Store as learning score
    #     state.metrics['learning_score'] = learning_score
        
    #     # Store embedding-specific metrics
    #     state.metrics['avg_min_distance'] = np.mean([m['min_distance'] for m in all_query_metrics])
    #     state.metrics['avg_close_neighbors'] = np.mean([m['close_neighbors'] for m in all_query_metrics])
    #     state.metrics['avg_very_close_neighbors'] = np.mean([m['very_close_neighbors'] for m in all_query_metrics])
    #     state.metrics['total_kb_docs'] = len(state.kb_embeddings)
        
    #     # Store query-level metrics for detailed analysis
    #     self._query_metrics = all_query_metrics
        
    #     # For stopping criteria, return learning score
    #     return float(learning_score)
        
    async def rank_links(self, state: CrawlState, config: AdaptiveConfig) -> List[Tuple[Link, float]]:
        """Main entry point for link ranking"""
        # Store config for use in other methods
        self.config = config
        
        # Filter out already crawled URLs and remove duplicates
        seen_urls = set()
        uncrawled_links = []
        
        for link in state.pending_links:
            if link.href not in state.crawled_urls and link.href not in seen_urls:
                uncrawled_links.append(link)
                seen_urls.add(link.href)
        
        if not uncrawled_links:
            return []
        
        # Get gaps in coverage (no threshold needed anymore)
        gaps = self.find_coverage_gaps(
            state.kb_embeddings, 
            state.query_embeddings
        )
        state.semantic_gaps = [(g[0].tolist(), g[1]) for g in gaps]  # Store as list for serialization
        
        # Select links that fill gaps (only from uncrawled)
        return await self.select_links_for_expansion(
            uncrawled_links,
            gaps,
            state.kb_embeddings
        )
        
    async def validate_coverage(self, state: CrawlState) -> float:
        """Validate coverage using held-out queries with caching"""
        if not hasattr(self, '_validation_queries') or not self._validation_queries:
            return state.metrics.get('confidence', 0.0)
        
        import numpy as np
        
        # Cache validation embeddings (only embed once!)
        if self._validation_embeddings_cache is None:
            self._validation_embeddings_cache = await self._get_embeddings(self._validation_queries)
        
        val_embeddings = self._validation_embeddings_cache
        
        # Use vectorized distance computation
        if state.kb_embeddings is None or len(state.kb_embeddings) == 0:
            return 0.0
            
        # Compute distance matrix for validation queries
        distance_matrix = self._compute_distance_matrix(val_embeddings, state.kb_embeddings)
        
        if distance_matrix is None:
            return 0.0
            
        # Find minimum distance for each validation query (vectorized)
        min_distances = np.min(distance_matrix, axis=1)
        
        # Compute scores using same exponential as training
        k_exp = self.config.embedding_k_exp if hasattr(self, 'config') else 1.0
        scores = np.exp(-k_exp * min_distances)
        
        validation_confidence = np.mean(scores)
        state.metrics['validation_confidence'] = validation_confidence
        
        return validation_confidence
    
    async def should_stop(self, state: CrawlState, config: AdaptiveConfig) -> bool:
        """Stop based on learning curve convergence"""
        confidence = state.metrics.get('confidence', 0.0)
        
        # Basic limits
        if len(state.crawled_urls) >= config.max_pages or not state.pending_links:
            return True
        
        # Track confidence history
        if not hasattr(state, 'confidence_history'):
            state.confidence_history = []
        
        state.confidence_history.append(confidence)
        
        # Need at least 3 iterations to check convergence
        if len(state.confidence_history) < 2:
            return False
        
        improvement_diffs = list(zip(state.confidence_history[:-1], state.confidence_history[1:]))
                    
        # Calculate average improvement
        avg_improvement = sum(abs(b - a) for a, b in improvement_diffs) / len(improvement_diffs)
        state.metrics['avg_improvement'] = avg_improvement

        min_relative_improvement = self.config.embedding_min_relative_improvement * confidence if hasattr(self, 'config') else 0.1 * confidence
        if avg_improvement < min_relative_improvement:
            # Converged - validate before stopping
            val_score = await self.validate_coverage(state)
            
            # Only stop if validation is reasonable
            validation_min = self.config.embedding_validation_min_score if hasattr(self, 'config') else 0.4
            if val_score > validation_min:
                state.metrics['stopped_reason'] = 'converged_validated'
                self._validation_passed = True
                return True
            else:
                state.metrics['stopped_reason'] = 'low_validation'
                # Continue crawling despite convergence
        
        return False
        
    def get_quality_confidence(self, state: CrawlState) -> float:
        """Calculate quality-based confidence score for display"""
        learning_score = state.metrics.get('learning_score', 0.0)
        validation_score = state.metrics.get('validation_confidence', 0.0)
        
        # Get config values
        validation_min = self.config.embedding_validation_min_score if hasattr(self, 'config') else 0.4
        quality_min = self.config.embedding_quality_min_confidence if hasattr(self, 'config') else 0.7
        quality_max = self.config.embedding_quality_max_confidence if hasattr(self, 'config') else 0.95
        scale_factor = self.config.embedding_quality_scale_factor if hasattr(self, 'config') else 0.833
        
        if self._validation_passed and validation_score > validation_min:
            # Validated systems get boosted scores
            # Map 0.4-0.7 learning → quality_min-quality_max confidence
            if learning_score < 0.4:
                confidence = quality_min  # Minimum for validated systems
            elif learning_score > 0.7:
                confidence = quality_max  # Maximum realistic confidence
            else:
                # Linear mapping in between
                confidence = quality_min + (learning_score - 0.4) * scale_factor
        else:
            # Not validated = conservative mapping
            confidence = learning_score * 0.8
            
        return confidence
    
    async def update_state(self, state: CrawlState, new_results: List[CrawlResult]) -> None:
        """Update embeddings and coverage metrics with deduplication"""
        from .utils import get_text_embeddings
        import numpy as np
        
        # Extract text from results
        new_texts = []
        valid_results = []
        for result in new_results:
            content = result.markdown.raw_markdown if hasattr(result, 'markdown') and result.markdown else ""
            if content:  # Only process non-empty content
                new_texts.append(content[:5000])  # Limit text length
                valid_results.append(result)
            
        if not new_texts:
            return
            
        # Get embeddings for new texts
        embedding_llm_config = {
            'provider': 'openai/text-embedding-3-small',
            'api_token': os.getenv('OPENAI_API_KEY')
        }        
        new_embeddings = await get_text_embeddings(new_texts, embedding_llm_config, self.embedding_model)

        # Deduplicate embeddings before adding to KB
        if state.kb_embeddings is None:
            # First batch - no deduplication needed
            state.kb_embeddings = new_embeddings
            deduplicated_indices = list(range(len(new_embeddings)))
        else:
            # Check for duplicates using vectorized similarity
            deduplicated_embeddings = []
            deduplicated_indices = []
            
            for i, new_emb in enumerate(new_embeddings):
                # Compute similarities with existing KB
                new_emb_normalized = new_emb / np.linalg.norm(new_emb)
                kb_normalized = state.kb_embeddings / np.linalg.norm(state.kb_embeddings, axis=1, keepdims=True)
                similarities = np.dot(kb_normalized, new_emb_normalized)
                
                # Only add if not too similar to existing content
                if np.max(similarities) < self._kb_similarity_threshold:
                    deduplicated_embeddings.append(new_emb)
                    deduplicated_indices.append(i)
            
            # Add deduplicated embeddings
            if deduplicated_embeddings:
                state.kb_embeddings = np.vstack([state.kb_embeddings, np.array(deduplicated_embeddings)])
        
        # Update crawl order only for non-duplicate results
        for idx in deduplicated_indices:
            state.crawl_order.append(valid_results[idx].url)
        
        # Invalidate distance matrix cache since KB changed
        self._kb_embeddings_hash = None
        self._distance_matrix_cache = None
            
        # Update coverage shape if needed
        if hasattr(state, 'query_embeddings') and state.query_embeddings is not None:
            state.coverage_shape = self.compute_coverage_shape(state.query_embeddings, self.config.alpha_shape_alpha if hasattr(self, 'config') else 0.5)


class AdaptiveCrawler:
    """Main adaptive crawler that orchestrates the crawling process"""
    
    def __init__(self, 
                 crawler: Optional[AsyncWebCrawler] = None,
                 config: Optional[AdaptiveConfig] = None,
                 strategy: Optional[CrawlStrategy] = None):
        self.crawler = crawler
        self.config = config or AdaptiveConfig()
        self.config.validate()
        
        # Create strategy based on config
        if strategy:
            self.strategy = strategy
        else:
            self.strategy = self._create_strategy(self.config.strategy)
        
        # Initialize state
        self.state: Optional[CrawlState] = None
        
        # Track if we own the crawler (for cleanup)
        self._owns_crawler = crawler is None
    
    def _create_strategy(self, strategy_name: str) -> CrawlStrategy:
        """Create strategy instance based on name"""
        if strategy_name == "statistical":
            return StatisticalStrategy()
        elif strategy_name == "embedding":
            return EmbeddingStrategy(
                embedding_model=self.config.embedding_model,
                llm_config=self.config.embedding_llm_config
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
    
    async def digest(self, 
                               start_url: str, 
                               query: str,
                               resume_from: Optional[str] = None) -> CrawlState:
        """Main entry point for adaptive crawling"""
        # Initialize or resume state
        if resume_from:
            self.state = CrawlState.load(resume_from)
            self.state.query = query  # Update query in case it changed
        else:
            self.state = CrawlState(
                crawled_urls=set(),
                knowledge_base=[],
                pending_links=[],
                query=query,
                metrics={}
            )
        
        # Create crawler if needed
        if not self.crawler:
            self.crawler = AsyncWebCrawler()
            await self.crawler.__aenter__()
            
        self.strategy.config = self.config  # Pass config to strategy
        
        # If using embedding strategy and not resuming, expand query space
        if isinstance(self.strategy, EmbeddingStrategy) and not resume_from:
            # Generate query space
            query_embeddings, expanded_queries = await self.strategy.map_query_semantic_space(
                query, 
                self.config.n_query_variations
            )
            self.state.query_embeddings = query_embeddings
            self.state.expanded_queries = expanded_queries[1:]  # Skip original query
            self.state.embedding_model = self.strategy.embedding_model
        
        try:
            # Initial crawl if not resuming
            if start_url not in self.state.crawled_urls:
                result = await self._crawl_with_preview(start_url, query)
                if result and hasattr(result, 'success') and result.success:
                    self.state.knowledge_base.append(result)
                    self.state.crawled_urls.add(start_url)
                    # Extract links from result - handle both dict and Links object formats
                    if hasattr(result, 'links') and result.links:
                        if isinstance(result.links, dict):
                            # Extract internal and external links from dict
                            internal_links = [Link(**link) for link in result.links.get('internal', [])]
                            external_links = [Link(**link) for link in result.links.get('external', [])]
                            self.state.pending_links.extend(internal_links + external_links)
                        else:
                            # Handle Links object
                            self.state.pending_links.extend(result.links.internal + result.links.external)
                    
                    # Update state
                    await self.strategy.update_state(self.state, [result])
            
            # adaptive expansion
            depth = 0
            while depth < self.config.max_depth:
                # Calculate confidence
                confidence = await self.strategy.calculate_confidence(self.state)
                self.state.metrics['confidence'] = confidence
                
                # Check stopping criteria
                if await self.strategy.should_stop(self.state, self.config):
                    break
                
                # Rank candidate links
                ranked_links = await self.strategy.rank_links(self.state, self.config)
                
                if not ranked_links:
                    break
                
                # Check minimum gain threshold
                if ranked_links[0][1] < self.config.min_gain_threshold:
                    break
                
                # Select top K links
                to_crawl = [(link, score) for link, score in ranked_links[:self.config.top_k_links]
                           if link.href not in self.state.crawled_urls]
                
                if not to_crawl:
                    break
                
                # Crawl selected links
                new_results = await self._crawl_batch(to_crawl, query)
                
                if new_results:
                    # Update knowledge base
                    self.state.knowledge_base.extend(new_results)
                    
                    # Update crawled URLs and pending links
                    for result, (link, _) in zip(new_results, to_crawl):
                        if result:
                            self.state.crawled_urls.add(link.href)
                            # Extract links from result - handle both dict and Links object formats
                            if hasattr(result, 'links') and result.links:
                                new_links = []
                                if isinstance(result.links, dict):
                                    # Extract internal and external links from dict
                                    internal_links = [Link(**link_data) for link_data in result.links.get('internal', [])]
                                    external_links = [Link(**link_data) for link_data in result.links.get('external', [])]
                                    new_links = internal_links + external_links
                                else:
                                    # Handle Links object
                                    new_links = result.links.internal + result.links.external
                                
                                # Add new links to pending
                                for new_link in new_links:
                                    if new_link.href not in self.state.crawled_urls:
                                        self.state.pending_links.append(new_link)
                    
                    # Update state with new results
                    await self.strategy.update_state(self.state, new_results)
                
                depth += 1
                
                # Save state if configured
                if self.config.save_state and self.config.state_path:
                    self.state.save(self.config.state_path)
            
            # Final confidence calculation
            learning_score = await self.strategy.calculate_confidence(self.state)
            
            # For embedding strategy, get quality-based confidence
            if isinstance(self.strategy, EmbeddingStrategy):
                self.state.metrics['confidence'] = self.strategy.get_quality_confidence(self.state)
            else:
                # For statistical strategy, use the same as before
                self.state.metrics['confidence'] = learning_score
                
            self.state.metrics['pages_crawled'] = len(self.state.crawled_urls)
            self.state.metrics['depth_reached'] = depth
            
            # Final save
            if self.config.save_state and self.config.state_path:
                self.state.save(self.config.state_path)
            
            return self.state
            
        finally:
            # Cleanup if we created the crawler
            if self._owns_crawler and self.crawler:
                await self.crawler.__aexit__(None, None, None)
    
    async def _crawl_with_preview(self, url: str, query: str) -> Optional[CrawlResult]:
        """Crawl a URL with link preview enabled"""
        config = CrawlerRunConfig(
            link_preview_config=LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                query=query,  # For BM25 scoring
                concurrency=5,
                timeout=5,
                max_links=50,  # Reasonable limit
                verbose=False
            ),
            score_links=True  # Enable intrinsic scoring
        )
        
        try:
            result = await self.crawler.arun(url=url, config=config)
            # Extract the actual CrawlResult from the container
            if hasattr(result, '_results') and result._results:
                result = result._results[0]

            # Filter our all links do not have head_date
            if hasattr(result, 'links') and result.links:
                result.links['internal'] = [link for link in result.links['internal'] if link.get('head_data')]
                # For now let's ignore external links without head_data
                # result.links['external'] = [link for link in result.links['external'] if link.get('head_data')]

            return result
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
    
    async def _crawl_batch(self, links_with_scores: List[Tuple[Link, float]], query: str) -> List[CrawlResult]:
        """Crawl multiple URLs in parallel"""
        tasks = []
        for link, score in links_with_scores:
            task = self._crawl_with_preview(link.href, query)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and failed crawls
        valid_results = []
        for result in results:
            if isinstance(result, CrawlResult):
                # Only include successful crawls
                if hasattr(result, 'success') and result.success:
                    valid_results.append(result)
                else:
                    print(f"Skipping failed crawl: {result.url if hasattr(result, 'url') else 'unknown'}")
            elif isinstance(result, Exception):
                print(f"Error in batch crawl: {result}")
        
        return valid_results
    
    # Status properties
    @property
    def confidence(self) -> float:
        """Current confidence level"""
        if self.state:
            return self.state.metrics.get('confidence', 0.0)
        return 0.0
    
    @property
    def coverage_stats(self) -> Dict[str, Any]:
        """Detailed coverage statistics"""
        if not self.state:
            return {}
        
        total_content_length = sum(
            len(result.markdown.raw_markdown or "") 
            for result in self.state.knowledge_base
        )
        
        return {
            'pages_crawled': len(self.state.crawled_urls),
            'total_content_length': total_content_length,
            'unique_terms': len(self.state.term_frequencies),
            'total_terms': sum(self.state.term_frequencies.values()),
            'pending_links': len(self.state.pending_links),
            'confidence': self.confidence,
            'coverage': self.state.metrics.get('coverage', 0.0),
            'consistency': self.state.metrics.get('consistency', 0.0),
            'saturation': self.state.metrics.get('saturation', 0.0)
        }
    
    @property
    def is_sufficient(self) -> bool:
        """Check if current knowledge is sufficient"""
        if isinstance(self.strategy, EmbeddingStrategy):
            # For embedding strategy, sufficient = validation passed
            return self.strategy._validation_passed
        else:
            # For statistical strategy, use threshold
            return self.confidence >= self.config.confidence_threshold
    
    def print_stats(self, detailed: bool = False) -> None:
        """Print comprehensive statistics about the knowledge base
        
        Args:
            detailed: If True, show detailed statistics including top terms
        """
        if not self.state:
            print("No crawling state available.")
            return
        
        # Import here to avoid circular imports
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            use_rich = True
        except ImportError:
            use_rich = False
            
        if not detailed and use_rich:
            # Summary view with nice table (like original)
            table = Table(title=f"Adaptive Crawl Stats - Query: '{self.state.query}'")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")
            
            # Basic stats
            stats = self.coverage_stats
            table.add_row("Pages Crawled", str(stats.get('pages_crawled', 0)))
            table.add_row("Unique Terms", str(stats.get('unique_terms', 0)))
            table.add_row("Total Terms", str(stats.get('total_terms', 0)))
            table.add_row("Content Length", f"{stats.get('total_content_length', 0):,} chars")
            table.add_row("Pending Links", str(stats.get('pending_links', 0)))
            table.add_row("", "")  # Spacer
            
            # Strategy-specific metrics
            if isinstance(self.strategy, EmbeddingStrategy):
                # Embedding-specific metrics
                table.add_row("Confidence", f"{stats.get('confidence', 0):.2%}")
                table.add_row("Avg Min Distance", f"{self.state.metrics.get('avg_min_distance', 0):.3f}")
                table.add_row("Avg Close Neighbors", f"{self.state.metrics.get('avg_close_neighbors', 0):.1f}")
                table.add_row("Validation Score", f"{self.state.metrics.get('validation_confidence', 0):.2%}")
                table.add_row("", "")  # Spacer
                table.add_row("Is Sufficient?", "[green]Yes (Validated)[/green]" if self.is_sufficient else "[red]No[/red]")
            else:
                # Statistical strategy metrics
                table.add_row("Confidence", f"{stats.get('confidence', 0):.2%}")
                table.add_row("Coverage", f"{stats.get('coverage', 0):.2%}")
                table.add_row("Consistency", f"{stats.get('consistency', 0):.2%}")
                table.add_row("Saturation", f"{stats.get('saturation', 0):.2%}")
                table.add_row("", "")  # Spacer
                table.add_row("Is Sufficient?", "[green]Yes[/green]" if self.is_sufficient else "[red]No[/red]")
            
            console.print(table)
        else:
            # Detailed view or fallback when rich not available
            print("\n" + "="*80)
            print(f"Adaptive Crawl Statistics - Query: '{self.state.query}'")
            print("="*80)
            
            # Basic stats
            print("\n[*] Basic Statistics:")
            print(f"  Pages Crawled: {len(self.state.crawled_urls)}")
            print(f"  Pending Links: {len(self.state.pending_links)}")
            print(f"  Total Documents: {self.state.total_documents}")
            
            # Content stats
            total_content_length = sum(
                len(self._get_content_from_result(result))
                for result in self.state.knowledge_base
            )
            total_words = sum(self.state.term_frequencies.values())
            unique_terms = len(self.state.term_frequencies)
            
            print(f"\n[*] Content Statistics:")
            print(f"  Total Content: {total_content_length:,} characters")
            print(f"  Total Words: {total_words:,}")
            print(f"  Unique Terms: {unique_terms:,}")
            if total_words > 0:
                print(f"  Vocabulary Richness: {unique_terms/total_words:.2%}")
            
            # Strategy-specific output
            if isinstance(self.strategy, EmbeddingStrategy):
                # Semantic coverage for embedding strategy
                print(f"\n[*] Semantic Coverage Analysis:")
                print(f"  Average Min Distance: {self.state.metrics.get('avg_min_distance', 0):.3f}")
                print(f"  Avg Close Neighbors (< 0.3): {self.state.metrics.get('avg_close_neighbors', 0):.1f}")
                print(f"  Avg Very Close Neighbors (< 0.2): {self.state.metrics.get('avg_very_close_neighbors', 0):.1f}")
                
                # Confidence metrics
                print(f"\n[*] Confidence Metrics:")
                if self.is_sufficient:
                    if use_rich:
                        console.print(f"  Overall Confidence: {self.confidence:.2%} [green][VALIDATED][/green]")
                    else:
                        print(f"  Overall Confidence: {self.confidence:.2%} [VALIDATED]")
                else:
                    if use_rich:
                        console.print(f"  Overall Confidence: {self.confidence:.2%} [red][NOT VALIDATED][/red]")
                    else:
                        print(f"  Overall Confidence: {self.confidence:.2%} [NOT VALIDATED]")
                        
                print(f"  Learning Score: {self.state.metrics.get('learning_score', 0):.2%}")
                print(f"  Validation Score: {self.state.metrics.get('validation_confidence', 0):.2%}")
                
            else:
                # Query coverage for statistical strategy
                print(f"\n[*] Query Coverage:")
                query_terms = self.strategy._tokenize(self.state.query.lower())
                for term in query_terms:
                    tf = self.state.term_frequencies.get(term, 0)
                    df = self.state.document_frequencies.get(term, 0)
                    if df > 0:
                        if use_rich:
                            console.print(f"  '{term}': found in {df}/{self.state.total_documents} docs ([green]{df/self.state.total_documents:.0%}[/green]), {tf} occurrences")
                        else:
                            print(f"  '{term}': found in {df}/{self.state.total_documents} docs ({df/self.state.total_documents:.0%}), {tf} occurrences")
                    else:
                        if use_rich:
                            console.print(f"  '{term}': [red][X] not found[/red]")
                        else:
                            print(f"  '{term}': [X] not found")
                
                # Confidence metrics
                print(f"\n[*] Confidence Metrics:")
                status = "[OK]" if self.is_sufficient else "[!!]"
                if use_rich:
                    status_colored = "[green][OK][/green]" if self.is_sufficient else "[red][!!][/red]"
                    console.print(f"  Overall Confidence: {self.confidence:.2%} {status_colored}")
                else:
                    print(f"  Overall Confidence: {self.confidence:.2%} {status}")
                print(f"  Coverage Score: {self.state.metrics.get('coverage', 0):.2%}")
                print(f"  Consistency Score: {self.state.metrics.get('consistency', 0):.2%}")
                print(f"  Saturation Score: {self.state.metrics.get('saturation', 0):.2%}")
            
            # Crawl efficiency
            if self.state.new_terms_history:
                avg_new_terms = sum(self.state.new_terms_history) / len(self.state.new_terms_history)
                print(f"\n[*] Crawl Efficiency:")
                print(f"  Avg New Terms per Page: {avg_new_terms:.1f}")
                print(f"  Information Saturation: {self.state.metrics.get('saturation', 0):.2%}")
                
            if detailed:
                print("\n" + "-"*80)
                if use_rich:
                    console.print("[bold cyan]DETAILED STATISTICS[/bold cyan]")
                else:
                    print("DETAILED STATISTICS")
                print("-"*80)
                
                # Top terms
                print("\n[+] Top 20 Terms by Frequency:")
                top_terms = sorted(self.state.term_frequencies.items(), key=lambda x: x[1], reverse=True)[:20]
                for i, (term, freq) in enumerate(top_terms, 1):
                    df = self.state.document_frequencies.get(term, 0)
                    if use_rich:
                        console.print(f"  {i:2d}. [yellow]'{term}'[/yellow]: {freq} occurrences in {df} docs")
                    else:
                        print(f"  {i:2d}. '{term}': {freq} occurrences in {df} docs")
                
                # URLs crawled
                print(f"\n[+] URLs Crawled ({len(self.state.crawled_urls)}):")
                for i, url in enumerate(self.state.crawl_order, 1):
                    new_terms = self.state.new_terms_history[i-1] if i <= len(self.state.new_terms_history) else 0
                    if use_rich:
                        console.print(f"  {i}. [cyan]{url}[/cyan]")
                        console.print(f"     -> Added [green]{new_terms}[/green] new terms")
                    else:
                        print(f"  {i}. {url}")
                        print(f"     -> Added {new_terms} new terms")
                
                # Document frequency distribution
                print("\n[+] Document Frequency Distribution:")
                df_counts = {}
                for df in self.state.document_frequencies.values():
                    df_counts[df] = df_counts.get(df, 0) + 1
                
                for df in sorted(df_counts.keys()):
                    count = df_counts[df]
                    print(f"  Terms in {df} docs: {count} terms")
                
                # Embedding stats
                if self.state.embedding_model:
                    print("\n[+] Semantic Coverage Analysis:")
                    print(f"  Embedding Model: {self.state.embedding_model}")
                    print(f"  Query Variations: {len(self.state.expanded_queries)}")
                    if self.state.kb_embeddings is not None:
                        print(f"  Knowledge Embeddings: {self.state.kb_embeddings.shape}")
                    else:
                        print(f"  Knowledge Embeddings: None")
                    print(f"  Semantic Gaps: {len(self.state.semantic_gaps)}")
                    print(f"  Coverage Achievement: {self.confidence:.2%}")
                    
                    # Show sample expanded queries
                    if self.state.expanded_queries:
                        print("\n[+] Query Space (samples):")
                        for i, eq in enumerate(self.state.expanded_queries[:5], 1):
                            if use_rich:
                                console.print(f"  {i}. [yellow]{eq}[/yellow]")
                            else:
                                print(f"  {i}. {eq}")
            
            print("\n" + "="*80)
    
    def _get_content_from_result(self, result) -> str:
        """Helper to safely extract content from result"""
        if hasattr(result, 'markdown') and result.markdown:
            if hasattr(result.markdown, 'raw_markdown'):
                return result.markdown.raw_markdown or ""
            return str(result.markdown)
        return ""
    
    def export_knowledge_base(self, filepath: Union[str, Path], format: str = "jsonl") -> None:
        """Export the knowledge base to a file
        
        Args:
            filepath: Path to save the file
            format: Export format - currently supports 'jsonl'
        """
        if not self.state or not self.state.knowledge_base:
            print("No knowledge base to export.")
            return
            
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "jsonl":
            # Export as JSONL - one CrawlResult per line
            with open(filepath, 'w', encoding='utf-8') as f:
                for result in self.state.knowledge_base:
                    # Convert CrawlResult to dict
                    result_dict = self._crawl_result_to_export_dict(result)
                    # Write as single line JSON
                    f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')
            
            print(f"Exported {len(self.state.knowledge_base)} documents to {filepath}")
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _crawl_result_to_export_dict(self, result) -> Dict[str, Any]:
        """Convert CrawlResult to a dictionary for export"""
        # Extract all available fields
        export_dict = {
            'url': getattr(result, 'url', ''),
            'timestamp': getattr(result, 'timestamp', None),
            'success': getattr(result, 'success', True),
            'query': self.state.query if self.state else '',
        }
        
        # Extract content
        if hasattr(result, 'markdown') and result.markdown:
            if hasattr(result.markdown, 'raw_markdown'):
                export_dict['content'] = result.markdown.raw_markdown
            else:
                export_dict['content'] = str(result.markdown)
        else:
            export_dict['content'] = ''
        
        # Extract metadata
        if hasattr(result, 'metadata'):
            export_dict['metadata'] = result.metadata
        
        # Extract links if available
        if hasattr(result, 'links'):
            export_dict['links'] = result.links
        
        # Add crawl-specific metadata
        if self.state:
            export_dict['crawl_metadata'] = {
                'crawl_order': self.state.crawl_order.index(export_dict['url']) + 1 if export_dict['url'] in self.state.crawl_order else 0,
                'confidence_at_crawl': self.state.metrics.get('confidence', 0),
                'total_documents': self.state.total_documents
            }
        
        return export_dict
    
    def import_knowledge_base(self, filepath: Union[str, Path], format: str = "jsonl") -> None:
        """Import a knowledge base from a file
        
        Args:
            filepath: Path to the file to import
            format: Import format - currently supports 'jsonl'
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if format == "jsonl":
            imported_results = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Convert back to a mock CrawlResult
                        mock_result = self._import_dict_to_crawl_result(data)
                        imported_results.append(mock_result)
            
            # Initialize state if needed
            if not self.state:
                self.state = CrawlState()
            
            # Add imported results
            self.state.knowledge_base.extend(imported_results)
            
            # Update state with imported data
            asyncio.run(self.strategy.update_state(self.state, imported_results))
            
            print(f"Imported {len(imported_results)} documents from {filepath}")
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def _import_dict_to_crawl_result(self, data: Dict[str, Any]):
        """Convert imported dict back to a mock CrawlResult"""
        class MockMarkdown:
            def __init__(self, content):
                self.raw_markdown = content
        
        class MockCrawlResult:
            def __init__(self, data):
                self.url = data.get('url', '')
                self.markdown = MockMarkdown(data.get('content', ''))
                self.links = data.get('links', {})
                self.metadata = data.get('metadata', {})
                self.success = data.get('success', True)
                self.timestamp = data.get('timestamp')
        
        return MockCrawlResult(data)
    
    def get_relevant_content(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get most relevant content for the query"""
        if not self.state or not self.state.knowledge_base:
            return []
        
        # Simple relevance ranking based on term overlap
        scored_docs = []
        query_terms = set(self.state.query.lower().split())
        
        for i, result in enumerate(self.state.knowledge_base):
            content = (result.markdown.raw_markdown or "").lower()
            content_terms = set(content.split())
            
            # Calculate relevance score
            overlap = len(query_terms & content_terms)
            score = overlap / len(query_terms) if query_terms else 0.0
            
            scored_docs.append({
                'url': result.url,
                'score': score,
                'content': result.markdown.raw_markdown,
                'index': i
            })
        
        # Sort by score and return top K
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:top_k]