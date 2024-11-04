import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup, Comment, element, Tag, NavigableString
import json
import html
import re
import os
import platform
from .html2text import HTML2Text
from .prompts import PROMPT_EXTRACT_BLOCKS
from .config import *
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urljoin
import requests
from requests.exceptions import InvalidSchema

class InvalidCSSSelectorError(Exception):
    pass

def calculate_semaphore_count():
    cpu_count = os.cpu_count()
    memory_gb = get_system_memory() / (1024 ** 3)  # Convert to GB
    base_count = max(1, cpu_count // 2)
    memory_based_cap = int(memory_gb / 2)  # Assume 2GB per instance
    return min(base_count, memory_based_cap)

def get_system_memory():
    system = platform.system()
    if system == "Linux":
        with open('/proc/meminfo', 'r') as mem:
            for line in mem:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1]) * 1024  # Convert KB to bytes
    elif system == "Darwin":  # macOS
        import subprocess
        output = subprocess.check_output(['sysctl', '-n', 'hw.memsize']).decode('utf-8')
        return int(output.strip())
    elif system == "Windows":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        c_ulonglong = ctypes.c_ulonglong
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', c_ulonglong),
                ('ullAvailPhys', c_ulonglong),
                ('ullTotalPageFile', c_ulonglong),
                ('ullAvailPageFile', c_ulonglong),
                ('ullTotalVirtual', c_ulonglong),
                ('ullAvailVirtual', c_ulonglong),
                ('ullAvailExtendedVirtual', c_ulonglong),
            ]
        memoryStatus = MEMORYSTATUSEX()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
        return memoryStatus.ullTotalPhys
    else:
        raise OSError("Unsupported operating system")

def get_home_folder():
    home_folder = os.path.join(Path.home(), ".crawl4ai")
    os.makedirs(home_folder, exist_ok=True)
    os.makedirs(f"{home_folder}/cache", exist_ok=True)
    os.makedirs(f"{home_folder}/models", exist_ok=True)
    return home_folder    

def beautify_html(escaped_html):
    """
    Beautifies an escaped HTML string.
    
    Parameters:
    escaped_html (str): A string containing escaped HTML.
    
    Returns:
    str: A beautifully formatted HTML string.
    """
    # Unescape the HTML string
    unescaped_html = html.unescape(escaped_html)
    
    # Use BeautifulSoup to parse and prettify the HTML
    soup = BeautifulSoup(unescaped_html, 'html.parser')
    pretty_html = soup.prettify()
    
    return pretty_html

def split_and_parse_json_objects(json_string):
    """
    Splits a JSON string which is a list of objects and tries to parse each object.
    
    Parameters:
    json_string (str): A string representation of a list of JSON objects, e.g., '[{...}, {...}, ...]'.
    
    Returns:
    tuple: A tuple containing two lists:
        - First list contains all successfully parsed JSON objects.
        - Second list contains the string representations of all segments that couldn't be parsed.
    """
    # Trim the leading '[' and trailing ']'
    if json_string.startswith('[') and json_string.endswith(']'):
        json_string = json_string[1:-1].strip()
    
    # Split the string into segments that look like individual JSON objects
    segments = []
    depth = 0
    start_index = 0
    
    for i, char in enumerate(json_string):
        if char == '{':
            if depth == 0:
                start_index = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                segments.append(json_string[start_index:i+1])
    
    # Try parsing each segment
    parsed_objects = []
    unparsed_segments = []
    
    for segment in segments:
        try:
            obj = json.loads(segment)
            parsed_objects.append(obj)
        except json.JSONDecodeError:
            unparsed_segments.append(segment)
    
    return parsed_objects, unparsed_segments

def sanitize_html(html):
    # Replace all unwanted and special characters with an empty string
    sanitized_html = html
    # sanitized_html = re.sub(r'[^\w\s.,;:!?=\[\]{}()<>\/\\\-"]', '', html)

    # Escape all double and single quotes
    sanitized_html = sanitized_html.replace('"', '\\"').replace("'", "\\'")

    return sanitized_html

