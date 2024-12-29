import re
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple, Dict
from rank_bm25 import BM25Okapi
from time import perf_counter
from collections import deque
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
from .utils import clean_tokens
from abc import ABC, abstractmethod
import math
from snowballstemmer import stemmer
class RelevantContentFilter(ABC):
    """Abstract base class for content filtering strategies"""
    def __init__(self, user_query: str = None):
        self.user_query = user_query
        self.included_tags = {
            # Primary structure
            'article', 'main', 'section', 'div', 
            # List structures
            'ul', 'ol', 'li', 'dl', 'dt', 'dd',
            # Text content
            'p', 'span', 'blockquote', 'pre', 'code',
            # Headers
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            # Tables
            'table', 'thead', 'tbody', 'tr', 'td', 'th',
            # Other semantic elements
            'figure', 'figcaption', 'details', 'summary',
            # Text formatting
            'em', 'strong', 'b', 'i', 'mark', 'small',
            # Rich content
            'time', 'address', 'cite', 'q'
        }
        self.excluded_tags = {
            'nav', 'footer', 'header', 'aside', 'script',
            'style', 'form', 'iframe', 'noscript'
        }
        self.header_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
        self.negative_patterns = re.compile(
            r'nav|footer|header|sidebar|ads|comment|promo|advert|social|share',
            re.I
        )
        self.min_word_count = 2
        
    @abstractmethod
    def filter_content(self, html: str) -> List[str]:
        """Abstract method to be implemented by specific filtering strategies"""
        pass
    
    def extract_page_query(self, soup: BeautifulSoup, body: Tag) -> str:
        """Common method to extract page metadata with fallbacks"""
        if self.user_query:
            return self.user_query

        query_parts = []
        
        # Title
        try:
            title = soup.title.string
            if title:
                query_parts.append(title)
        except Exception:
            pass

        if soup.find('h1'):
            query_parts.append(soup.find('h1').get_text())
            
        # Meta tags
        temp = ""
        for meta_name in ['keywords', 'description']:
            meta = soup.find('meta', attrs={'name': meta_name})
            if meta and meta.get('content'):
                query_parts.append(meta['content'])
                temp += meta['content']
                
        # If still empty, grab first significant paragraph
        if not temp:
            # Find the first tag P thatits text contains more than 50 characters
            for p in body.find_all('p'):
                if len(p.get_text()) > 150:
                    query_parts.append(p.get_text()[:150])
                    break        
                                
        return ' '.join(filter(None, query_parts))


    def extract_text_chunks(self, body: Tag, min_word_threshold: int = None) -> List[Tuple[str, str]]:
        """
        Extracts text chunks from a BeautifulSoup body element while preserving order.
        Returns list of tuples (text, tag_name) for classification.
        
        Args:
            body: BeautifulSoup Tag object representing the body element
            
        Returns:
            List of (text, tag_name) tuples
        """
        # Tags to ignore - inline elements that shouldn't break text flow
        INLINE_TAGS = {
            'a', 'abbr', 'acronym', 'b', 'bdo', 'big', 'br', 'button', 'cite', 'code',
            'dfn', 'em', 'i', 'img', 'input', 'kbd', 'label', 'map', 'object', 'q',
            'samp', 'script', 'select', 'small', 'span', 'strong', 'sub', 'sup',
            'textarea', 'time', 'tt', 'var'
        }
        
        # Tags that typically contain meaningful headers
        HEADER_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header'}
        
        chunks = []
        current_text = []
        chunk_index = 0
    
        def should_break_chunk(tag: Tag) -> bool:
            """Determine if a tag should cause a break in the current text chunk"""
            return (
                tag.name not in INLINE_TAGS
                and not (tag.name == 'p' and len(current_text) == 0)
            )
        
        # Use deque for efficient push/pop operations
        stack = deque([(body, False)])
        
        while stack:
            element, visited = stack.pop()
            
            if visited:
                # End of block element - flush accumulated text
                if current_text and should_break_chunk(element):
                    text = ' '.join(''.join(current_text).split())
                    if text:
                        tag_type = 'header' if element.name in HEADER_TAGS else 'content'
                        chunks.append((chunk_index, text, tag_type, element))
                        chunk_index += 1
                    current_text = []
                continue
                
            if isinstance(element, NavigableString):
                if str(element).strip():
                    current_text.append(str(element).strip())
                continue
                
            # Pre-allocate children to avoid multiple list operations
            children = list(element.children)
            if not children:
                continue
                
            # Mark block for revisit after processing children
            stack.append((element, True))
            
            # Add children in reverse order for correct processing
            for child in reversed(children):
                if isinstance(child, (Tag, NavigableString)):
                    stack.append((child, False))
        
        # Handle any remaining text
        if current_text:
            text = ' '.join(''.join(current_text).split())
            if text:
                chunks.append((chunk_index, text, 'content', body))
        
        if min_word_threshold:
            chunks = [chunk for chunk in chunks if len(chunk[1].split()) >= min_word_threshold]
        
        return chunks    

    def _deprecated_extract_text_chunks(self, soup: BeautifulSoup) -> List[Tuple[int, str, Tag]]:
        """Common method for extracting text chunks"""
        _text_cache = {}
        def fast_text(element: Tag) -> str:
            elem_id = id(element)
            if elem_id in _text_cache:
                return _text_cache[elem_id]
            texts = []
            for content in element.contents:
                if isinstance(content, str):
                    text = content.strip()
                    if text:
                        texts.append(text)
            result = ' '.join(texts)
            _text_cache[elem_id] = result
            return result
        
        candidates = []
        index = 0
        
        def dfs(element):
            nonlocal index
            if isinstance(element, Tag):
                if element.name in self.included_tags:
                    if not self.is_excluded(element):
                        text = fast_text(element)
                        word_count = len(text.split())
                        
                        # Headers pass through with adjusted minimum
                        if element.name in self.header_tags:
                            if word_count >= 3:  # Minimal sanity check for headers
                                candidates.append((index, text, element))
                                index += 1
                        # Regular content uses standard minimum
                        elif word_count >= self.min_word_count:
                            candidates.append((index, text, element))
                            index += 1
                            
                for child in element.children:
                    dfs(child)

        dfs(soup.body if soup.body else soup)
        return candidates

    def is_excluded(self, tag: Tag) -> bool:
        """Common method for exclusion logic"""
        if tag.name in self.excluded_tags:
            return True
        class_id = ' '.join(filter(None, [
            ' '.join(tag.get('class', [])),
            tag.get('id', '')
        ]))
        return bool(self.negative_patterns.search(class_id))

    def clean_element(self, tag: Tag) -> str:
        """Common method for cleaning HTML elements with minimal overhead"""
        if not tag or not isinstance(tag, Tag):
            return ""
            
        unwanted_tags = {'script', 'style', 'aside', 'form', 'iframe', 'noscript'}
        unwanted_attrs = {'style', 'onclick', 'onmouseover', 'align', 'bgcolor', 'class', 'id'}
        
        # Use string builder pattern for better performance
        builder = []
        
        def render_tag(elem):
            if not isinstance(elem, Tag):
                if isinstance(elem, str):
                    builder.append(elem.strip())
                return
                
            if elem.name in unwanted_tags:
                return
                
            # Start tag
            builder.append(f'<{elem.name}')
            
            # Add cleaned attributes
            attrs = {k: v for k, v in elem.attrs.items() if k not in unwanted_attrs}
            for key, value in attrs.items():
                builder.append(f' {key}="{value}"')
                
            builder.append('>')
            
            # Process children
            for child in elem.children:
                render_tag(child)
                
            # Close tag
            builder.append(f'</{elem.name}>')
        
        try:
            render_tag(tag)
            return ''.join(builder)
        except Exception:
            return str(tag)  # Fallback to original if anything fails

