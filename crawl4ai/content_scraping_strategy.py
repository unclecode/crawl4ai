import re  # Point 1: Pre-Compile Regular Expressions
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import asyncio, requests, re, os
from .config import *
from bs4 import element, NavigableString, Comment
from bs4 import PageElement, Tag
from urllib.parse import urljoin
from requests.exceptions import InvalidSchema
# from .content_cleaning_strategy import ContentCleaningStrategy
from .content_filter_strategy import RelevantContentFilter, BM25ContentFilter#, HeuristicContentFilter
from .markdown_generation_strategy import MarkdownGenerationStrategy, DefaultMarkdownGenerator
from .models import MarkdownGenerationResult
from .utils import (
    extract_metadata,
    normalize_url,
    is_external_url,    
    get_base_domain,    
)


# Pre-compile regular expressions for Open Graph and Twitter metadata
OG_REGEX = re.compile(r'^og:')
TWITTER_REGEX = re.compile(r'^twitter:')
DIMENSION_REGEX = re.compile(r"(\d+)(\D*)")

# Function to parse image height/width value and units
def parse_dimension(dimension):
    if dimension:
        # match = re.match(r"(\d+)(\D*)", dimension)
        match = DIMENSION_REGEX.match(dimension)
        if match:
            number = int(match.group(1))
            unit = match.group(2) or 'px'  # Default unit is 'px' if not specified
            return number, unit
    return None, None

# Fetch image file metadata to extract size and extension
def fetch_image_file_size(img, base_url):
    #If src is relative path construct full URL, if not it may be CDN URL
    img_url = urljoin(base_url,img.get('src'))
    try:
        response = requests.head(img_url)
        if response.status_code == 200:
            return response.headers.get('Content-Length',None)
        else:
            print(f"Failed to retrieve file size for {img_url}")
            return None
    except InvalidSchema as e:
        return None
    finally:
        return

class ContentScrapingStrategy(ABC):
    @abstractmethod
    def scrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def ascrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        pass