def sanitize_input_encode(text: str) -> str:
    """Sanitize input to handle potential encoding issues."""
    try:
        # Attempt to encode and decode as UTF-8 to handle potential encoding issues
        return text.encode('utf-8', errors='ignore').decode('utf-8')
    except UnicodeEncodeError as e:
        print(f"Warning: Encoding issue detected. Some characters may be lost. Error: {e}")
        # Fall back to ASCII if UTF-8 fails
        return text.encode('ascii', errors='ignore').decode('ascii')

def escape_json_string(s):
    """
    Escapes characters in a string to be JSON safe.

    Parameters:
    s (str): The input string to be escaped.

    Returns:
    str: The escaped string, safe for JSON encoding.
    """
    # Replace problematic backslash first
    s = s.replace('\\', '\\\\')
    
    # Replace the double quote
    s = s.replace('"', '\\"')
    
    # Escape control characters
    s = s.replace('\b', '\\b')
    s = s.replace('\f', '\\f')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    
    # Additional problematic characters
    # Unicode control characters
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda x: '\\u{:04x}'.format(ord(x.group())), s)
    
    return s

class CustomHTML2Text_v0(HTML2Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inside_pre = False
        self.inside_code = False
        
        self.skip_internal_links = False
        self.single_line_break = False
        self.mark_code = False
        self.include_sup_sub = False
        self.body_width = 0
        self.ignore_mailto_links = True
        self.ignore_links = False
        self.escape_backslash = False
        self.escape_dot = False
        self.escape_plus = False
        self.escape_dash = False
        self.escape_snob = False


    def handle_tag(self, tag, attrs, start):
        if tag == 'pre':
            if start:
                self.o('```\n')
                self.inside_pre = True
            else:
                self.o('\n```')
                self.inside_pre = False
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            pass


        # elif tag == 'code' and not self.inside_pre:
        #     if start:
        #         if not self.inside_pre:
        #             self.o('`')
        #         self.inside_code = True
        #     else:
        #         if not self.inside_pre:
        #             self.o('`')
        #         self.inside_code = False

        super().handle_tag(tag, attrs, start)

def replace_inline_tags(soup, tags, only_text=False):
    tag_replacements = {
        'b': lambda tag: f"**{tag.text}**",
        'i': lambda tag: f"*{tag.text}*",
        'u': lambda tag: f"__{tag.text}__",
        'span': lambda tag: f"{tag.text}",
        'del': lambda tag: f"~~{tag.text}~~",
        'ins': lambda tag: f"++{tag.text}++",
        'sub': lambda tag: f"~{tag.text}~",
        'sup': lambda tag: f"^^{tag.text}^^",
        'strong': lambda tag: f"**{tag.text}**",
        'em': lambda tag: f"*{tag.text}*",
        'code': lambda tag: f"`{tag.text}`",
        'kbd': lambda tag: f"`{tag.text}`",
        'var': lambda tag: f"_{tag.text}_",
        's': lambda tag: f"~~{tag.text}~~",
        'q': lambda tag: f'"{tag.text}"',
        'abbr': lambda tag: f"{tag.text} ({tag.get('title', '')})",
        'cite': lambda tag: f"_{tag.text}_",
        'dfn': lambda tag: f"_{tag.text}_",
        'time': lambda tag: f"{tag.text}",
        'small': lambda tag: f"<small>{tag.text}</small>",
        'mark': lambda tag: f"=={tag.text}=="
    }
    
    replacement_data = [(tag, tag_replacements.get(tag, lambda t: t.text)) for tag in tags]

    for tag_name, replacement_func in replacement_data:
        for tag in soup.find_all(tag_name):
            replacement_text = tag.text if only_text else replacement_func(tag)
            tag.replace_with(replacement_text)

    return soup    

    # for tag_name in tags:
    #     for tag in soup.find_all(tag_name):
    #         if not only_text:
    #             replacement_text = tag_replacements.get(tag_name, lambda t: t.text)(tag)
    #             tag.replace_with(replacement_text)
    #         else:
    #             tag.replace_with(tag.text)

    # return soup

def get_content_of_website(url, html, word_count_threshold = MIN_WORD_THRESHOLD, css_selector = None, **kwargs):
    try:
        if not html:
            return None
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Get the content within the <body> tag
        body = soup.body
        
        # If css_selector is provided, extract content based on the selector
        if css_selector:
            selected_elements = body.select(css_selector)
            if not selected_elements:
                raise InvalidCSSSelectorError(f"Invalid CSS selector , No elements found for CSS selector: {css_selector}")
            div_tag = soup.new_tag('div')
            for el in selected_elements:
                div_tag.append(el)
            body = div_tag
            
        links = {
            'internal': [],
            'external': []
        }
        
        # Extract all internal and external links
        for a in body.find_all('a', href=True):
            href = a['href']
            url_base = url.split('/')[2]
            if href.startswith('http') and url_base not in href:
                links['external'].append({
                    'href': href,
                    'text': a.get_text()
                })
            else:
                links['internal'].append(
                    {
                        'href': href,
                        'text': a.get_text()
                    }
                )

        # Remove script, style, and other tags that don't carry useful content from body
        for tag in body.find_all(['script', 'style', 'link', 'meta', 'noscript']):
            tag.decompose()

        # Remove all attributes from remaining tags in body, except for img tags
        for tag in body.find_all():
            if tag.name != 'img':
                tag.attrs = {}

        # Extract all img tgas int0 [{src: '', alt: ''}]
        media = {
            'images': [],
            'videos': [],
            'audios': []
        }
        for img in body.find_all('img'):
            media['images'].append({
                'src': img.get('src'),
                'alt': img.get('alt'),
                "type": "image"
            })
            
        # Extract all video tags into [{src: '', alt: ''}]
        for video in body.find_all('video'):
            media['videos'].append({
                'src': video.get('src'),
                'alt': video.get('alt'),
                "type": "video"
            })
            
        # Extract all audio tags into [{src: '', alt: ''}]
        for audio in body.find_all('audio'):
            media['audios'].append({
                'src': audio.get('src'),
                'alt': audio.get('alt'),
                "type": "audio"
            })
        
        # Replace images with their alt text or remove them if no alt text is available
        for img in body.find_all('img'):
            alt_text = img.get('alt')
            if alt_text:
                img.replace_with(soup.new_string(alt_text))
            else:
                img.decompose()


        # Create a function that replace content of all"pre" tag with its inner text
        def replace_pre_tags_with_text(node):
            for child in node.find_all('pre'):
                # set child inner html to its text
                child.string = child.get_text()
            return node
        
        # Replace all "pre" tags with their inner text
        body = replace_pre_tags_with_text(body)
        
        # Replace inline tags with their text content
        body = replace_inline_tags(
            body, 
            ['b', 'i', 'u', 'span', 'del', 'ins', 'sub', 'sup', 'strong', 'em', 'code', 'kbd', 'var', 's', 'q', 'abbr', 'cite', 'dfn', 'time', 'small', 'mark'],
            only_text=kwargs.get('only_text', False)
        )

        # Recursively remove empty elements, their parent elements, and elements with word count below threshold
        def remove_empty_and_low_word_count_elements(node, word_count_threshold):
            for child in node.contents:
                if isinstance(child, element.Tag):
                    remove_empty_and_low_word_count_elements(child, word_count_threshold)
                    word_count = len(child.get_text(strip=True).split())
                    if (len(child.contents) == 0 and not child.get_text(strip=True)) or word_count < word_count_threshold:
                        child.decompose()
            return node

        body = remove_empty_and_low_word_count_elements(body, word_count_threshold)
        
        def remove_small_text_tags(body: Tag, word_count_threshold: int = MIN_WORD_THRESHOLD):
            # We'll use a list to collect all tags that don't meet the word count requirement
            tags_to_remove = []

            # Traverse all tags in the body
            for tag in body.find_all(True):  # True here means all tags
                # Check if the tag contains text and if it's not just whitespace
                if tag.string and tag.string.strip():
                    # Split the text by spaces and count the words
                    word_count = len(tag.string.strip().split())
                    # If the word count is less than the threshold, mark the tag for removal
                    if word_count < word_count_threshold:
                        tags_to_remove.append(tag)

            # Remove all marked tags from the tree
            for tag in tags_to_remove:
                tag.decompose()  # or tag.extract() to remove and get the element

            return body
        
    
        # Remove small text tags
        body = remove_small_text_tags(body, word_count_threshold)       
        
        def is_empty_or_whitespace(tag: Tag):
            if isinstance(tag, NavigableString):
                return not tag.strip()
            # Check if the tag itself is empty or all its children are empty/whitespace
            if not tag.contents:
                return True
            return all(is_empty_or_whitespace(child) for child in tag.contents)

        def remove_empty_tags(body: Tag):
            # Continue processing until no more changes are made
            changes = True
            while changes:
                changes = False
                # Collect all tags that are empty or contain only whitespace
                empty_tags = [tag for tag in body.find_all(True) if is_empty_or_whitespace(tag)]
                for tag in empty_tags:
                    # If a tag is empty, decompose it
                    tag.decompose()
                    changes = True  # Mark that a change was made

            return body        

        
        # Remove empty tags
        body = remove_empty_tags(body)
        
        # Flatten nested elements with only one child of the same type
        def flatten_nested_elements(node):
            for child in node.contents:
                if isinstance(child, element.Tag):
                    flatten_nested_elements(child)
                    if len(child.contents) == 1 and child.contents[0].name == child.name:
                        # print('Flattening:', child.name)
                        child_content = child.contents[0]
                        child.replace_with(child_content)
                        
            return node

        body = flatten_nested_elements(body)
        


        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)): 
            comment.extract()

        # Remove consecutive empty newlines and replace multiple spaces with a single space
        cleaned_html = str(body).replace('\n\n', '\n').replace('  ', ' ')
        
        # Sanitize the cleaned HTML content
        cleaned_html = sanitize_html(cleaned_html)
        # sanitized_html = escape_json_string(cleaned_html)

        # Convert cleaned HTML to Markdown
        h = html2text.HTML2Text()
        h = CustomHTML2Text()
        h.ignore_links = True
        markdown = h.handle(cleaned_html)
        markdown = markdown.replace('    ```', '```')
            
        try:
            meta = extract_metadata(html, soup)
        except Exception as e:
            print('Error extracting metadata:', str(e))
            meta = {}
                
        
        # Return the Markdown content
        return{
            'markdown': markdown,
            'cleaned_html': cleaned_html,
            'success': True,
            'media': media,
            'links': links,
            'metadata': meta
        }

    except Exception as e:
        print('Error processing HTML content:', str(e))
        raise InvalidCSSSelectorError(f"Invalid CSS selector: {css_selector}") from e