class BM25ContentFilter(RelevantContentFilter):
    """
    Content filtering using BM25 algorithm with priority tag handling.
    
    How it works:
    1. Extracts page metadata with fallbacks.
    2. Extracts text chunks from the body element.
    3. Tokenizes the corpus and query.
    4. Applies BM25 algorithm to calculate scores for each chunk.
    5. Filters out chunks below the threshold.
    6. Sorts chunks by score in descending order.
    7. Returns the top N chunks.
    
    Attributes:
        user_query (str): User query for filtering (optional).
        bm25_threshold (float): BM25 threshold for filtering (default: 1.0).
        language (str): Language for stemming (default: 'english').
        
        Methods:
            filter_content(self, html: str, min_word_threshold: int = None)
    """
    def __init__(self, user_query: str = None, bm25_threshold: float = 1.0, language: str = 'english'):
        """
        Initializes the BM25ContentFilter class, if not provided, falls back to page metadata.
        
        Note:
        If no query is given and no page metadata is available, then it tries to pick up the first significant paragraph.
        
        Args:
            user_query (str): User query for filtering (optional).
            bm25_threshold (float): BM25 threshold for filtering (default: 1.0).
            language (str): Language for stemming (default: 'english').
        """
        super().__init__(user_query=user_query)
        self.bm25_threshold = bm25_threshold
        self.priority_tags = {
            'h1': 5.0,
            'h2': 4.0,
            'h3': 3.0,
            'title': 4.0,
            'strong': 2.0,
            'b': 1.5,
            'em': 1.5,
            'blockquote': 2.0,
            'code': 2.0,
            'pre': 1.5,
            'th': 1.5,  # Table headers
        }
        self.stemmer = stemmer(language)

    def filter_content(self, html: str, min_word_threshold: int = None) -> List[str]:
        """
        Implements content filtering using BM25 algorithm with priority tag handling.
        
            Note:
        This method implements the filtering logic for the BM25ContentFilter class.
        It takes HTML content as input and returns a list of filtered text chunks.
        
        Args:
            html (str): HTML content to be filtered.
            min_word_threshold (int): Minimum word threshold for filtering (optional).
        
        Returns:
            List[str]: List of filtered text chunks.
        """
        if not html or not isinstance(html, str):
            return []

        soup = BeautifulSoup(html, 'lxml')
        
        # Check if body is present
        if not soup.body:
            # Wrap in body tag if missing
            soup = BeautifulSoup(f'<body>{html}</body>', 'lxml')        
        body = soup.find('body')
        
        query = self.extract_page_query(soup, body)
        
        if not query:
            return []
            # return [self.clean_element(soup)]
            
        candidates = self.extract_text_chunks(body, min_word_threshold)

        if not candidates:
            return []

        # Tokenize corpus
        # tokenized_corpus = [chunk.lower().split() for _, chunk, _, _ in candidates]
        # tokenized_query = query.lower().split()
                
        # tokenized_corpus = [[ps.stem(word) for word in chunk.lower().split()] 
        #                 for _, chunk, _, _ in candidates]
        # tokenized_query = [ps.stem(word) for word in query.lower().split()]        
        
        tokenized_corpus = [[self.stemmer.stemWord(word) for word in chunk.lower().split()] 
                   for _, chunk, _, _ in candidates]
        tokenized_query = [self.stemmer.stemWord(word) for word in query.lower().split()]

        # tokenized_corpus = [[self.stemmer.stemWord(word) for word in tokenize_text(chunk.lower())] 
        #            for _, chunk, _, _ in candidates]
        # tokenized_query = [self.stemmer.stemWord(word) for word in tokenize_text(query.lower())]

        # Clean from stop words and noise
        tokenized_corpus = [clean_tokens(tokens) for tokens in tokenized_corpus]
        tokenized_query = clean_tokens(tokenized_query)

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        # Adjust scores with tag weights
        adjusted_candidates = []
        for score, (index, chunk, tag_type, tag) in zip(scores, candidates):
            tag_weight = self.priority_tags.get(tag.name, 1.0)
            adjusted_score = score * tag_weight
            adjusted_candidates.append((adjusted_score, index, chunk, tag))

        # Filter candidates by threshold
        selected_candidates = [
            (index, chunk, tag) for adjusted_score, index, chunk, tag in adjusted_candidates
            if adjusted_score >= self.bm25_threshold
        ]

        if not selected_candidates:
            return []

        # Sort selected candidates by original document order
        selected_candidates.sort(key=lambda x: x[0])

        return [self.clean_element(tag) for _, _, tag in selected_candidates]

