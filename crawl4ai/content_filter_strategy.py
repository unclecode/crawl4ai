import os
import re
import time
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple, Dict
from rank_bm25 import BM25Okapi
import nltk
from time import perf_counter
from html5lib import parse, treebuilders
from time import perf_counter
from collections import deque
from bs4 import BeautifulSoup, NavigableString, Tag
from .utils import clean_tokens
from abc import ABC, abstractmethod

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
        if soup.title:
            query_parts.append(soup.title.string)
        elif soup.find('h1'):
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


    def extract_text_chunks(self, body: Tag) -> List[Tuple[str, str]]:
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
    def __init__(self, user_query: str = None, bm25_threshold: float = 1.0):
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

    def filter_content(self, html: str) -> List[str]:
        """Implements content filtering using BM25 algorithm with priority tag handling"""
        if not html or not isinstance(html, str):
            return []

        soup = BeautifulSoup(html, 'lxml')
        body = soup.find('body')
        query = self.extract_page_query(soup.find('head'), body)
        candidates = self.extract_text_chunks(body)

        if not candidates:
            return []

        # Split into priority and regular candidates
        priority_candidates = []
        regular_candidates = []
        
        for index, chunk, tag_type, tag in candidates:
            if tag.name in self.priority_tags:
                priority_candidates.append((index, chunk, tag_type, tag))
            else:
                regular_candidates.append((index, chunk, tag_type, tag))

        # Process regular content with BM25
        tokenized_corpus = [chunk.lower().split() for _, chunk, _, _ in regular_candidates]
        tokenized_query = query.lower().split()
        
        # Clean from stop words and noise
        tokenized_corpus = [clean_tokens(tokens) for tokens in tokenized_corpus]
        tokenized_query = clean_tokens(tokenized_query)
        
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        # Score and boost regular candidates
        scored_candidates = [
            (score * self.priority_tags.get(tag.name, 1.0), index, chunk, tag_type, tag)
            for score, (index, chunk, tag_type, tag) in zip(scores, regular_candidates)
        ]
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Process scored candidates
        selected_tags = set()
        selected_candidates = []

        # First add all priority candidates
        for index, chunk, tag_type, tag in priority_candidates:
            tag_id = id(tag)
            if tag_id not in selected_tags:
                selected_candidates.append((index, chunk, tag))
                selected_tags.add(tag_id)

        # Then add scored regular candidates that meet threshold
        for score, index, chunk, tag_type, tag in scored_candidates:
            if score < self.bm25_threshold:
                continue
            tag_id = id(tag)
            if tag_id not in selected_tags:
                selected_candidates.append((index, chunk, tag))
                selected_tags.add(tag_id)

        if not selected_candidates:
            return []

        # Sort by original document order
        selected_candidates.sort(key=lambda x: x[0])
        return [self.clean_element(tag) for _, _, tag in selected_candidates]