def get_content_of_website_optimized(url: str, html: str, word_count_threshold: int = MIN_WORD_THRESHOLD, css_selector: str = None, **kwargs) -> Dict[str, Any]:
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body
    
    image_description_min_word_threshold = kwargs.get('image_description_min_word_threshold', IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD)

    for tag in kwargs.get('excluded_tags', []) or []:
        for el in body.select(tag):
            el.decompose()
        
    if css_selector:
        selected_elements = body.select(css_selector)
        if not selected_elements:
            raise InvalidCSSSelectorError(f"Invalid CSS selector, No elements found for CSS selector: {css_selector}")
        body = soup.new_tag('div')
        for el in selected_elements:
            body.append(el)

    links = {'internal': [], 'external': []}
    media = {'images': [], 'videos': [], 'audios': []}

    # Extract meaningful text for media files from closest parent
    def find_closest_parent_with_useful_text(tag):
            current_tag = tag
            while current_tag:
                current_tag = current_tag.parent
                # Get the text content from the parent tag
                if current_tag:
                    text_content = current_tag.get_text(separator=' ',strip=True)
                    # Check if the text content has at least word_count_threshold
                    if len(text_content.split()) >= image_description_min_word_threshold:
                        return text_content
            return None

    def process_image(img, url, index, total_images):
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
            # Function to parse image height/width value and units
            def parse_dimension(dimension):
                if dimension:
                    match = re.match(r"(\d+)(\D*)", dimension)
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

            image_height = img.get('height')
            height_value, height_unit = parse_dimension(image_height)
            image_width =  img.get('width')
            width_value, width_unit = parse_dimension(image_width)
            image_size = 0 #int(fetch_image_file_size(img,base_url) or 0)
            image_format = os.path.splitext(img.get('src',''))[1].lower()
            # Remove . from format
            image_format = image_format.strip('.')
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
        if score <= IMAGE_SCORE_THRESHOLD:
            return None
        return {
            'src': img.get('src', '').replace('\\"', '"').strip(),
            'alt': img.get('alt', ''),
            'desc': find_closest_parent_with_useful_text(img),
            'score': score,
            'type': 'image'
        }

    def process_element(element: element.PageElement) -> bool:
        try:
            if isinstance(element, NavigableString):
                if isinstance(element, Comment):
                    element.extract()
                return False

            if element.name in ['script', 'style', 'link', 'meta', 'noscript']:
                element.decompose()
                return False

            keep_element = False

            if element.name == 'a' and element.get('href'):
                href = element['href']
                url_base = url.split('/')[2]
                link_data = {'href': href, 'text': element.get_text()}
                if href.startswith('http') and url_base not in href:
                    links['external'].append(link_data)
                else:
                    links['internal'].append(link_data)
                keep_element = True

            elif element.name == 'img':
                return True  # Always keep image elements

            elif element.name in ['video', 'audio']:
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

            if element.name != 'pre':
                if element.name in ['b', 'i', 'u', 'span', 'del', 'ins', 'sub', 'sup', 'strong', 'em', 'code', 'kbd', 'var', 's', 'q', 'abbr', 'cite', 'dfn', 'time', 'small', 'mark']:
                    if kwargs.get('only_text', False):
                        element.replace_with(element.get_text())
                    else:
                        element.unwrap()
                elif element.name != 'img':
                    element.attrs = {}

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
            print('Error processing element:', str(e))
            return False

    #process images by filtering and extracting contextual text from the page
    imgs = body.find_all('img')
    media['images'] = [
        result for result in
        (process_image(img, url, i, len(imgs)) for i, img in enumerate(imgs))
        if result is not None
    ]

    process_element(body)

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
            img['src'] = base64_pattern.sub('', src)

    cleaned_html = str(body).replace('\n\n', '\n').replace('  ', ' ')
    cleaned_html = sanitize_html(cleaned_html)

    h = CustomHTML2Text()
    h.ignore_links = True
    markdown = h.handle(cleaned_html)
    markdown = markdown.replace('    ```', '```')

    try:
        meta = extract_metadata(html, soup)
    except Exception as e:
        print('Error extracting metadata:', str(e))
        meta = {}

    return {
        'markdown': markdown,
        'cleaned_html': cleaned_html,
        'success': True,
        'media': media,
        'links': links,
        'metadata': meta
    }

