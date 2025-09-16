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
    extract_page_context,
    calculate_link_intrinsic_score,
)
from lxml import etree
from lxml import html as lhtml
from typing import List
from .models import ScrapingResult, MediaItem, Link, Media, Links
import copy

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
                parts[1].rstrip("w").split('.')[0]
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


class LXMLWebScrapingStrategy(ContentScrapingStrategy):
    """
    LXML-based implementation for fast web content scraping.
    
    This is the primary scraping strategy in Crawl4AI, providing high-performance
    HTML parsing and content extraction using the lxml library.
    
    Note: WebScrapingStrategy is now an alias for this class to maintain
    backward compatibility.
    """
    def __init__(self, logger=None):
        self.logger = logger
        self.DIMENSION_REGEX = re.compile(r"(\d+)(\D*)")
        self.BASE64_PATTERN = re.compile(r'data:image/[^;]+;base64,([^"]+)')

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
        actual_url = kwargs.get("redirected_url", url)
        raw_result = self._scrap(actual_url, html, **kwargs)
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
            tables=raw_result.get("media", {}).get("tables", [])
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
        return await asyncio.to_thread(self.scrap, url, html, **kwargs)

    def process_element(self, url, element: lhtml.HtmlElement, **kwargs) -> Dict[str, Any]:
        """
        Process an HTML element.

        How it works:
        1. Check if the element is an image, video, or audio.
        2. Extract the element's attributes and content.
        3. Process the element based on its type.
        4. Return the processed element information.

        Args:
            url (str): The URL of the page containing the element.
            element (lhtml.HtmlElement): The HTML element to process.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing the processed element information.
        """
        media = {"images": [], "videos": [], "audios": [], "tables": []}
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
        url: str,
        element: lhtml.HtmlElement,
        media: Dict[str, List],
        internal_links_dict: Dict[str, Any],
        external_links_dict: Dict[str, Any],
        page_context: dict = None,
        **kwargs,
    ) -> bool:
        base_domain = kwargs.get("base_domain", get_base_domain(url))
        exclude_domains = set(kwargs.get("exclude_domains", []))

        # Process links
        try:
            base_element = element.xpath("//head/base[@href]")
            if base_element:
                base_href = base_element[0].get("href", "").strip()
                if base_href:
                    url = base_href
        except Exception as e:
            self._log("error", f"Error extracting base URL: {str(e)}", "SCRAPE")
            pass

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
                
                # Add intrinsic scoring if enabled
                if kwargs.get("score_links", False) and page_context is not None:
                    try:
                        intrinsic_score = calculate_link_intrinsic_score(
                            link_text=link_data["text"],
                            url=normalized_href,
                            title_attr=link_data["title"],
                            class_attr=link.get("class", ""),
                            rel_attr=link.get("rel", ""),
                            page_context=page_context
                        )
                        link_data["intrinsic_score"] = intrinsic_score
                    except Exception:
                        # Fail gracefully - assign default score
                        link_data["intrinsic_score"] = 0
                else:
                    # No scoring enabled - assign infinity (all links equal priority)
                    link_data["intrinsic_score"] = 0

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
            "tr",
            "td",
            "th",
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
        target_elements: List[str] = None,
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
            
            # Extract page context for link scoring (if enabled) - do this BEFORE any removals
            page_context = None
            if kwargs.get("score_links", False):
                try:
                    # Extract title
                    title_elements = doc.xpath('//title')
                    page_title = title_elements[0].text_content() if title_elements else ""
                    
                    # Extract headlines
                    headlines = []
                    for tag in ['h1', 'h2', 'h3']:
                        elements = doc.xpath(f'//{tag}')
                        for el in elements:
                            text = el.text_content().strip()
                            if text:
                                headlines.append(text)
                    headlines_text = ' '.join(headlines)
                    
                    # Extract meta description
                    meta_desc_elements = doc.xpath('//meta[@name="description"]/@content')
                    meta_description = meta_desc_elements[0] if meta_desc_elements else ""
                    
                    # Create page context
                    page_context = extract_page_context(page_title, headlines_text, meta_description, url)
                except Exception:
                    page_context = {}  # Fail gracefully
            
            # Early removal of all images if exclude_all_images is set
            # This is more efficient in lxml as we remove elements before any processing
            if kwargs.get("exclude_all_images", False):
                for img in body.xpath('//img'):
                    if img.getparent() is not None:
                        img.getparent().remove(img)

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

            content_element = None
            if target_elements:
                try:
                    for_content_targeted_element = []
                    for target_element in target_elements:
                        for_content_targeted_element.extend(body.cssselect(target_element))
                    content_element = lhtml.Element("div")
                    content_element.extend(copy.deepcopy(for_content_targeted_element))
                except Exception as e:
                    self._log("error", f"Error with target element detection: {str(e)}", "SCRAPE")
                    return None
            else:
                content_element = body

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
            media = {"images": [], "videos": [], "audios": [], "tables": []}
            internal_links_dict = {}
            external_links_dict = {}

            self._process_element(
                url,
                body,
                media,
                internal_links_dict,
                external_links_dict,
                page_context=page_context,
                base_domain=base_domain,
                **kwargs,
            )

            # Extract tables using the table extraction strategy if provided
            if 'table' not in excluded_tags:
                table_extraction = kwargs.get('table_extraction')
                if table_extraction:
                    # Pass logger to the strategy if it doesn't have one
                    if not table_extraction.logger:
                        table_extraction.logger = self.logger
                    # Extract tables using the strategy
                    extracted_tables = table_extraction.extract_tables(body, **kwargs)
                    media["tables"].extend(extracted_tables)

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

            # Remove unneeded attributes
            self.remove_unwanted_attributes_fast(
                body, keep_data_attributes=kwargs.get("keep_data_attributes", False)
            )

            # Generate output HTML
            cleaned_html = lhtml.tostring(
                # body,   
                content_element,
                encoding="unicode",
                pretty_print=True,
                method="html",
                with_tail=False,
            ).strip()
            
            # Create links dictionary in the format expected by LinkPreview
            links = {
                "internal": list(internal_links_dict.values()),
                "external": list(external_links_dict.values()),
            }
            
            # Extract head content for links if configured
            link_preview_config = kwargs.get("link_preview_config")
            if link_preview_config is not None:
                try:
                    import asyncio
                    from .link_preview import LinkPreview
                    from .models import Links, Link
                    
                    verbose = link_preview_config.verbose
                    
                    if verbose:
                        self._log("info", "Starting link head extraction for {internal} internal and {external} external links",
                                  params={"internal": len(links["internal"]), "external": len(links["external"])}, tag="LINK_EXTRACT")
                    
                    # Convert dict links to Link objects
                    internal_links = [Link(**link_data) for link_data in links["internal"]]
                    external_links = [Link(**link_data) for link_data in links["external"]]
                    links_obj = Links(internal=internal_links, external=external_links)
                    
                    # Create a config object for LinkPreview
                    class TempCrawlerRunConfig:
                        def __init__(self, link_config, score_links):
                            self.link_preview_config = link_config
                            self.score_links = score_links
                    
                    config = TempCrawlerRunConfig(link_preview_config, kwargs.get("score_links", False))
                    
                    # Extract head content (run async operation in sync context)
                    async def extract_links():
                        async with LinkPreview(self.logger) as extractor:
                            return await extractor.extract_link_heads(links_obj, config)
                    
                    # Run the async operation
                    try:
                        # Check if we're already in an async context
                        loop = asyncio.get_running_loop()
                        # If we're in an async context, we need to run in a thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, extract_links())
                            updated_links = future.result()
                    except RuntimeError:
                        # No running loop, we can use asyncio.run directly
                        updated_links = asyncio.run(extract_links())
                    
                    # Convert back to dict format
                    links["internal"] = [link.dict() for link in updated_links.internal]
                    links["external"] = [link.dict() for link in updated_links.external]
                    
                    if verbose:
                        successful_internal = len([l for l in updated_links.internal if l.head_extraction_status == "valid"])
                        successful_external = len([l for l in updated_links.external if l.head_extraction_status == "valid"])
                        self._log("info", "Link head extraction completed: {internal_success}/{internal_total} internal, {external_success}/{external_total} external",
                                  params={
                                      "internal_success": successful_internal,
                                      "internal_total": len(updated_links.internal),
                                      "external_success": successful_external,
                                      "external_total": len(updated_links.external)
                                  }, tag="LINK_EXTRACT")
                    else:
                        self._log("info", "Link head extraction completed successfully", tag="LINK_EXTRACT")
                        
                except Exception as e:
                    self._log("error", f"Error during link head extraction: {str(e)}", tag="LINK_EXTRACT")
                    # Continue with original links if head extraction fails
            
            return {
                "cleaned_html": cleaned_html,
                "success": success,
                "media": media,
                "links": links,
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
                "media": {
                    "images": [],
                    "videos": [],
                    "audios": [],
                    "tables": []
                },
                "links": {"internal": [], "external": []},
                "metadata": {},
            }


# Backward compatibility alias
WebScrapingStrategy = LXMLWebScrapingStrategy