class WebScrapingStrategy(ContentScrapingStrategy):
    """
    Class for web content scraping. Perhaps the most important class. 
    
    How it works:
    1. Extract content from HTML using BeautifulSoup.
    2. Clean the extracted content using a content cleaning strategy.
    3. Filter the cleaned content using a content filtering strategy.
    4. Generate markdown content from the filtered content.
    5. Return the markdown content.
    """
    
    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, level, message, tag="SCRAPE", **kwargs):
        """Helper method to safely use logger."""
        if self.logger:
            log_method = getattr(self.logger, level)
            log_method(message=message, tag=tag, **kwargs)
                
    def scrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for content scraping.  

        Args:
            url (str): The URL of the page to scrape.
            html (str): The HTML content of the page.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the scraped content. This dictionary contains the following keys:

            - 'markdown': The generated markdown content, type is str, however soon will become MarkdownGenerationResult via 'markdown.raw_markdown'.
            - 'fit_markdown': The generated markdown content with relevant content filtered, this will be removed soon and available in 'markdown.fit_markdown'.
            - 'fit_html': The HTML content with relevant content filtered, this will be removed soon and available in 'markdown.fit_html'.
            - 'markdown_v2': The generated markdown content with relevant content filtered, this is temporary and will be removed soon and replaced with 'markdown'
        """
        return self._scrap(url, html, is_async=False, **kwargs)

    async def ascrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for asynchronous content scraping.

        Args:
            url (str): The URL of the page to scrape.
            html (str): The HTML content of the page.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the scraped content. This dictionary contains the following keys:

            - 'markdown': The generated markdown content, type is str, however soon will become MarkdownGenerationResult via 'markdown.raw_markdown'.
            - 'fit_markdown': The generated markdown content with relevant content filtered, this will be removed soon and available in 'markdown.fit_markdown'.
            - 'fit_html': The HTML content with relevant content filtered, this will be removed soon and available in 'markdown.fit_html'.
            - 'markdown_v2': The generated markdown content with relevant content filtered, this is temporary and will be removed soon and replaced with 'markdown'
        """
        return await asyncio.to_thread(self._scrap, url, html, **kwargs)

    def _generate_markdown_content(self, cleaned_html: str,html: str,url: str, success: bool, **kwargs) -> Dict[str, Any]:
        """
        Generate markdown content from cleaned HTML.

        Args:
            cleaned_html (str): The cleaned HTML content.
            html (str): The original HTML content.
            url (str): The URL of the page.
            success (bool): Whether the content was successfully cleaned.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the generated markdown content.
        """
        markdown_generator: Optional[MarkdownGenerationStrategy] = kwargs.get('markdown_generator', DefaultMarkdownGenerator())
        
        if markdown_generator:
            try:
                if kwargs.get('fit_markdown', False) and not markdown_generator.content_filter:
                        markdown_generator.content_filter = BM25ContentFilter(
                            user_query=kwargs.get('fit_markdown_user_query', None),
                            bm25_threshold=kwargs.get('fit_markdown_bm25_threshold', 1.0)
                        )
                
                markdown_result: MarkdownGenerationResult = markdown_generator.generate_markdown(
                    cleaned_html=cleaned_html,
                    base_url=url,
                    html2text_options=kwargs.get('html2text', {})
                )
                
                return {
                    'markdown': markdown_result.raw_markdown,  
                    'fit_markdown': markdown_result.fit_markdown,
                    'fit_html': markdown_result.fit_html, 
                    'markdown_v2': markdown_result
                }
            except Exception as e:
                self._log('error',
                    message="Error using new markdown generation strategy: {error}",
                    tag="SCRAPE",
                    params={"error": str(e)}
                )
                markdown_generator = None
                return {
                    'markdown': f"Error using new markdown generation strategy: {str(e)}",
                    'fit_markdown': "Set flag 'fit_markdown' to True to get cleaned HTML content.",
                    'fit_html': "Set flag 'fit_markdown' to True to get cleaned HTML content.",
                    'markdown_v2': None                    
                }

        # Legacy method
        """
        # h = CustomHTML2Text()
        # h.update_params(**kwargs.get('html2text', {}))            
        # markdown = h.handle(cleaned_html)
        # markdown = markdown.replace('    ```', '```')
        
        # fit_markdown = "Set flag 'fit_markdown' to True to get cleaned HTML content."
        # fit_html = "Set flag 'fit_markdown' to True to get cleaned HTML content."
        
        # if kwargs.get('content_filter', None) or kwargs.get('fit_markdown', False):
        #     content_filter = kwargs.get('content_filter', None)
        #     if not content_filter:
        #         content_filter = BM25ContentFilter(
        #             user_query=kwargs.get('fit_markdown_user_query', None),
        #             bm25_threshold=kwargs.get('fit_markdown_bm25_threshold', 1.0)
        #         )
        #     fit_html = content_filter.filter_content(html)
        #     fit_html = '\n'.join('<div>{}</div>'.format(s) for s in fit_html)
        #     fit_markdown = h.handle(fit_html)

        # markdown_v2 = MarkdownGenerationResult(
        #     raw_markdown=markdown,
        #     markdown_with_citations=markdown,
        #     references_markdown=markdown,
        #     fit_markdown=fit_markdown
        # )
        
        # return {
        #     'markdown': markdown,
        #     'fit_markdown': fit_markdown,
        #     'fit_html': fit_html,
        #     'markdown_v2' : markdown_v2
        # }
        """

    def flatten_nested_elements(self, node):
        """
        Flatten nested elements in a HTML tree.

        Args:
            node (Tag): The root node of the HTML tree.

        Returns:
            Tag: The flattened HTML tree.
        """
        if isinstance(node, NavigableString):
            return node
        if len(node.contents) == 1 and isinstance(node.contents[0], Tag) and node.contents[0].name == node.name:
            return self.flatten_nested_elements(node.contents[0])
        node.contents = [self.flatten_nested_elements(child) for child in node.contents]
        return node

    def find_closest_parent_with_useful_text(self, tag, **kwargs):
        """
        Find the closest parent with useful text.

        Args:
            tag (Tag): The starting tag to search from.
            **kwargs: Additional keyword arguments.

        Returns:
            Tag: The closest parent with useful text, or None if not found.
        """
        image_description_min_word_threshold = kwargs.get('image_description_min_word_threshold', IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD)
        current_tag = tag
        while current_tag:
            current_tag = current_tag.parent
            # Get the text content of the parent tag
            if current_tag:
                text_content = current_tag.get_text(separator=' ',strip=True)
                # Check if the text content has at least word_count_threshold
                if len(text_content.split()) >= image_description_min_word_threshold:
                    return text_content
        return None

    def remove_unwanted_attributes(self, element, important_attrs, keep_data_attributes=False):
        """
        Remove unwanted attributes from an HTML element.

        Args:    
            element (Tag): The HTML element to remove attributes from.
            important_attrs (list): List of important attributes to keep.
            keep_data_attributes (bool): Whether to keep data attributes.

        Returns:
            None
        """
        attrs_to_remove = []
        for attr in element.attrs:
            if attr not in important_attrs:
                if keep_data_attributes:
                    if not attr.startswith('data-'):
                        attrs_to_remove.append(attr)
                else:
                    attrs_to_remove.append(attr)
        
        for attr in attrs_to_remove:
            del element[attr]

    def process_image(self, img, url, index, total_images, **kwargs):
        """
        Process an image element.
        
        How it works:
        1. Check if the image has valid display and inside undesired html elements.
        2. Score an image for it's usefulness.
        3. Extract image file metadata to extract size and extension.
        4. Generate a dictionary with the processed image information.
        5. Return the processed image information.

        Args:
            img (Tag): The image element to process.
            url (str): The URL of the page containing the image.
            index (int): The index of the image in the list of images.
            total_images (int): The total number of images in the list.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the processed image information.
        """
        parse_srcset = lambda s: [{'url': u.strip().split()[0], 'width': u.strip().split()[-1].rstrip('w') 
                        if ' ' in u else None} 
                        for u in [f"http{p}" for p in s.split("http") if p]]
        
        # Constants for checks
        classes_to_check = frozenset(['button', 'icon', 'logo'])
        tags_to_check = frozenset(['button', 'input'])
        image_formats = frozenset(['jpg', 'jpeg', 'png', 'webp', 'avif', 'gif'])
        
        # Pre-fetch commonly used attributes
        style = img.get('style', '')
        alt = img.get('alt', '')
        src = img.get('src', '')
        data_src = img.get('data-src', '')
        srcset = img.get('srcset', '')
        data_srcset = img.get('data-srcset', '')        
        width = img.get('width')
        height = img.get('height')
        parent = img.parent
        parent_classes = parent.get('class', [])

        # Quick validation checks
        if ('display:none' in style or
            parent.name in tags_to_check or
            any(c in cls for c in parent_classes for cls in classes_to_check) or
            any(c in src for c in classes_to_check) or
            any(c in alt for c in classes_to_check)):
            return None

        # Quick score calculation
        score = 0
        if width and width.isdigit():
            width_val = int(width)
            score += 1 if width_val > 150 else 0
        if height and height.isdigit():
            height_val = int(height)
            score += 1 if height_val > 150 else 0
        if alt:
            score += 1
        score += index/total_images < 0.5
        
        # image_format = ''
        # if "data:image/" in src:
        #     image_format = src.split(',')[0].split(';')[0].split('/')[1].split(';')[0]
        # else:
        #     image_format = os.path.splitext(src)[1].lower().strip('.').split('?')[0]
        
        # if image_format in ('jpg', 'png', 'webp', 'avif'):
        #     score += 1
            
            
        # Check for image format in all possible sources
        def has_image_format(url):
            return any(fmt in url.lower() for fmt in image_formats)
        
        # Score for having proper image sources
        if any(has_image_format(url) for url in [src, data_src, srcset, data_srcset]):
            score += 1
        if srcset or data_srcset:
            score += 1
        if img.find_parent('picture'):
            score += 1
        
        # Detect format from any available source
        detected_format = None
        for url in [src, data_src, srcset, data_srcset]:
            if url:
                format_matches = [fmt for fmt in image_formats if fmt in url.lower()]
                if format_matches:
                    detected_format = format_matches[0]
                    break            

        if score <= kwargs.get('image_score_threshold', IMAGE_SCORE_THRESHOLD):
            return None

        # Use set for deduplication
        unique_urls = set()
        image_variants = []
        
        # Generate a unique group ID for this set of variants
        group_id = index 
        
        # Base image info template
        image_description_min_word_threshold = kwargs.get('image_description_min_word_threshold', IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD)
        base_info = {
            'alt': alt,
            'desc': self.find_closest_parent_with_useful_text(img, **kwargs),
            'score': score,
            'type': 'image',
            'group_id': group_id, # Group ID for this set of variants
            'format': detected_format,
        }

        # Inline function for adding variants
        def add_variant(src, width=None):
            if src and not src.startswith('data:') and src not in unique_urls:
                unique_urls.add(src)
                image_variants.append({**base_info, 'src': src, 'width': width})

        # Process all sources
        add_variant(src)
        add_variant(data_src)
        
        # Handle srcset and data-srcset in one pass
        for attr in ('srcset', 'data-srcset'):
            if value := img.get(attr):
                for source in parse_srcset(value):
                    add_variant(source['url'], source['width'])

        # Quick picture element check
        if picture := img.find_parent('picture'):
            for source in picture.find_all('source'):
                if srcset := source.get('srcset'):
                    for src in parse_srcset(srcset):
                        add_variant(src['url'], src['width'])

        # Framework-specific attributes in one pass
        for attr, value in img.attrs.items():
            if attr.startswith('data-') and ('src' in attr or 'srcset' in attr) and 'http' in value:
                add_variant(value)

        return image_variants if image_variants else None

    def process_element(self, url, element: PageElement, **kwargs) -> Dict[str, Any]:        
        """
        Process an HTML element.
        
        How it works:
        1. Check if the element is an image, video, or audio.
        2. Extract the element's attributes and content.
        3. Process the element based on its type.
        4. Return the processed element information.

        Args:
            url (str): The URL of the page containing the element.
            element (Tag): The HTML element to process.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the processed element information.
        """
        media = {'images': [], 'videos': [], 'audios': []}
        internal_links_dict = {}
        external_links_dict = {}
        self._process_element(
            url,
            element,
            media,
            internal_links_dict,
            external_links_dict,
            **kwargs
        )
        return {
            'media': media,
            'internal_links_dict': internal_links_dict,
            'external_links_dict': external_links_dict
        }
        
    def _process_element(self, url, element: PageElement,  media: Dict[str, Any], internal_links_dict: Dict[str, Any], external_links_dict: Dict[str, Any], **kwargs) -> bool:
        """
        Process an HTML element.        
        """
        try:
            if isinstance(element, NavigableString):
                if isinstance(element, Comment):
                    element.extract()
                return False
            
            # if element.name == 'img':
            #     process_image(element, url, 0, 1)
            #     return True
            base_domain = kwargs.get("base_domain", get_base_domain(url))

            if element.name in ['script', 'style', 'link', 'meta', 'noscript']:
                element.decompose()
                return False

            keep_element = False
            
            exclude_domains = kwargs.get('exclude_domains', [])
            # exclude_social_media_domains = kwargs.get('exclude_social_media_domains', set(SOCIAL_MEDIA_DOMAINS))
            # exclude_social_media_domains = SOCIAL_MEDIA_DOMAINS + kwargs.get('exclude_social_media_domains', [])
            # exclude_social_media_domains = list(set(exclude_social_media_domains))
            
            try:
                if element.name == 'a' and element.get('href'):
                    href = element.get('href', '').strip()
                    if not href:  # Skip empty hrefs
                        return False
                        
                    url_base = url.split('/')[2]
                    
                    # Normalize the URL
                    try:
                        normalized_href = normalize_url(href, url)
                    except ValueError as e:
                        # logging.warning(f"Invalid URL format: {href}, Error: {str(e)}")
                        return False
                        
                    link_data = {
                        'href': normalized_href,
                        'text': element.get_text().strip(),
                        'title': element.get('title', '').strip(),
                        'base_domain': base_domain
                    }
                                        
                    is_external = is_external_url(normalized_href, base_domain)
                            
                    keep_element = True
                    
                    # Handle external link exclusions
                    if is_external:
                        link_base_domain = get_base_domain(normalized_href)
                        link_data['base_domain'] = link_base_domain
                        if kwargs.get('exclude_external_links', False):
                            element.decompose()
                            return False
                        # elif kwargs.get('exclude_social_media_links', False):
                        #     if link_base_domain in exclude_social_media_domains:
                        #         element.decompose()
                        #         return False
                            # if any(domain in normalized_href.lower() for domain in exclude_social_media_domains):
                            #     element.decompose()
                            #     return False
                        elif exclude_domains:
                            if link_base_domain in exclude_domains:
                                element.decompose()
                                return False
                            # if any(domain in normalized_href.lower() for domain in kwargs.get('exclude_domains', [])):
                            #     element.decompose()
                            #     return False

                    if is_external:
                        if normalized_href not in external_links_dict:
                            external_links_dict[normalized_href] = link_data
                    else:
                        if normalized_href not in internal_links_dict:
                            internal_links_dict[normalized_href] = link_data

                                
            except Exception as e:
                raise Exception(f"Error processing links: {str(e)}")

            try:
                if element.name == 'img':
                    potential_sources = ['src', 'data-src', 'srcset' 'data-lazy-src', 'data-original']
                    src = element.get('src', '')
                    while not src and potential_sources:
                        src = element.get(potential_sources.pop(0), '')
                    if not src:
                        element.decompose()
                        return False
                    
                    # If it is srcset pick up the first image
                    if 'srcset' in element.attrs:
                        src = element.attrs['srcset'].split(',')[0].split(' ')[0]
                        
                    # If image src is internal, then skip
                    if not is_external_url(src, base_domain):
                        return True
                    
                    image_src_base_domain = get_base_domain(src)
                    
                    # Check flag if we should remove external images
                    if kwargs.get('exclude_external_images', False):
                        element.decompose()
                        return False
                        # src_url_base = src.split('/')[2]
                        # url_base = url.split('/')[2]
                        # if url_base not in src_url_base:
                        #     element.decompose()
                        #     return False
                        
                    # if kwargs.get('exclude_social_media_links', False):
                    #     if image_src_base_domain in exclude_social_media_domains:
                    #         element.decompose()
                    #         return False
                        # src_url_base = src.split('/')[2]
                        # url_base = url.split('/')[2]
                        # if any(domain in src for domain in exclude_social_media_domains):
                        #     element.decompose()
                        #     return False
                        
                    # Handle exclude domains
                    if exclude_domains:                        
                        if image_src_base_domain in exclude_domains:
                            element.decompose()
                            return False
                        # if any(domain in src for domain in kwargs.get('exclude_domains', [])):
                        #     element.decompose()
                        #     return False
                    
                    return True  # Always keep image elements
            except Exception as e:
                raise "Error processing images"
            
            
            # Check if flag to remove all forms is set
            if kwargs.get('remove_forms', False) and element.name == 'form':
                element.decompose()
                return False
            
            if element.name in ['video', 'audio']:
                media[f"{element.name}s"].append({
                    'src': element.get('src'),
                    'alt': element.get('alt'),
                    'type': element.name,
                    'description': self.find_closest_parent_with_useful_text(element, **kwargs)
                })
                source_tags = element.find_all('source')
                for source_tag in source_tags:
                    media[f"{element.name}s"].append({
                    'src': source_tag.get('src'),
                    'alt': element.get('alt'),
                    'type': element.name,
                    'description': self.find_closest_parent_with_useful_text(element, **kwargs)
                })
                return True  # Always keep video and audio elements

            if element.name in ONLY_TEXT_ELIGIBLE_TAGS:
                if kwargs.get('only_text', False):
                    element.replace_with(element.get_text())

            try:
                self.remove_unwanted_attributes(element, IMPORTANT_ATTRS, kwargs.get('keep_data_attributes', False))
            except Exception as e:
                # print('Error removing unwanted attributes:', str(e))
                self._log('error',
                    message="Error removing unwanted attributes: {error}",
                    tag="SCRAPE",
                    params={"error": str(e)}
                )
            # Process children
            for child in list(element.children):
                if isinstance(child, NavigableString) and not isinstance(child, Comment):
                    if len(child.strip()) > 0:
                        keep_element = True
                else:
                    if self._process_element(url, child, media, internal_links_dict, external_links_dict, **kwargs):
                        keep_element = True
                

            # Check word count
            word_count_threshold = kwargs.get('word_count_threshold', MIN_WORD_THRESHOLD)
            if not keep_element:
                word_count = len(element.get_text(strip=True).split())
                keep_element = word_count >= word_count_threshold

            if not keep_element:
                element.decompose()

            return keep_element
        except Exception as e:
            # print('Error processing element:', str(e))
            self._log('error',
                message="Error processing element: {error}",
                tag="SCRAPE",
                params={"error": str(e)}
            )                
            return False

    def _scrap(self, url: str, html: str, word_count_threshold: int = MIN_WORD_THRESHOLD, css_selector: str = None, **kwargs) -> Dict[str, Any]:
        """
        Extract content from HTML using BeautifulSoup.

        Args:
            url (str): The URL of the page to scrape.
            html (str): The HTML content of the page to scrape.
            word_count_threshold (int): The minimum word count threshold for content extraction.
            css_selector (str): The CSS selector to use for content extraction.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the extracted content.
        """
        success = True
        if not html:
            return None

        parser_type = kwargs.get('parser', 'lxml')
        soup = BeautifulSoup(html, parser_type)
        body = soup.body
        base_domain = get_base_domain(url)
        
        try:
            meta = extract_metadata("", soup)
        except Exception as e:
            self._log('error', 
                message="Error extracting metadata: {error}",
                tag="SCRAPE",
                params={"error": str(e)}
            )            
            meta = {}
        
        # Handle tag-based removal first - faster than CSS selection
        excluded_tags = set(kwargs.get('excluded_tags', []) or [])  
        if excluded_tags:
            for element in body.find_all(lambda tag: tag.name in excluded_tags):
                element.extract()
        
        # Handle CSS selector-based removal
        excluded_selector = kwargs.get('excluded_selector', '')
        if excluded_selector:
            is_single_selector = ',' not in excluded_selector and ' ' not in excluded_selector
            if is_single_selector:
                while element := body.select_one(excluded_selector):
                    element.extract()
            else:
                for element in body.select(excluded_selector):
                    element.extract()  
        
        if css_selector:
            selected_elements = body.select(css_selector)
            if not selected_elements:
                return {
                    'markdown': '',
                    'cleaned_html': '',
                    'success': True,
                    'media': {'images': [], 'videos': [], 'audios': []},
                    'links': {'internal': [], 'external': []},
                    'metadata': {},
                    'message': f"No elements found for CSS selector: {css_selector}"
                }
                # raise InvalidCSSSelectorError(f"Invalid CSS selector, No elements found for CSS selector: {css_selector}")
            body = soup.new_tag('div')
            for el in selected_elements:
                body.append(el)

        kwargs['exclude_social_media_domains'] = set(kwargs.get('exclude_social_media_domains', []) + SOCIAL_MEDIA_DOMAINS)
        kwargs['exclude_domains'] = set(kwargs.get('exclude_domains', []))
        if kwargs.get('exclude_social_media_links', False):
            kwargs['exclude_domains'] = kwargs['exclude_domains'].union(kwargs['exclude_social_media_domains'])
        
        result_obj = self.process_element(
            url, 
            body, 
            word_count_threshold = word_count_threshold, 
            base_domain=base_domain,
            **kwargs
        )
        
        links = {'internal': [], 'external': []}
        media = result_obj['media']
        internal_links_dict = result_obj['internal_links_dict']
        external_links_dict = result_obj['external_links_dict']
        
        # Update the links dictionary with unique links
        links['internal'] = list(internal_links_dict.values())
        links['external'] = list(external_links_dict.values())

        # # Process images using ThreadPoolExecutor
        imgs = body.find_all('img')
        
        media['images'] = [
            img for result in (self.process_image(img, url, i, len(imgs)) 
                            for i, img in enumerate(imgs))
            if result is not None
            for img in result
        ]

        body = self.flatten_nested_elements(body)
        base64_pattern = re.compile(r'data:image/[^;]+;base64,([^"]+)')
        for img in imgs:
            src = img.get('src', '')
            if base64_pattern.match(src):
                # Replace base64 data with empty string
                img['src'] = base64_pattern.sub('', src)
                
        str_body = ""
        try:
            str_body = body.encode_contents().decode('utf-8')
        except Exception as e:
            # Reset body to the original HTML
            success = False
            body = BeautifulSoup(html, 'html.parser')
            
            # Create a new div with a special ID
            error_div = body.new_tag('div', id='crawl4ai_error_message')
            error_div.string = '''
            Crawl4AI Error: This page is not fully supported.
            
            Possible reasons:
            1. The page may have restrictions that prevent crawling.
            2. The page might not be fully loaded.
            
            Suggestions:
            - Try calling the crawl function with these parameters:
            magic=True,
            - Set headless=False to visualize what's happening on the page.
            
            If the issue persists, please check the page's structure and any potential anti-crawling measures.
            '''
            
            # Append the error div to the body
            body.body.append(error_div)
            str_body = body.encode_contents().decode('utf-8')
            
            print(f"[LOG] 😧 Error: After processing the crawled HTML and removing irrelevant tags, nothing was left in the page. Check the markdown for further details.")
            self._log('error',
                message="After processing the crawled HTML and removing irrelevant tags, nothing was left in the page. Check the markdown for further details.",
                tag="SCRAPE"
            )

        cleaned_html = str_body.replace('\n\n', '\n').replace('  ', ' ')

        # markdown_content = self._generate_markdown_content(
        #     cleaned_html=cleaned_html,
        #     html=html,
        #     url=url,
        #     success=success,
        #     **kwargs
        # )
        
        return {
            # **markdown_content,
            'cleaned_html': cleaned_html,
            'success': success,
            'media': media,
            'links': links,
            'metadata': meta
        }
