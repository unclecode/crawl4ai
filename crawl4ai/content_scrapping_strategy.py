from abc import ABC, abstractmethod
from typing import Dict, Any
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import asyncio, requests, re, os
from .config import *
from bs4 import element, NavigableString, Comment
from urllib.parse import urljoin
from requests.exceptions import InvalidSchema

from .utils import (
    sanitize_input_encode,
    sanitize_html,
    extract_metadata,
    InvalidCSSSelectorError,
    CustomHTML2Text
)



class ContentScrappingStrategy(ABC):
    @abstractmethod
    def scrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def ascrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        pass

class WebScrappingStrategy(ContentScrappingStrategy):
    def scrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        return self._get_content_of_website_optimized(url, html, is_async=False, **kwargs)

    async def ascrap(self, url: str, html: str, **kwargs) -> Dict[str, Any]:
        return await asyncio.to_thread(self._get_content_of_website_optimized, url, html, **kwargs)

    def _get_content_of_website_optimized(self, url: str, html: str, word_count_threshold: int = MIN_WORD_THRESHOLD, css_selector: str = None, **kwargs) -> Dict[str, Any]:
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
                'src': img.get('src', ''),
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
                    if element.name == 'img':
                        process_image(element, url, 0, 1)
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
        # imgs = body.find_all('img')
        # media['images'] = [
        #     result for result in
        #     (process_image(img, url, i, len(imgs)) for i, img in enumerate(imgs))
        #     if result is not None
        # ]
        
        process_element(body)

        # # Process images using ThreadPoolExecutor
        imgs = body.find_all('img')
        with ThreadPoolExecutor() as executor:
            image_results = list(executor.map(process_image, imgs, [url]*len(imgs), range(len(imgs)), [len(imgs)]*len(imgs)))
        media['images'] = [result for result in image_results if result is not None]

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