def extract_metadata(html, soup = None):
    metadata = {}
    
    if not html:
        return metadata
    
    # Parse HTML content with BeautifulSoup
    if not soup:
        soup = BeautifulSoup(html, 'html.parser')

    # Title
    title_tag = soup.find('title')
    metadata['title'] = title_tag.string if title_tag else None

    # Meta description
    description_tag = soup.find('meta', attrs={'name': 'description'})
    metadata['description'] = description_tag['content'] if description_tag else None

    # Meta keywords
    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    metadata['keywords'] = keywords_tag['content'] if keywords_tag else None

    # Meta author
    author_tag = soup.find('meta', attrs={'name': 'author'})
    metadata['author'] = author_tag['content'] if author_tag else None

    # Open Graph metadata
    og_tags = soup.find_all('meta', attrs={'property': lambda value: value and value.startswith('og:')})
    for tag in og_tags:
        property_name = tag['property']
        metadata[property_name] = tag['content']

    # Twitter Card metadata
    twitter_tags = soup.find_all('meta', attrs={'name': lambda value: value and value.startswith('twitter:')})
    for tag in twitter_tags:
        property_name = tag['name']
        metadata[property_name] = tag['content']

    return metadata

def extract_xml_tags(string):
    tags = re.findall(r'<(\w+)>', string)
    return list(set(tags))

