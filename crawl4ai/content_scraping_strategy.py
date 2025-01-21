import re
from itertools import chain
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import asyncio
import requests
from .config import (
    MIN_WORD_THRESHOLD,
    IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
    IMAGE_SCORE_THRESHOLD,
    ONLY_TEXT_ELIGIBLE_TAGS,
    IMPORTANT_ATTRS,
    SOCIAL_MEDIA_DOMAINS,
)
from bs4 import NavigableString, Comment
from bs4 import PageElement, Tag
from urllib.parse import urljoin
from requests.exceptions import InvalidSchema
from .utils import (
    extract_metadata,
    normalize_url,
    is_external_url,
    get_base_domain,
    extract_metadata_using_lxml,
)
from lxml import etree
from lxml import html as lhtml
from typing import List
from .models import ScrapingResult, MediaItem, Link, Media, Links

# Pre-compile regular expressions for Open Graph and Twitter metadata
OG_REGEX = re.compile(r"^og:")
TWITTER_REGEX = re.compile(r"^twitter:")
DIMENSION_REGEX = re.compile(r"(\d+)(\D*)")


# Function to parse srcset
def parse_srcset(s: str) -> List[Dict]:
    if not s:
        return []
    variants = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        parts = part.split()
        if len(parts) >= 1:
            url = parts[0]
            width = (
                parts[1].rstrip("w")
                if len(parts) > 1 and parts[1].endswith("w")
                else None
            )
            variants.append({"url": url, "width": width})
    return variants


# Function to parse image height/width value and units
def parse_dimension(dimension):
    if dimension:
        # match = re.match(r"(\d+)(\D*)", dimension)
        match = DIMENSION_REGEX.match(dimension)
        if match:
            number = int(match.group(1))
            unit = match.group(2) or "px"  # Default unit is 'px' if not specified
            return number, unit
    return None, None


# Fetch image file metadata to extract size and extension
def fetch_image_file_size(img, base_url):
    # If src is relative path construct full URL, if not it may be CDN URL
    img_url = urljoin(base_url, img.get("src"))
    try:
        response = requests.head(img_url)
        if response.status_code == 200:
            return response.headers.get("Content-Length", None)
        else:
            print(f"Failed to retrieve file size for {img_url}")
            return None
    except InvalidSchema:
        return None
    finally:
        return


