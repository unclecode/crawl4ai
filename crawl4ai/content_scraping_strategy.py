import re
from itertools import chain
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
# from bs4 import BeautifulSoup
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
# from bs4 import NavigableString, Comment
# from bs4 import PageElement, Tag
from urllib.parse import urljoin
from requests.exceptions import InvalidSchema
from .utils import (
    # extract_metadata,
    normalize_url,
    is_external_url,
    get_base_domain,
    extract_metadata_using_lxml,
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
    def __init__(self, logger=None):
        self.logger = logger
        self.DIMENSION_REGEX = re.compile(r"(\d+)(\D*)")
        self.BASE64_PATTERN = re.compile(r'data:image/[^;]+;base64,([^"]+)')
        
        # Constants for image processing
        self.classes_to_check = frozenset(["button", "icon", "logo"])
        self.tags_to_check = frozenset(["button", "input"])
        self.image_formats = frozenset(["jpg", "jpeg", "png", "webp", "avif", "gif"])

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

    def process_element(self, url: str, element: lhtml.HtmlElement, **kwargs) -> Dict[str, Any]:
        """
        Process an HTML element.

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

    def remove_unwanted_attributes(self, element: lhtml.HtmlElement, important_attrs: List[str], keep_data_attributes: bool = False):
        """
        Remove unwanted attributes from an HTML element.

        Args:
            element (lhtml.HtmlElement): The HTML element to remove attributes from.
            important_attrs (List[str]): List of important attributes to keep.
            keep_data_attributes (bool): Whether to keep data attributes.

        Returns:
            None
        """
        attrs_to_remove = []
        for attr in element.attrib:
            if attr not in important_attrs:
                if keep_data_attributes:
                    if not attr.startswith("data-"):
                        attrs_to_remove.append(attr)
                else:
                    attrs_to_remove.append(attr)

        for attr in attrs_to_remove:
            del element.attrib[attr]

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
        if parent.tag in self.tags_to_check:
            return None

        parent_classes = parent.get("class", "").split()
        if any(
            "button" in cls or "icon" in cls or "logo" in cls for cls in parent_classes
        ):
            return None

        # If src is in class or alt, likely an icon
        if (src and any(c in src for c in self.classes_to_check)) or (
            alt and any(c in alt for c in self.classes_to_check)
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
        detected_format = None
        for url in [src, data_src, srcset, data_srcset]:
            if url:
                format_matches = [fmt for fmt in self.image_formats if fmt in url.lower()]
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

    def is_data_table(self, table: etree.Element, **kwargs) -> bool:
        score = 0
        # Check for thead and tbody
        has_thead = len(table.xpath(".//thead")) > 0
        has_tbody = len(table.xpath(".//tbody")) > 0
        if has_thead:
            score += 2
        if has_tbody:
            score += 1

        # Check for th elements
        th_count = len(table.xpath(".//th"))
        if th_count > 0:
            score += 2
            if has_thead or table.xpath(".//tr[1]/th"):
                score += 1

        # Check for nested tables
        if len(table.xpath(".//table")) > 0:
            score -= 3

        # Role attribute check
        role = table.get("role", "").lower()
        if role in {"presentation", "none"}:
            score -= 3

        # Column consistency
        rows = table.xpath(".//tr")
        if not rows:
            return False
        col_counts = [len(row.xpath(".//td|.//th")) for row in rows]
        avg_cols = sum(col_counts) / len(col_counts)
        variance = sum((c - avg_cols)**2 for c in col_counts) / len(col_counts)
        if variance < 1:
            score += 2

        # Caption and summary
        if table.xpath(".//caption"):
            score += 2
        if table.get("summary"):
            score += 1

        # Text density
        total_text = sum(len(''.join(cell.itertext()).strip()) for row in rows for cell in row.xpath(".//td|.//th"))
        total_tags = sum(1 for _ in table.iterdescendants())
        text_ratio = total_text / (total_tags + 1e-5)
        if text_ratio > 20:
            score += 3
        elif text_ratio > 10:
            score += 2

        # Data attributes
        data_attrs = sum(1 for attr in table.attrib if attr.startswith('data-'))
        score += data_attrs * 0.5

        # Size check
        if avg_cols >= 2 and len(rows) >= 2:
            score += 2

        threshold = kwargs.get("table_score_threshold", 7)
        return score >= threshold

    def extract_table_data(self, table: etree.Element) -> dict:
        caption = table.xpath(".//caption/text()")
        caption = caption[0].strip() if caption else ""
        summary = table.get("summary", "").strip()

        # Extract headers with colspan handling
        headers = []
        thead_rows = table.xpath(".//thead/tr")
        if thead_rows:
            header_cells = thead_rows[0].xpath(".//th")
            for cell in header_cells:
                text = cell.text_content().strip()
                colspan = int(cell.get("colspan", 1))
                headers.extend([text] * colspan)
        else:
            first_row = table.xpath(".//tr[1]")
            if first_row:
                for cell in first_row[0].xpath(".//th|.//td"):
                    text = cell.text_content().strip()
                    colspan = int(cell.get("colspan", 1))
                    headers.extend([text] * colspan)

        # Extract rows with colspan handling
        rows = []
        for row in table.xpath(".//tr[not(ancestor::thead)]"):
            row_data = []
            for cell in row.xpath(".//td"):
                text = cell.text_content().strip()
                colspan = int(cell.get("colspan", 1))
                row_data.extend([text] * colspan)
            if row_data:
                rows.append(row_data)

        # Align rows with headers
        max_columns = len(headers) if headers else (max(len(row) for row in rows) if rows else 0)
        aligned_rows = []
        for row in rows:
            aligned = row[:max_columns] + [''] * (max_columns - len(row))
            aligned_rows.append(aligned)

        if not headers:
            headers = [f"Column {i+1}" for i in range(max_columns)]

        return {
            "headers": headers,
            "rows": aligned_rows,
            "caption": caption,
            "summary": summary,
        }

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
            # Extract metadata FIRST from the original HTML to avoid issues with modified content.
            try:
                meta = extract_metadata_using_lxml(html, None)  # Pass the original HTML
            except Exception as e:
                self._log("error", f"Error extracting metadata: {str(e)}", "SCRAPE")
                meta = {}
                
            doc = lhtml.document_fromstring(html)
            # Match BeautifulSoup's behavior of using body or full doc
            # body = doc.xpath('//body')[0] if doc.xpath('//body') else doc
            body = doc

            base_domain = get_base_domain(url)
            
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

            # # Extract metadata before any content filtering
            # try:
            #     meta = extract_metadata_using_lxml(
            #         "", doc
            #     )  # Using same function as BeautifulSoup version
            # except Exception as e:
            #     self._log("error", f"Error extracting metadata: {str(e)}", "SCRAPE")
            #     meta = {}

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
                base_domain=base_domain,
                **kwargs,
            )

            if 'table' not in excluded_tags:
                tables = body.xpath(".//table")
                for table in tables:
                    if self.is_data_table(table, **kwargs):
                        table_data = self.extract_table_data(table)
                        media["tables"].append(table_data)

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
                body, 
                important_attrs=IMPORTANT_ATTRS + kwargs.get("keep_attrs", []),
                keep_data_attributes=kwargs.get("keep_data_attributes", False)
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
                "media": {
                    "images": [],
                    "videos": [],
                    "audios": [],
                    "tables": []
                },
                "links": {"internal": [], "external": []},
                "metadata": {},
            }