def extract_xml_data(tags, string):
    data = {}

    for tag in tags:
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, string, re.DOTALL)
        if match:
            data[tag] = match.group(1).strip()
        else:
            data[tag] = ""

    return data
    
# Function to perform the completion with exponential backoff
def perform_completion_with_backoff(
    provider, 
    prompt_with_variables, 
    api_token, 
    json_response = False, 
    base_url=None,
    **kwargs
    ):
    from litellm import completion 
    from litellm.exceptions import RateLimitError
    max_attempts = 3
    base_delay = 2  # Base delay in seconds, you can adjust this based on your needs
    
    extra_args = {}
    if json_response:
        extra_args["response_format"] = { "type": "json_object" }
        
    if kwargs.get("extra_args"):
        extra_args.update(kwargs["extra_args"])
    
    for attempt in range(max_attempts):
        try:
            response =completion(
                model=provider,
                messages=[
                    {"role": "user", "content": prompt_with_variables}
                ],
                temperature=0.01,
                api_key=api_token,
                base_url=base_url,
                **extra_args
            )
            return response  # Return the successful response
        except RateLimitError as e:
            print("Rate limit error:", str(e))
            
            # Check if we have exhausted our max attempts
            if attempt < max_attempts - 1:
                # Calculate the delay and wait
                delay = base_delay * (2 ** attempt)  # Exponential backoff formula
                print(f"Waiting for {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                # Return an error response after exhausting all retries
                return [{
                    "index": 0,
                    "tags": ["error"],
                    "content": ["Rate limit error. Please try again later."]
                }]
    
def extract_blocks(url, html, provider = DEFAULT_PROVIDER, api_token = None, base_url = None):
    # api_token = os.getenv('GROQ_API_KEY', None) if not api_token else api_token
    api_token = PROVIDER_MODELS.get(provider, None) if not api_token else api_token
    
    variable_values = {
        "URL": url,
        "HTML": escape_json_string(sanitize_html(html)),
    }

    prompt_with_variables = PROMPT_EXTRACT_BLOCKS
    for variable in variable_values:
        prompt_with_variables = prompt_with_variables.replace(
            "{" + variable + "}", variable_values[variable]
        )
        
    response = perform_completion_with_backoff(provider, prompt_with_variables, api_token, base_url=base_url)
        
    try:
        blocks = extract_xml_data(["blocks"], response.choices[0].message.content)['blocks']
        blocks = json.loads(blocks)
        ## Add error: False to the blocks
        for block in blocks:
            block['error'] = False
    except Exception as e:
        parsed, unparsed = split_and_parse_json_objects(response.choices[0].message.content)
        blocks = parsed
        # Append all unparsed segments as onr error block and content is list of unparsed segments
        if unparsed:
            blocks.append({
                "index": 0,
                "error": True,
                "tags": ["error"],
                "content": unparsed
            })
    return blocks

def extract_blocks_batch(batch_data, provider = "groq/llama3-70b-8192", api_token = None):
    api_token = os.getenv('GROQ_API_KEY', None) if not api_token else api_token
    from litellm import batch_completion
    messages = []
    
    for url, html in batch_data:        
        variable_values = {
            "URL": url,
            "HTML": html,
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )
            
        messages.append([{"role": "user", "content": prompt_with_variables}])
        
    
    responses = batch_completion(
        model = provider,
        messages = messages,
        temperature = 0.01
    )
    
    all_blocks = []
    for response in responses:    
        try:
            blocks = extract_xml_data(["blocks"], response.choices[0].message.content)['blocks']
            blocks = json.loads(blocks)

        except Exception as e:
            blocks = [{
                "index": 0,
                "tags": ["error"],
                "content": ["Error extracting blocks from the HTML content. Choose another provider/model or try again."],
                "questions": ["What went wrong during the block extraction process?"]
            }]
        all_blocks.append(blocks)
    
    return sum(all_blocks, [])

def merge_chunks_based_on_token_threshold(chunks, token_threshold):
    """
    Merges small chunks into larger ones based on the total token threshold.

    :param chunks: List of text chunks to be merged based on token count.
    :param token_threshold: Max number of tokens for each merged chunk.
    :return: List of merged text chunks.
    """
    merged_sections = []
    current_chunk = []
    total_token_so_far = 0

    for chunk in chunks:
        chunk_token_count = len(chunk.split()) * 1.3  # Estimate token count with a factor
        if total_token_so_far + chunk_token_count < token_threshold:
            current_chunk.append(chunk)
            total_token_so_far += chunk_token_count
        else:
            if current_chunk:
                merged_sections.append('\n\n'.join(current_chunk))
            current_chunk = [chunk]
            total_token_so_far = chunk_token_count

    # Add the last chunk if it exists
    if current_chunk:
        merged_sections.append('\n\n'.join(current_chunk))

    return merged_sections

def process_sections(url: str, sections: list, provider: str, api_token: str, base_url=None) -> list:
    extracted_content = []
    if provider.startswith("groq/"):
        # Sequential processing with a delay
        for section in sections:
            extracted_content.extend(extract_blocks(url, section, provider, api_token, base_url=base_url))
            time.sleep(0.5)  # 500 ms delay between each processing
    else:
        # Parallel processing using ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(extract_blocks, url, section, provider, api_token, base_url=base_url) for section in sections]
            for future in as_completed(futures):
                extracted_content.extend(future.result())
    
    return extracted_content

def wrap_text(draw, text, font, max_width):
    # Wrap the text to fit within the specified width
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line)
    return '\n'.join(lines)