class ContentScrapingStrategy(ABC):
    @abstractmethod
    def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        pass

    @abstractmethod
    async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
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

    def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        """
        Main entry point for content scraping.

        Args:
            url (str): The URL of the page to scrape.
            html (str): The HTML content of the page.
            **kwargs: Additional keyword arguments.

        Returns:
            ScrapingResult: A structured result containing the scraped content.
        """
        raw_result = self._scrap(url, html, is_async=False, **kwargs)
        if raw_result is None:
            return ScrapingResult(
                cleaned_html="",
                success=False,
                media=Media(),
                links=Links(),
                metadata={},
            )

        # Convert media items
        media = Media(
            images=[
                MediaItem(**img)
                for img in raw_result.get("media", {}).get("images", [])
                if img
            ],
            videos=[
                MediaItem(**vid)
                for vid in raw_result.get("media", {}).get("videos", [])
                if vid
            ],
            audios=[
                MediaItem(**aud)
                for aud in raw_result.get("media", {}).get("audios", [])
                if aud
            ],
        )

        # Convert links
        links = Links(
            internal=[
                Link(**link)
                for link in raw_result.get("links", {}).get("internal", [])
                if link
            ],
            external=[
                Link(**link)
                for link in raw_result.get("links", {}).get("external", [])
                if link
            ],
        )

        return ScrapingResult(
            cleaned_html=raw_result.get("cleaned_html", ""),
            success=raw_result.get("success", False),
            media=media,
            links=links,
            metadata=raw_result.get("metadata", {}),
        )

    async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        """
        Main entry point for asynchronous content scraping.

        Args:
            url (str): The URL of the page to scrape.
            html (str): The HTML content of the page.
            **kwargs: Additional keyword arguments.

        Returns:
            ScrapingResult: A structured result containing the scraped content.
        """
        return await asyncio.to_thread(self._scrap, url, html, **kwargs)

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
        if (
            len(node.contents) == 1
            and isinstance(node.contents[0], Tag)
            and node.contents[0].name == node.name
        ):
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
        image_description_min_word_threshold = kwargs.get(
            "image_description_min_word_threshold", IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
        )
        current_tag = tag
        while current_tag:
            current_tag = current_tag.parent
            # Get the text content of the parent tag
            if current_tag:
                text_content = current_tag.get_text(separator=" ", strip=True)
                # Check if the text content has at least word_count_threshold
                if len(text_content.split()) >= image_description_min_word_threshold:
                    return text_content
        return None

    def remove_unwanted_attributes(
        self, element, important_attrs, keep_data_attributes=False
    ):
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
                    if not attr.startswith("data-"):
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
        # parse_srcset = lambda s: [{'url': u.strip().split()[0], 'width': u.strip().split()[-1].rstrip('w')
        #                 if ' ' in u else None}
        #                 for u in [f"http{p}" for p in s.split("http") if p]]

        # Constants for checks
        classes_to_check = frozenset(["button", "icon", "logo"])
        tags_to_check = frozenset(["button", "input"])
        image_formats = frozenset(["jpg", "jpeg", "png", "webp", "avif", "gif"])

        # Pre-fetch commonly used attributes
        style = img.get("style", "")
        alt = img.get("alt", "")
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        srcset = img.get("srcset", "")
        data_srcset = img.get("data-srcset", "")
        width = img.get("width")
        height = img.get("height")
        parent = img.parent
        parent_classes = parent.get("class", [])

        # Quick validation checks
        if (
            "display:none" in style
            or parent.name in tags_to_check
            or any(c in cls for c in parent_classes for cls in classes_to_check)
            or any(c in src for c in classes_to_check)
            or any(c in alt for c in classes_to_check)
        ):
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
        score += index / total_images < 0.5

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
        if img.find_parent("picture"):
            score += 1

        # Detect format from any available source
        detected_format = None
        for url in [src, data_src, srcset, data_srcset]:
            if url:
                format_matches = [fmt for fmt in image_formats if fmt in url.lower()]
                if format_matches:
                    detected_format = format_matches[0]
                    break

        if score <= kwargs.get("image_score_threshold", IMAGE_SCORE_THRESHOLD):
            return None

        # Use set for deduplication
        unique_urls = set()
        image_variants = []

        # Generate a unique group ID for this set of variants
        group_id = index

        # Base image info template
        base_info = {
            "alt": alt,
            "desc": self.find_closest_parent_with_useful_text(img, **kwargs),
            "score": score,
            "type": "image",
            "group_id": group_id,  # Group ID for this set of variants
            "format": detected_format,
        }

        # Inline function for adding variants
        def add_variant(src, width=None):
            if src and not src.startswith("data:") and src not in unique_urls:
                unique_urls.add(src)
                image_variants.append({**base_info, "src": src, "width": width})

        # Process all sources
        add_variant(src)
        add_variant(data_src)

        # Handle srcset and data-srcset in one pass
        for attr in ("srcset", "data-srcset"):
            if value := img.get(attr):
                for source in parse_srcset(value):
                    add_variant(source["url"], source["width"])

        # Quick picture element check
        if picture := img.find_parent("picture"):
            for source in picture.find_all("source"):
                if srcset := source.get("srcset"):
                    for src in parse_srcset(srcset):
                        add_variant(src["url"], src["width"])

        # Framework-specific attributes in one pass
        for attr, value in img.attrs.items():
            if (
                attr.startswith("data-")
                and ("src" in attr or "srcset" in attr)
                and "http" in value
            ):
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
        media = {"images": [], "videos": [], "audios": []}
        internal_links_dict = {}
        external_links_dict = {}
        self._process_element(
            url, element, media, internal_links_dict, external_links_dict, **kwargs
        )
        return {
            "media": media,
            "internal_links_dict": internal_links_dict,
            "external_links_dict": external_links_dict,
        }

    def _process_element(
        self,
        url,
        element: PageElement,
        media: Dict[str, Any],
        internal_links_dict: Dict[str, Any],
        external_links_dict: Dict[str, Any],
        **kwargs,
    ) -> bool:
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

            if element.name in ["script", "style", "link", "meta", "noscript"]:
                element.decompose()
                return False

            keep_element = False

            exclude_domains = kwargs.get("exclude_domains", [])
            # exclude_social_media_domains = kwargs.get('exclude_social_media_domains', set(SOCIAL_MEDIA_DOMAINS))
            # exclude_social_media_domains = SOCIAL_MEDIA_DOMAINS + kwargs.get('exclude_social_media_domains', [])
            # exclude_social_media_domains = list(set(exclude_social_media_domains))

            try:
                if element.name == "a" and element.get("href"):
                    href = element.get("href", "").strip()
                    if not href:  # Skip empty hrefs
                        return False

                    # url_base = url.split("/")[2]

                    # Normalize the URL
                    try:
                        normalized_href = normalize_url(href, url)
                    except ValueError:
                        # logging.warning(f"Invalid URL format: {href}, Error: {str(e)}")
                        return False

                    link_data = {
                        "href": normalized_href,
                        "text": element.get_text().strip(),
                        "title": element.get("title", "").strip(),
                        "base_domain": base_domain,
                    }

                    is_external = is_external_url(normalized_href, base_domain)

                    keep_element = True

                    # Handle external link exclusions
                    if is_external:
                        link_base_domain = get_base_domain(normalized_href)
                        link_data["base_domain"] = link_base_domain
                        if kwargs.get("exclude_external_links", False):
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
                if element.name == "img":
                    potential_sources = [
                        "src",
                        "data-src",
                        "srcset" "data-lazy-src",
                        "data-original",
                    ]
                    src = element.get("src", "")
                    while not src and potential_sources:
                        src = element.get(potential_sources.pop(0), "")
                    if not src:
                        element.decompose()
                        return False

                    # If it is srcset pick up the first image
                    if "srcset" in element.attrs:
                        src = element.attrs["srcset"].split(",")[0].split(" ")[0]

                    # If image src is internal, then skip
                    if not is_external_url(src, base_domain):
                        return True

                    image_src_base_domain = get_base_domain(src)

                    # Check flag if we should remove external images
                    if kwargs.get("exclude_external_images", False):
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
            except Exception:
                raise "Error processing images"

            # Check if flag to remove all forms is set
            if kwargs.get("remove_forms", False) and element.name == "form":
                element.decompose()
                return False

            if element.name in ["video", "audio"]:
                media[f"{element.name}s"].append(
                    {
                        "src": element.get("src"),
                        "alt": element.get("alt"),
                        "type": element.name,
                        "description": self.find_closest_parent_with_useful_text(
                            element, **kwargs
                        ),
                    }
                )
                source_tags = element.find_all("source")
                for source_tag in source_tags:
                    media[f"{element.name}s"].append(
                        {
                            "src": source_tag.get("src"),
                            "alt": element.get("alt"),
                            "type": element.name,
                            "description": self.find_closest_parent_with_useful_text(
                                element, **kwargs
                            ),
                        }
                    )
                return True  # Always keep video and audio elements

            if element.name in ONLY_TEXT_ELIGIBLE_TAGS:
                if kwargs.get("only_text", False):
                    element.replace_with(element.get_text())

            try:
                self.remove_unwanted_attributes(
                    element, IMPORTANT_ATTRS, kwargs.get("keep_data_attributes", False)
                )
            except Exception as e:
                # print('Error removing unwanted attributes:', str(e))
                self._log(
                    "error",
                    message="Error removing unwanted attributes: {error}",
                    tag="SCRAPE",
                    params={"error": str(e)},
                )
            # Process children
            for child in list(element.children):
                if isinstance(child, NavigableString) and not isinstance(
                    child, Comment
                ):
                    if len(child.strip()) > 0:
                        keep_element = True
                else:
                    if self._process_element(
                        url,
                        child,
                        media,
                        internal_links_dict,
                        external_links_dict,
                        **kwargs,
                    ):
                        keep_element = True

            # Check word count
            word_count_threshold = kwargs.get(
                "word_count_threshold", MIN_WORD_THRESHOLD
            )
            if not keep_element:
                word_count = len(element.get_text(strip=True).split())
                keep_element = word_count >= word_count_threshold

            if not keep_element:
                element.decompose()

            return keep_element
        except Exception as e:
            # print('Error processing element:', str(e))
            self._log(
                "error",
                message="Error processing element: {error}",
                tag="SCRAPE",
                params={"error": str(e)},
            )
            return False

    def _scrap(
        self,
        url: str,
        html: str,
        word_count_threshold: int = MIN_WORD_THRESHOLD,
        css_selector: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
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

        parser_type = kwargs.get("parser", "lxml")
        soup = BeautifulSoup(html, parser_type)
        body = soup.body
        base_domain = get_base_domain(url)

        try:
            meta = extract_metadata("", soup)
        except Exception as e:
            self._log(
                "error",
                message="Error extracting metadata: {error}",
                tag="SCRAPE",
                params={"error": str(e)},
            )
            meta = {}

        # Handle tag-based removal first - faster than CSS selection
        excluded_tags = set(kwargs.get("excluded_tags", []) or [])
        if excluded_tags:
            for element in body.find_all(lambda tag: tag.name in excluded_tags):
                element.extract()

        # Handle CSS selector-based removal
        excluded_selector = kwargs.get("excluded_selector", "")
        if excluded_selector:
            is_single_selector = (
                "," not in excluded_selector and " " not in excluded_selector
            )
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
                    "markdown": "",
                    "cleaned_html": "",
                    "success": True,
                    "media": {"images": [], "videos": [], "audios": []},
                    "links": {"internal": [], "external": []},
                    "metadata": {},
                    "message": f"No elements found for CSS selector: {css_selector}",
                }
                # raise InvalidCSSSelectorError(f"Invalid CSS selector, No elements found for CSS selector: {css_selector}")
            body = soup.new_tag("div")
            for el in selected_elements:
                body.append(el)

        kwargs["exclude_social_media_domains"] = set(
            kwargs.get("exclude_social_media_domains", []) + SOCIAL_MEDIA_DOMAINS
        )
        kwargs["exclude_domains"] = set(kwargs.get("exclude_domains", []))
        if kwargs.get("exclude_social_media_links", False):
            kwargs["exclude_domains"] = kwargs["exclude_domains"].union(
                kwargs["exclude_social_media_domains"]
            )

        result_obj = self.process_element(
            url,
            body,
            word_count_threshold=word_count_threshold,
            base_domain=base_domain,
            **kwargs,
        )

        links = {"internal": [], "external": []}
        media = result_obj["media"]
        internal_links_dict = result_obj["internal_links_dict"]
        external_links_dict = result_obj["external_links_dict"]

        # Update the links dictionary with unique links
        links["internal"] = list(internal_links_dict.values())
        links["external"] = list(external_links_dict.values())

        # # Process images using ThreadPoolExecutor
        imgs = body.find_all("img")

        media["images"] = [
            img
            for result in (
                self.process_image(img, url, i, len(imgs), **kwargs)
                for i, img in enumerate(imgs)
            )
            if result is not None
            for img in result
        ]

        body = self.flatten_nested_elements(body)
        base64_pattern = re.compile(r'data:image/[^;]+;base64,([^"]+)')
        for img in imgs:
            src = img.get("src", "")
            if base64_pattern.match(src):
                # Replace base64 data with empty string
                img["src"] = base64_pattern.sub("", src)

        str_body = ""
        try:
            str_body = body.encode_contents().decode("utf-8")
        except Exception:
            # Reset body to the original HTML
            success = False
            body = BeautifulSoup(html, "html.parser")

            # Create a new div with a special ID
            error_div = body.new_tag("div", id="crawl4ai_error_message")
            error_div.string = """
            Crawl4AI Error: This page is not fully supported.
            
            Possible reasons:
            1. The page may have restrictions that prevent crawling.
            2. The page might not be fully loaded.
            
            Suggestions:
            - Try calling the crawl function with these parameters:
            magic=True,
            - Set headless=False to visualize what's happening on the page.
            
            If the issue persists, please check the page's structure and any potential anti-crawling measures.
            """

            # Append the error div to the body
            body.append(error_div)
            str_body = body.encode_contents().decode("utf-8")

            print(
                "[LOG] 😧 Error: After processing the crawled HTML and removing irrelevant tags, nothing was left in the page. Check the markdown for further details."
            )
            self._log(
                "error",
                message="After processing the crawled HTML and removing irrelevant tags, nothing was left in the page. Check the markdown for further details.",
                tag="SCRAPE",
            )

        cleaned_html = str_body.replace("\n\n", "\n").replace("  ", " ")

        return {
            # **markdown_content,
            "cleaned_html": cleaned_html,
            "success": success,
            "media": media,
            "links": links,
            "metadata": meta,
        }


