import re
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple, Dict
from rank_bm25 import BM25Okapi
from time import perf_counter
from collections import deque
from bs4 import BeautifulSoup, NavigableString, Tag
from .utils import clean_tokens
from abc import ABC, abstractmethod

from snowballstemmer import stemmer


# import regex
# def tokenize_text(text):
#     # Regular expression to match words or CJK (Chinese, Japanese, Korean) characters
#     pattern = r'\p{L}+|\p{N}+|[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}ー]|[\p{P}]'
#     return regex.findall(pattern, text)

# from nltk.stem import PorterStemmer
# ps = PorterStemmer()
class RelevantContentFilter(ABC):
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
    

    def extract_text_chunks1(self, soup: BeautifulSoup) -> List[Tuple[int, str, Tag]]:
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
    def __init__(self, user_query: str = None, bm25_threshold: float = 1.0, language: str = 'english'):
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
        """Implements content filtering using BM25 algorithm with priority tag handling"""
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


class HeuristicContentFilter(RelevantContentFilter):
    def __init__(self):
        super().__init__()
        # Weights for different heuristics
        self.tag_weights = {
            'article': 10,
            'main': 8,
            'section': 5,
            'div': 3,
            'p': 2,
            'pre': 2,
            'code': 2,
            'blockquote': 2,
            'li': 1,
            'span': 1,
        }
        self.max_depth = 5  # Maximum depth from body to consider

    def filter_content(self, html: str) -> List[str]:
        """Implements heuristic content filtering without relying on a query."""
        if not html or not isinstance(html, str):
            return []

        soup = BeautifulSoup(html, 'lxml')

        # Ensure there is a body tag
        if not soup.body:
            soup = BeautifulSoup(f'<body>{html}</body>', 'lxml')
        body = soup.body

        # Extract candidate text chunks
        candidates = self.extract_text_chunks(body)

        if not candidates:
            return []

        # Score each candidate
        scored_candidates = []
        for index, text, tag_type, tag in candidates:
            score = self.score_element(tag, text)
            if score > 0:
                scored_candidates.append((score, index, text, tag))

        # Sort candidates by score and then by document order
        scored_candidates.sort(key=lambda x: (-x[0], x[1]))

        # Extract the top candidates (e.g., top 5)
        top_candidates = scored_candidates[:5]  # Adjust the number as needed

        # Sort the top candidates back to their original document order
        top_candidates.sort(key=lambda x: x[1])

        # Clean and return the content
        return [self.clean_element(tag) for _, _, _, tag in top_candidates]

    def score_element(self, tag: Tag, text: str) -> float:
        """Compute a score for an element based on heuristics."""
        if not text or not tag:
            return 0

        # Exclude unwanted tags
        if self.is_excluded(tag):
            return 0

        # Text density
        text_length = len(text.strip())
        html_length = len(str(tag))
        text_density = text_length / html_length if html_length > 0 else 0

        # Link density
        link_text_length = sum(len(a.get_text().strip()) for a in tag.find_all('a'))
        link_density = link_text_length / text_length if text_length > 0 else 0

        # Tag weight
        tag_weight = self.tag_weights.get(tag.name, 1)

        # Depth factor (prefer elements closer to the body tag)
        depth = self.get_depth(tag)
        depth_weight = max(self.max_depth - depth, 1) / self.max_depth

        # Compute the final score
        score = (text_density * tag_weight * depth_weight) / (1 + link_density)

        return score

    def get_depth(self, tag: Tag) -> int:
        """Compute the depth of the tag from the body tag."""
        depth = 0
        current = tag
        while current and current != current.parent and current.name != 'body':
            current = current.parent
            depth += 1
        return depth

    def extract_text_chunks(self, body: Tag) -> List[Tuple[int, str, str, Tag]]:
        """
        Extracts text chunks from the body element while preserving order.
        Returns list of tuples (index, text, tag_type, tag) for scoring.
        """
        chunks = []
        index = 0

        def traverse(element):
            nonlocal index
            if isinstance(element, NavigableString):
                return
            if not isinstance(element, Tag):
                return
            if self.is_excluded(element):
                return
            # Only consider included tags
            if element.name in self.included_tags:
                text = element.get_text(separator=' ', strip=True)
                if len(text.split()) >= self.min_word_count:
                    tag_type = 'header' if element.name in self.header_tags else 'content'
                    chunks.append((index, text, tag_type, element))
                    index += 1
                    # Do not traverse children of this element to prevent duplication
                    return
            for child in element.children:
                traverse(child)

        traverse(body)
        return chunks

    def is_excluded(self, tag: Tag) -> bool:
        """Determine if a tag should be excluded based on heuristics."""
        if tag.name in self.excluded_tags:
            return True
        class_id = ' '.join(filter(None, [
            ' '.join(tag.get('class', [])),
            tag.get('id', '')
        ]))
        if self.negative_patterns.search(class_id):
            return True
        # Exclude tags with high link density (e.g., navigation menus)
        text = tag.get_text(separator=' ', strip=True)
        link_text_length = sum(len(a.get_text(strip=True)) for a in tag.find_all('a'))
        text_length = len(text)
        if text_length > 0 and (link_text_length / text_length) > 0.5:
            return True
        return False