class PruningContentFilter(RelevantContentFilter):
    """
    Content filtering using pruning algorithm with dynamic threshold.
    
    How it works:
    1. Extracts page metadata with fallbacks.
    2. Extracts text chunks from the body element.
    3. Applies pruning algorithm to calculate scores for each chunk.
    4. Filters out chunks below the threshold.
    5. Sorts chunks by score in descending order.
    6. Returns the top N chunks.

    Attributes:
        user_query (str): User query for filtering (optional), if not provided, falls back to page metadata.
        min_word_threshold (int): Minimum word threshold for filtering (optional).
        threshold_type (str): Threshold type for dynamic threshold (default: 'fixed').
        threshold (float): Fixed threshold value (default: 0.48).
        
        Methods:
            filter_content(self, html: str, min_word_threshold: int = None):
    """
    def __init__(self, user_query: str = None, min_word_threshold: int = None, 
                 threshold_type: str = 'fixed', threshold: float = 0.48):
        """
        Initializes the PruningContentFilter class, if not provided, falls back to page metadata.
        
        Note:
        If no query is given and no page metadata is available, then it tries to pick up the first significant paragraph.
        
        Args:
            user_query (str): User query for filtering (optional).
            min_word_threshold (int): Minimum word threshold for filtering (optional).
            threshold_type (str): Threshold type for dynamic threshold (default: 'fixed').
            threshold (float): Fixed threshold value (default: 0.48).
        """
        super().__init__(None)
        self.min_word_threshold = min_word_threshold
        self.threshold_type = threshold_type
        self.threshold = threshold
        
        # Add tag importance for dynamic threshold
        self.tag_importance = {
            'article': 1.5,
            'main': 1.4,
            'section': 1.3,
            'p': 1.2,
            'h1': 1.4,
            'h2': 1.3,
            'h3': 1.2,
            'div': 0.7,
            'span': 0.6
        }
        
        # Metric configuration
        self.metric_config = {
            'text_density': True,
            'link_density': True,
            'tag_weight': True,
            'class_id_weight': True,
            'text_length': True,
        }
        
        self.metric_weights = {
            'text_density': 0.4,
            'link_density': 0.2,
            'tag_weight': 0.2,
            'class_id_weight': 0.1,
            'text_length': 0.1,
        }
        
        self.tag_weights = {
            'div': 0.5,
            'p': 1.0,
            'article': 1.5,
            'section': 1.0,
            'span': 0.3,
            'li': 0.5,
            'ul': 0.5,
            'ol': 0.5,
            'h1': 1.2,
            'h2': 1.1,
            'h3': 1.0,
            'h4': 0.9,
            'h5': 0.8,
            'h6': 0.7,
        }

    def filter_content(self, html: str, min_word_threshold: int = None) -> List[str]:
        """
        Implements content filtering using pruning algorithm with dynamic threshold.
        
        Note:
        This method implements the filtering logic for the PruningContentFilter class.
        It takes HTML content as input and returns a list of filtered text chunks.
        
        Args:
            html (str): HTML content to be filtered.
            min_word_threshold (int): Minimum word threshold for filtering (optional).
        
        Returns:
            List[str]: List of filtered text chunks.
        """
        if not html or not isinstance(html, str):
            return []
            
        soup = BeautifulSoup(html, 'lxml')
        if not soup.body:
            soup = BeautifulSoup(f'<body>{html}</body>', 'lxml')
        
        # Remove comments and unwanted tags
        self._remove_comments(soup)
        self._remove_unwanted_tags(soup)
        
        # Prune tree starting from body
        body = soup.find('body')
        self._prune_tree(body)
        
        # Extract remaining content as list of HTML strings
        content_blocks = []
        for element in body.children:
            if isinstance(element, str) or not hasattr(element, 'name'):
                continue
            if len(element.get_text(strip=True)) > 0:
                content_blocks.append(str(element))
                
        return content_blocks

    def _remove_comments(self, soup):
        """Removes HTML comments"""
        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

    def _remove_unwanted_tags(self, soup):
        """Removes unwanted tags"""
        for tag in self.excluded_tags:
            for element in soup.find_all(tag):
                element.decompose()

    def _prune_tree(self, node):
        """
        Prunes the tree starting from the given node.
        
        Args:
            node (Tag): The node from which the pruning starts.
        """
        if not node or not hasattr(node, 'name') or node.name is None:
            return

        text_len = len(node.get_text(strip=True))
        tag_len = len(node.encode_contents().decode('utf-8'))
        link_text_len = sum(len(s.strip()) for s in (a.string for a in node.find_all('a', recursive=False)) if s)

        metrics = {
            'node': node,
            'tag_name': node.name,
            'text_len': text_len,
            'tag_len': tag_len,
            'link_text_len': link_text_len
        }

        score = self._compute_composite_score(metrics, text_len, tag_len, link_text_len)

        if self.threshold_type == 'fixed':
            should_remove = score < self.threshold
        else:  # dynamic
            tag_importance = self.tag_importance.get(node.name, 0.7)
            text_ratio = text_len / tag_len if tag_len > 0 else 0
            link_ratio = link_text_len / text_len if text_len > 0 else 1
            
            threshold = self.threshold  # base threshold
            if tag_importance > 1:
                threshold *= 0.8
            if text_ratio > 0.4:
                threshold *= 0.9
            if link_ratio > 0.6:
                threshold *= 1.2
                
            should_remove = score < threshold

        if should_remove:
            node.decompose()
        else:
            children = [child for child in node.children if hasattr(child, 'name')]
            for child in children:
                self._prune_tree(child)

    def _compute_composite_score(self, metrics, text_len, tag_len, link_text_len):
        """Computes the composite score"""
        if self.min_word_threshold:
            # Get raw text from metrics node - avoid extra processing
            text = metrics['node'].get_text(strip=True)
            word_count = text.count(' ') + 1
            if word_count < self.min_word_threshold:
                return -1.0  # Guaranteed removal
        score = 0.0
        total_weight = 0.0

        if self.metric_config['text_density']:
            density = text_len / tag_len if tag_len > 0 else 0
            score += self.metric_weights['text_density'] * density
            total_weight += self.metric_weights['text_density']

        if self.metric_config['link_density']:
            density = 1 - (link_text_len / text_len if text_len > 0 else 0)
            score += self.metric_weights['link_density'] * density
            total_weight += self.metric_weights['link_density']

        if self.metric_config['tag_weight']:
            tag_score = self.tag_weights.get(metrics['tag_name'], 0.5)
            score += self.metric_weights['tag_weight'] * tag_score
            total_weight += self.metric_weights['tag_weight']

        if self.metric_config['class_id_weight']:
            class_score = self._compute_class_id_weight(metrics['node'])
            score += self.metric_weights['class_id_weight'] * max(0, class_score)
            total_weight += self.metric_weights['class_id_weight']

        if self.metric_config['text_length']:
            score += self.metric_weights['text_length'] * math.log(text_len + 1)
            total_weight += self.metric_weights['text_length']

        return score / total_weight if total_weight > 0 else 0

    def _compute_class_id_weight(self, node):
        """Computes the class ID weight"""
        class_id_score = 0
        if 'class' in node.attrs:
            classes = ' '.join(node['class'])
            if self.negative_patterns.match(classes):
                class_id_score -= 0.5
        if 'id' in node.attrs:
            element_id = node['id']
            if self.negative_patterns.match(element_id):
                class_id_score -= 0.5
        return class_id_score