def format_html(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    return soup.prettify()

def normalize_url(href, base_url):
    """Normalize URLs to ensure consistent format"""
    from urllib.parse import urljoin, urlparse

    # Parse base URL to get components
    parsed_base = urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        raise ValueError(f"Invalid base URL format: {base_url}")

    # Use urljoin to handle all cases
    normalized = urljoin(base_url, href.strip())
    return normalized

def normalize_url_tmp(href, base_url):
    """Normalize URLs to ensure consistent format"""
    # Extract protocol and domain from base URL
    try:
        base_parts = base_url.split('/')
        protocol = base_parts[0]
        domain = base_parts[2]
    except IndexError:
        raise ValueError(f"Invalid base URL format: {base_url}")
    
    # Handle special protocols
    special_protocols = {'mailto:', 'tel:', 'ftp:', 'file:', 'data:', 'javascript:'}
    if any(href.lower().startswith(proto) for proto in special_protocols):
        return href.strip()
        
    # Handle anchor links
    if href.startswith('#'):
        return f"{base_url}{href}"
        
    # Handle protocol-relative URLs
    if href.startswith('//'):
        return f"{protocol}{href}"
        
    # Handle root-relative URLs
    if href.startswith('/'):
        return f"{protocol}//{domain}{href}"
        
    # Handle relative URLs
    if not href.startswith(('http://', 'https://')):
        # Remove leading './' if present
        href = href.lstrip('./')
        return f"{protocol}//{domain}/{href}"
        
    return href.strip()

def is_external_url(url, base_domain):
    """Determine if a URL is external"""
    special_protocols = {'mailto:', 'tel:', 'ftp:', 'file:', 'data:', 'javascript:'}
    if any(url.lower().startswith(proto) for proto in special_protocols):
        return True
        
    try:
        # Handle URLs with protocol
        if url.startswith(('http://', 'https://')):
            url_domain = url.split('/')[2]
            return base_domain.lower() not in url_domain.lower()
    except IndexError:
        return False
        
    return False