class LXMLWebScrapingStrategy(WebScrapingStrategy):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.DIMENSION_REGEX = re.compile(r"(\d+)(\D*)")
        self.BASE64_PATTERN = re.compile(r'data:image/[^;]+;base64,([^"]+)')

    def _process_element(
        self,
        url: str,
        element: lhtml.HtmlElement,
        media: Dict[str, List],
        internal_links_dict: Dict[str, Any],
        external_links_dict: Dict[str, Any],
        **kwargs,
    ) -> bool:
        base_domain = kwargs.get("base_domain", get_base_domain(url))
        exclude_domains = set(kwargs.get("exclude_domains", []))

        # Process links
        for link in element.xpath(".//a[@href]"):
            href = link.get("href", "").strip()
            if not href:
                continue

            try:
                normalized_href = normalize_url(href, url)
                link_data = {
                    "href": normalized_href,
                    "text": link.text_content().strip(),
                    "title": link.get("title", "").strip(),
                    "base_domain": base_domain,
                }

                is_external = is_external_url(normalized_href, base_domain)
                if is_external:
                    link_base_domain = get_base_domain(normalized_href)
                    link_data["base_domain"] = link_base_domain
                    if (
                        kwargs.get("exclude_external_links", False)
                        or link_base_domain in exclude_domains
                    ):
                        link.getparent().remove(link)
                        continue

                    if normalized_href not in external_links_dict:
                        external_links_dict[normalized_href] = link_data
                else:
                    if normalized_href not in internal_links_dict:
                        internal_links_dict[normalized_href] = link_data

            except Exception as e:
                self._log("error", f"Error processing link: {str(e)}", "SCRAPE")
                continue

        # Process images
        images = element.xpath(".//img")
        total_images = len(images)

        for idx, img in enumerate(images):
            src = img.get("src") or ""
            img_domain = get_base_domain(src)

            # Decide if we need to exclude this image
            # 1) If its domain is in exclude_domains, remove.
            # 2) Or if exclude_external_images=True and it's an external domain, remove.
            if (img_domain in exclude_domains) or (
                kwargs.get("exclude_external_images", False)
                and is_external_url(src, base_domain)
            ):
                parent = img.getparent()
                if parent is not None:
                    parent.remove(img)
                continue

            # Otherwise, process the image as usual.
            try:
                processed_images = self.process_image(
                    img, url, idx, total_images, **kwargs
                )
                if processed_images:
                    media["images"].extend(processed_images)
            except Exception as e:
                self._log("error", f"Error processing image: {str(e)}", "SCRAPE")

        # Process videos and audios
        for media_type in ["video", "audio"]:
            for elem in element.xpath(f".//{media_type}"):
                media_info = {
                    "src": elem.get("src"),
                    "alt": elem.get("alt"),
                    "type": media_type,
                    "description": self.find_closest_parent_with_useful_text(
                        elem, **kwargs
                    ),
                }
                media[f"{media_type}s"].append(media_info)

                # Process source tags within media elements
                for source in elem.xpath(".//source"):
                    if src := source.get("src"):
                        media[f"{media_type}s"].append({**media_info, "src": src})

        # Clean up unwanted elements
        if kwargs.get("remove_forms", False):
            for form in element.xpath(".//form"):
                form.getparent().remove(form)

        if excluded_tags := kwargs.get("excluded_tags", []):
            for tag in excluded_tags:
                for elem in element.xpath(f".//{tag}"):
                    elem.getparent().remove(elem)

        if excluded_selector := kwargs.get("excluded_selector", ""):
            try:
                for elem in element.cssselect(excluded_selector):
                    elem.getparent().remove(elem)
            except Exception:
                pass  # Invalid selector

        return True

    def find_closest_parent_with_useful_text(
        self, element: lhtml.HtmlElement, **kwargs
    ) -> Optional[str]:
        image_description_min_word_threshold = kwargs.get(
            "image_description_min_word_threshold", IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
        )
        current = element
        while current is not None:
            if (
                current.text
                and len(current.text_content().split())
                >= image_description_min_word_threshold
            ):
                return current.text_content().strip()
            current = current.getparent()
        return None

    def flatten_nested_elements(self, element: lhtml.HtmlElement) -> lhtml.HtmlElement:
        """Flatten nested elements of the same type in LXML tree"""
        if len(element) == 1 and element.tag == element[0].tag:
            return self.flatten_nested_elements(element[0])

        for child in element:
            child_idx = element.index(child)
            flattened_child = self.flatten_nested_elements(child)
            if flattened_child is not child:  # Only replace if actually flattened
                element[child_idx] = flattened_child

        return element

    def process_image(
        self, img: lhtml.HtmlElement, url: str, index: int, total_images: int, **kwargs
    ) -> Optional[List[Dict]]:
        # Quick validation checks
        style = img.get("style", "")
        alt = img.get("alt", "")
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        srcset = img.get("srcset", "")
        data_srcset = img.get("data-srcset", "")

        if "display:none" in style:
            return None

        parent = img.getparent()
        if parent.tag in ["button", "input"]:
            return None

        parent_classes = parent.get("class", "").split()
        if any(
            "button" in cls or "icon" in cls or "logo" in cls for cls in parent_classes
        ):
            return None

        # If src is in class or alt, likely an icon
        if (src and any(c in src for c in ["button", "icon", "logo"])) or (
            alt and any(c in alt for c in ["button", "icon", "logo"])
        ):
            return None

        # Score calculation
        score = 0
        if (width := img.get("width")) and width.isdigit():
            score += 1 if int(width) > 150 else 0
        if (height := img.get("height")) and height.isdigit():
            score += 1 if int(height) > 150 else 0
        if alt:
            score += 1
        score += index / total_images < 0.5

        # Check formats in all possible sources
        image_formats = {"jpg", "jpeg", "png", "webp", "avif", "gif"}
        detected_format = None
        for url in [src, data_src, srcset, data_srcset]:
            if url:
                format_matches = [fmt for fmt in image_formats if fmt in url.lower()]
                if format_matches:
                    detected_format = format_matches[0]
                    score += 1
                    break

        if srcset or data_srcset:
            score += 1

        if picture := img.xpath("./ancestor::picture[1]"):
            score += 1

        if score <= kwargs.get("image_score_threshold", IMAGE_SCORE_THRESHOLD):
            return None

        # Process image variants
        unique_urls = set()
        image_variants = []
        base_info = {
            "alt": alt,
            "desc": self.find_closest_parent_with_useful_text(img, **kwargs),
            "score": score,
            "type": "image",
            "group_id": index,
            "format": detected_format,
        }

        def add_variant(src: str, width: Optional[str] = None):
            if src and not src.startswith("data:") and src not in unique_urls:
                unique_urls.add(src)
                variant = {**base_info, "src": src}
                if width:
                    variant["width"] = width
                image_variants.append(variant)

        # Add variants from different sources
        add_variant(src)
        add_variant(data_src)

        for srcset_attr in [srcset, data_srcset]:
            if srcset_attr:
                for source in parse_srcset(srcset_attr):
                    add_variant(source["url"], source["width"])

        # Handle picture element
        if picture:
            for source in picture[0].xpath(".//source[@srcset]"):
                if source_srcset := source.get("srcset"):
                    for src_data in parse_srcset(source_srcset):
                        add_variant(src_data["url"], src_data["width"])

        # Check framework-specific attributes
        for attr, value in img.attrib.items():
            if (
                attr.startswith("data-")
                and ("src" in attr or "srcset" in attr)
                and "http" in value
            ):
                add_variant(value)

        return image_variants if image_variants else None

    def remove_empty_elements_fast(self, root, word_count_threshold=5):
        """
        Remove elements that fall below the desired word threshold in a single pass from the bottom up.
        Skips non-element nodes like HtmlComment and bypasses certain tags that are allowed to have no content.
        """
        bypass_tags = {
            "a",
            "img",
            "br",
            "hr",
            "input",
            "meta",
            "link",
            "source",
            "track",
            "wbr",
        }

        for el in reversed(list(root.iterdescendants())):
            if not isinstance(el, lhtml.HtmlElement):
                continue

            if el.tag in bypass_tags:
                continue

            text_content = (el.text_content() or "").strip()
            if (
                len(text_content.split()) < word_count_threshold
                and not el.getchildren()
            ):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)

        return root

    def remove_unwanted_attributes_fast(
        self, root: lhtml.HtmlElement, important_attrs=None, keep_data_attributes=False
    ) -> lhtml.HtmlElement:
        """
        Removes all attributes from each element (including root) except those in `important_attrs`.
        If `keep_data_attributes=True`, also retain any attribute starting with 'data-'.

        Returns the same root element, mutated in-place, for fluent usage.
        """
        if important_attrs is None:
            important_attrs = set(IMPORTANT_ATTRS)

        # If you want to handle the root as well, use 'include_self=True'
        # so you don't miss attributes on the top-level element.
        # Manually include the root, then all its descendants
        for el in chain((root,), root.iterdescendants()):
            # We only remove attributes on HtmlElement nodes, skip comments or text nodes
            if not isinstance(el, lhtml.HtmlElement):
                continue

            old_attribs = dict(el.attrib)
            new_attribs = {}

            for attr_name, attr_val in old_attribs.items():
                # If it's an important attribute, keep it
                if attr_name in important_attrs:
                    new_attribs[attr_name] = attr_val
                # Or if keep_data_attributes is True and it's a 'data-*' attribute
                elif keep_data_attributes and attr_name.startswith("data-"):
                    new_attribs[attr_name] = attr_val

            # Clear old attributes and set the filtered set
            el.attrib.clear()
            el.attrib.update(new_attribs)

        return root

    def _scrap(
        self,
        url: str,
        html: str,
        word_count_threshold: int = MIN_WORD_THRESHOLD,
        css_selector: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if not html:
            return None

        success = True
        try:
            doc = lhtml.document_fromstring(html)
            # Match BeautifulSoup's behavior of using body or full doc
            # body = doc.xpath('//body')[0] if doc.xpath('//body') else doc
            body = doc

            base_domain = get_base_domain(url)

            # Add comment removal
            if kwargs.get("remove_comments", False):
                comments = body.xpath("//comment()")
                for comment in comments:
                    comment.getparent().remove(comment)

            # Handle tag-based removal first
            excluded_tags = set(kwargs.get("excluded_tags", []) or [])
            if excluded_tags:
                for tag in excluded_tags:
                    for element in body.xpath(f".//{tag}"):
                        if element.getparent() is not None:
                            element.getparent().remove(element)

            # Handle CSS selector-based exclusion
            excluded_selector = kwargs.get("excluded_selector", "")
            if excluded_selector:
                try:
                    for element in body.cssselect(excluded_selector):
                        if element.getparent() is not None:
                            element.getparent().remove(element)
                except Exception as e:
                    self._log(
                        "error", f"Error with excluded CSS selector: {str(e)}", "SCRAPE"
                    )

            # Extract metadata before any content filtering
            try:
                meta = extract_metadata_using_lxml(
                    "", doc
                )  # Using same function as BeautifulSoup version
            except Exception as e:
                self._log("error", f"Error extracting metadata: {str(e)}", "SCRAPE")
                meta = {}

            # Handle CSS selector targeting
            if css_selector:
                try:
                    selected_elements = body.cssselect(css_selector)
                    if not selected_elements:
                        return {
                            "markdown": "",
                            "cleaned_html": "",
                            "success": True,
                            "media": {"images": [], "videos": [], "audios": []},
                            "links": {"internal": [], "external": []},
                            "metadata": meta,
                            "message": f"No elements found for CSS selector: {css_selector}",
                        }
                    body = lhtml.Element("div")
                    body.extend(selected_elements)
                except Exception as e:
                    self._log("error", f"Error with CSS selector: {str(e)}", "SCRAPE")
                    return None

            # Remove script and style tags
            for tag in ["script", "style", "link", "meta", "noscript"]:
                for element in body.xpath(f".//{tag}"):
                    if element.getparent() is not None:
                        element.getparent().remove(element)

            # Handle social media and domain exclusions
            kwargs["exclude_domains"] = set(kwargs.get("exclude_domains", []))
            if kwargs.get("exclude_social_media_links", False):
                kwargs["exclude_social_media_domains"] = set(
                    kwargs.get("exclude_social_media_domains", [])
                    + SOCIAL_MEDIA_DOMAINS
                )
                kwargs["exclude_domains"].update(kwargs["exclude_social_media_domains"])

            # Process forms if needed
            if kwargs.get("remove_forms", False):
                for form in body.xpath(".//form"):
                    if form.getparent() is not None:
                        form.getparent().remove(form)

            # Process content
            media = {"images": [], "videos": [], "audios": []}
            internal_links_dict = {}
            external_links_dict = {}

            self._process_element(
                url,
                body,
                media,
                internal_links_dict,
                external_links_dict,
                base_domain=base_domain,
                **kwargs,
            )

            # Handle only_text option
            if kwargs.get("only_text", False):
                for tag in ONLY_TEXT_ELIGIBLE_TAGS:
                    for element in body.xpath(f".//{tag}"):
                        if element.text:
                            new_text = lhtml.Element("span")
                            new_text.text = element.text_content()
                            if element.getparent() is not None:
                                element.getparent().replace(element, new_text)

            # Clean base64 images
            for img in body.xpath(".//img[@src]"):
                src = img.get("src", "")
                if self.BASE64_PATTERN.match(src):
                    img.set("src", self.BASE64_PATTERN.sub("", src))

            # Remove empty elements
            self.remove_empty_elements_fast(body, 1)

            # Remvoe unneeded attributes
            self.remove_unwanted_attributes_fast(
                body, keep_data_attributes=kwargs.get("keep_data_attributes", False)
            )

            # Generate output HTML
            cleaned_html = lhtml.tostring(
                body,
                encoding="unicode",
                pretty_print=True,
                method="html",
                with_tail=False,
            ).strip()
            return {
                "cleaned_html": cleaned_html,
                "success": success,
                "media": media,
                "links": {
                    "internal": list(internal_links_dict.values()),
                    "external": list(external_links_dict.values()),
                },
                "metadata": meta,
            }

        except Exception as e:
            self._log("error", f"Error processing HTML: {str(e)}", "SCRAPE")
            # Create error message in case of failure
            error_body = lhtml.Element("div")
            # Use etree.SubElement rather than lhtml.SubElement
            error_div = etree.SubElement(error_body, "div", id="crawl4ai_error_message")
            error_div.text = f"""
            Crawl4AI Error: This page is not fully supported.
            
            Error Message: {str(e)}
            
            Possible reasons:
            1. The page may have restrictions that prevent crawling.
            2. The page might not be fully loaded.
            
            Suggestions:
            - Try calling the crawl function with these parameters:
            magic=True,
            - Set headless=False to visualize what's happening on the page.
            
            If the issue persists, please check the page's structure and any potential anti-crawling measures.
            """
            cleaned_html = lhtml.tostring(
                error_body, encoding="unicode", pretty_print=True
            )
            return {
                "cleaned_html": cleaned_html,
                "success": False,
                "media": {"images": [], "videos": [], "audios": []},
                "links": {"internal": [], "external": []},
                "metadata": {},
            }
