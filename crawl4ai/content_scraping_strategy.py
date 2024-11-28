import re  # Point 1: Pre-Compile Regular Expressions
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import asyncio, requests, re, os
from .config import *
from bs4 import element, NavigableString, Comment
from urllib.parse import urljoin
from requests.exceptions import InvalidSchema
# from .content_cleaning_strategy import ContentCleaningStrategy
from .content_filter_strategy import RelevantContentFilter, BM25ContentFilter#, HeuristicContentFilter
from .markdown_generation_strategy import MarkdownGenerationStrategy, DefaultMarkdownGenerator
from .models import MarkdownGenerationResult
from .utils import (
    sanitize_input_encode,
    sanitize_html,
    extract_metadata,
    InvalidCSSSelectorError,
    CustomHTML2Text,
    normalize_url,
    is_external_url    
)
from .tools import profile_and_time

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
    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, level, message, tag="SCRAPE", **kwargs):
        """Helper method to safely use logger."""
        if self.logger:
            log_method = getattr(self.logger, level)
            log_method(message=message, tag=tag, **kwargs)
                
    def scrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        return self._get_content_of_website_optimized(url, html, is_async=False, **kwargs)

    async def ascrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        return await asyncio.to_thread(self._get_content_of_website_optimized, url, html, **kwargs)


    def _generate_markdown_content(self, 
                                 cleaned_html: str,
                                 html: str,
                                 url: str,
                                 success: bool,
                                 **kwargs) -> Dict[str, Any]:
        """Generate markdown content using either new strategy or legacy method.
        
        Args:
            cleaned_html: Sanitized HTML content
            html: Original HTML content
            url: Base URL of the page
            success: Whether scraping was successful
            **kwargs: Additional options including:
                - markdown_generator: Optional[MarkdownGenerationStrategy]
                - html2text: Dict[str, Any] options for HTML2Text
                - content_filter: Optional[RelevantContentFilter]
                - fit_markdown: bool
                - fit_markdown_user_query: Optional[str]
                - fit_markdown_bm25_threshold: float
        
        Returns:
            Dict containing markdown content in various formats
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
                
                help_message = """"""
                
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
        h = CustomHTML2Text()
        h.update_params(**kwargs.get('html2text', {}))            
        markdown = h.handle(cleaned_html)
        markdown = markdown.replace('    ```', '```')
        
        fit_markdown = "Set flag 'fit_markdown' to True to get cleaned HTML content."
        fit_html = "Set flag 'fit_markdown' to True to get cleaned HTML content."
        
        if kwargs.get('content_filter', None) or kwargs.get('fit_markdown', False):
            content_filter = kwargs.get('content_filter', None)
            if not content_filter:
                content_filter = BM25ContentFilter(
                    user_query=kwargs.get('fit_markdown_user_query', None),
                    bm25_threshold=kwargs.get('fit_markdown_bm25_threshold', 1.0)
                )
            fit_html = content_filter.filter_content(html)
            fit_html = '\n'.join('<div>{}</div>'.format(s) for s in fit_html)
            fit_markdown = h.handle(fit_html)

        markdown_v2 = MarkdownGenerationResult(
            raw_markdown=markdown,
            markdown_with_citations=markdown,
            references_markdown=markdown,
            fit_markdown=fit_markdown
        )
        
        return {
            'markdown': markdown,
            'fit_markdown': fit_markdown,
            'fit_html': fit_html,
            'markdown_v2' : markdown_v2
        }


    def _get_content_of_website_optimized(self, url: str, html: str, word_count_threshold: int = MIN_WORD_THRESHOLD, css_selector: str = None, **kwargs) -> Dict[str, Any]:
        success = True
        if not html:
            return None

        # soup = BeautifulSoup(html, 'html.parser')
        soup = BeautifulSoup(html, 'lxml')
        body = soup.body
        
        try:
            meta = extract_metadata("", soup)
        except Exception as e:
            self._log('error', 
                message="Error extracting metadata: {error}",
                tag="SCRAPE",
                params={"error": str(e)}
            )            
            # print('Error extracting metadata:', str(e))
            meta = {}
        
        
        image_description_min_word_threshold = kwargs.get('image_description_min_word_threshold', IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD)

        for tag in kwargs.get('excluded_tags', []) or []:
            for el in body.select(tag):
                el.decompose()
        
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

        links = {'internal': [], 'external': []}
        media = {'images': [], 'videos': [], 'audios': []}
        internal_links_dict = {}
        external_links_dict = {}

        # Extract meaningful text for media files from closest parent
        def find_closest_parent_with_useful_text(tag):
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

        def process_image_old(img, url, index, total_images):
                   
            
            #Check if an image has valid display and inside undesired html elements
            def is_valid_image(img, parent, parent_classes):
                style = img.get('style', '')
                src = img.get('src', '')
                classes_to_check = ['button', 'icon', 'logo']
                tags_to_check = ['button', 'input']
                return all([
                    'display:none' not in style,
                    src,
                    not any(s in var for var in [src, img.get('alt', ''), *parent_classes] for s in classes_to_check),
                    parent.name not in tags_to_check
                ])

            #Score an image for it's usefulness
            def score_image_for_usefulness(img, base_url, index, images_count):
                image_height = img.get('height')
                height_value, height_unit = parse_dimension(image_height)
                image_width =  img.get('width')
                width_value, width_unit = parse_dimension(image_width)
                image_size = 0 #int(fetch_image_file_size(img,base_url) or 0)
                image_src = img.get('src','')
                if "data:image/" in image_src:
                    image_format = image_src.split(',')[0].split(';')[0].split('/')[1]
                else:
                    image_format = os.path.splitext(img.get('src',''))[1].lower()
                # Remove . from format
                image_format = image_format.strip('.').split('?')[0]
                score = 0
                if height_value:
                    if height_unit == 'px' and height_value > 150:
                        score += 1
                    if height_unit in ['%','vh','vmin','vmax'] and height_value >30:
                        score += 1
                if width_value:
                    if width_unit == 'px' and width_value > 150:
                        score += 1
                    if width_unit in ['%','vh','vmin','vmax'] and width_value >30:
                        score += 1
                if image_size > 10000:
                    score += 1
                if img.get('alt') != '':
                    score+=1
                if any(image_format==format for format in ['jpg','png','webp']):
                    score+=1
                if index/images_count<0.5:
                    score+=1
                return score

            if not is_valid_image(img, img.parent, img.parent.get('class', [])):
                return None
                
            score = score_image_for_usefulness(img, url, index, total_images)
            if score <= kwargs.get('image_score_threshold', IMAGE_SCORE_THRESHOLD):
                return None

            base_result = {
                'src': img.get('src', ''),
                'data-src': img.get('data-src', ''),
                'alt': img.get('alt', ''),
                'desc': find_closest_parent_with_useful_text(img),
                'score': score,
                'type': 'image'
            }

            sources = []
            srcset = img.get('srcset', '')
            if srcset:
                sources = parse_srcset(srcset)
                if sources:
                    return [dict(base_result, src=source['url'], width=source['width']) 
                        for source in sources]

            return [base_result]  # Always return a list

        def process_image(img, url, index, total_images):
            parse_srcset = lambda s: [{'url': u.strip().split()[0], 'width': u.strip().split()[-1].rstrip('w') 
                          if ' ' in u else None} 
                         for u in [f"http{p}" for p in s.split("http") if p]]
            
            # Constants for checks
            classes_to_check = frozenset(['button', 'icon', 'logo'])
            tags_to_check = frozenset(['button', 'input'])
            
            # Pre-fetch commonly used attributes
            style = img.get('style', '')
            alt = img.get('alt', '')
            src = img.get('src', '')
            data_src = img.get('data-src', '')
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
            
            image_format = ''
            if "data:image/" in src:
                image_format = src.split(',')[0].split(';')[0].split('/')[1].split(';')[0]
            else:
                image_format = os.path.splitext(src)[1].lower().strip('.').split('?')[0]
            
            if image_format in ('jpg', 'png', 'webp', 'avif'):
                score += 1

            if score <= kwargs.get('image_score_threshold', IMAGE_SCORE_THRESHOLD):
                return None

            # Use set for deduplication
            unique_urls = set()
            image_variants = []
            
            # Generate a unique group ID for this set of variants
            group_id = index 
            
            # Base image info template
            base_info = {
                'alt': alt,
                'desc': find_closest_parent_with_useful_text(img),
                'score': score,
                'type': 'image',
                'group_id': group_id # Group ID for this set of variants
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

        def remove_unwanted_attributes(element, important_attrs, keep_data_attributes=False):
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
        
        def process_element(element: element.PageElement) -> bool:
            try:
                if isinstance(element, NavigableString):
                    if isinstance(element, Comment):
                        element.extract()
                    return False
                
                # if element.name == 'img':
                #     process_image(element, url, 0, 1)
                #     return True

                if element.name in ['script', 'style', 'link', 'meta', 'noscript']:
                    element.decompose()
                    return False

                keep_element = False
                
                exclude_social_media_domains = SOCIAL_MEDIA_DOMAINS + kwargs.get('exclude_social_media_domains', [])
                exclude_social_media_domains = list(set(exclude_social_media_domains))
                
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
                            'title': element.get('title', '').strip()
                        }
                        
                        # Check for duplicates and add to appropriate dictionary
                        is_external = is_external_url(normalized_href, url_base)
                        if is_external:
                            if normalized_href not in external_links_dict:
                                external_links_dict[normalized_href] = link_data
                        else:
                            if normalized_href not in internal_links_dict:
                                internal_links_dict[normalized_href] = link_data
                                
                        keep_element = True
                        
                        # Handle external link exclusions
                        if is_external:
                            if kwargs.get('exclude_external_links', False):
                                element.decompose()
                                return False
                            elif kwargs.get('exclude_social_media_links', False):
                                if any(domain in normalized_href.lower() for domain in exclude_social_media_domains):
                                    element.decompose()
                                    return False
                            elif kwargs.get('exclude_domains', []):
                                if any(domain in normalized_href.lower() for domain in kwargs.get('exclude_domains', [])):
                                    element.decompose()
                                    return False
                                    
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
                            
                        # Check flag if we should remove external images
                        if kwargs.get('exclude_external_images', False):
                            src_url_base = src.split('/')[2]
                            url_base = url.split('/')[2]
                            if url_base not in src_url_base:
                                element.decompose()
                                return False
                            
                        if not kwargs.get('exclude_external_images', False) and kwargs.get('exclude_social_media_links', False):
                            src_url_base = src.split('/')[2]
                            url_base = url.split('/')[2]
                            if any(domain in src for domain in exclude_social_media_domains):
                                element.decompose()
                                return False
                            
                        # Handle exclude domains
                        if kwargs.get('exclude_domains', []):
                            if any(domain in src for domain in kwargs.get('exclude_domains', [])):
                                element.decompose()
                                return False
                        
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
                        'description': find_closest_parent_with_useful_text(element)
                    })
                    source_tags = element.find_all('source')
                    for source_tag in source_tags:
                        media[f"{element.name}s"].append({
                        'src': source_tag.get('src'),
                        'alt': element.get('alt'),
                        'type': element.name,
                        'description': find_closest_parent_with_useful_text(element)
                    })
                    return True  # Always keep video and audio elements

                if element.name in ONLY_TEXT_ELIGIBLE_TAGS:
                    if kwargs.get('only_text', False):
                        element.replace_with(element.get_text())

                try:
                    remove_unwanted_attributes(element, IMPORTANT_ATTRS, kwargs.get('keep_data_attributes', False))
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
                        if process_element(child):
                            keep_element = True
                    

                # Check word count
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
       
        process_element(body)
        
        # Update the links dictionary with unique links
        links['internal'] = list(internal_links_dict.values())
        links['external'] = list(external_links_dict.values())

        # # Process images using ThreadPoolExecutor
        imgs = body.find_all('img')
        
        # For test we use for loop instead of thread
        media['images'] = [
            img for result in (process_image(img, url, i, len(imgs)) 
                            for i, img in enumerate(imgs))
            if result is not None
            for img in result
        ]

        def flatten_nested_elements(node):
            if isinstance(node, NavigableString):
                return node
            if len(node.contents) == 1 and isinstance(node.contents[0], element.Tag) and node.contents[0].name == node.name:
                return flatten_nested_elements(node.contents[0])
            node.contents = [flatten_nested_elements(child) for child in node.contents]
            return node

        body = flatten_nested_elements(body)
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

        markdown_content = self._generate_markdown_content(
            cleaned_html=cleaned_html,
            html=html,
            url=url,
            success=success,
            **kwargs
        )
        
        return {
            **markdown_content,
            'cleaned_html': cleaned_html,
            'success': success,
            'media': media,
            'links': links,
            'metadata': meta
        }
