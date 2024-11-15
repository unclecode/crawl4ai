from bs4 import BeautifulSoup, Tag
import re
from typing import Optional

class ContentCleaningStrategy:
    def __init__(self):
        # Precompile regex patterns for performance
        self.negative_patterns = re.compile(r'nav|footer|header|sidebar|ads|comment', re.I)
        self.positive_patterns = re.compile(r'content|article|main|post', re.I)
        self.priority_tags = {'article', 'main', 'section', 'div'}
        self.non_content_tags = {'nav', 'footer', 'header', 'aside'}
        # Thresholds
        self.text_density_threshold = 9.0
        self.min_word_count = 50
        self.link_density_threshold = 0.2
        self.max_dom_depth = 10  # To prevent excessive DOM traversal

    def clean(self, clean_html: str) -> str:
        """
        Main function that takes cleaned HTML and returns super cleaned HTML.

        Args:
            clean_html (str): The cleaned HTML content.

        Returns:
            str: The super cleaned HTML containing only the main content.
        """
        try:
            if not clean_html or not isinstance(clean_html, str):
                return ''
            soup = BeautifulSoup(clean_html, 'html.parser')
            main_content = self.extract_main_content(soup)
            if main_content:
                super_clean_element = self.clean_element(main_content)
                return str(super_clean_element)
            else:
                return ''
        except Exception:
            # Handle exceptions silently or log them as needed
            return ''

    def extract_main_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        """
        Identifies and extracts the main content element from the HTML.

        Args:
            soup (BeautifulSoup): The parsed HTML soup.

        Returns:
            Optional[Tag]: The Tag object containing the main content, or None if not found.
        """
        candidates = []
        for element in soup.find_all(self.priority_tags):
            if self.is_non_content_tag(element):
                continue
            if self.has_negative_class_id(element):
                continue
            score = self.calculate_content_score(element)
            candidates.append((score, element))
        
        if not candidates:
            return None

        # Sort candidates by score in descending order
        candidates.sort(key=lambda x: x[0], reverse=True)
        # Select the element with the highest score
        best_element = candidates[0][1]
        return best_element

    def calculate_content_score(self, element: Tag) -> float:
        """
        Calculates a score for an element based on various heuristics.

        Args:
            element (Tag): The HTML element to score.

        Returns:
            float: The content score of the element.
        """
        score = 0.0

        if self.is_priority_tag(element):
            score += 5.0
        if self.has_positive_class_id(element):
            score += 3.0
        if self.has_negative_class_id(element):
            score -= 3.0
        if self.is_high_text_density(element):
            score += 2.0
        if self.is_low_link_density(element):
            score += 2.0
        if self.has_sufficient_content(element):
            score += 2.0
        if self.has_headings(element):
            score += 3.0

        dom_depth = self.calculate_dom_depth(element)
        score += min(dom_depth, self.max_dom_depth) * 0.5  # Adjust weight as needed

        return score

    def is_priority_tag(self, element: Tag) -> bool:
        """Checks if the element is a priority tag."""
        return element.name in self.priority_tags

    def is_non_content_tag(self, element: Tag) -> bool:
        """Checks if the element is a non-content tag."""
        return element.name in self.non_content_tags

    def has_negative_class_id(self, element: Tag) -> bool:
        """Checks if the element has negative indicators in its class or id."""
        class_id = ' '.join(filter(None, [
            self.get_attr_str(element.get('class')),
            element.get('id', '')
        ]))
        return bool(self.negative_patterns.search(class_id))

    def has_positive_class_id(self, element: Tag) -> bool:
        """Checks if the element has positive indicators in its class or id."""
        class_id = ' '.join(filter(None, [
            self.get_attr_str(element.get('class')),
            element.get('id', '')
        ]))
        return bool(self.positive_patterns.search(class_id))

    @staticmethod
    def get_attr_str(attr) -> str:
        """Converts an attribute value to a string."""
        if isinstance(attr, list):
            return ' '.join(attr)
        elif isinstance(attr, str):
            return attr
        else:
            return ''

    def is_high_text_density(self, element: Tag) -> bool:
        """Determines if the element has high text density."""
        text_density = self.calculate_text_density(element)
        return text_density > self.text_density_threshold

    def calculate_text_density(self, element: Tag) -> float:
        """Calculates the text density of an element."""
        text_length = len(element.get_text(strip=True))
        tag_count = len(element.find_all())
        tag_count = tag_count or 1  # Prevent division by zero
        return text_length / tag_count

    def is_low_link_density(self, element: Tag) -> bool:
        """Determines if the element has low link density."""
        link_density = self.calculate_link_density(element)
        return link_density < self.link_density_threshold

    def calculate_link_density(self, element: Tag) -> float:
        """Calculates the link density of an element."""
        text = element.get_text(strip=True)
        if not text:
            return 0.0
        link_text = ' '.join(a.get_text(strip=True) for a in element.find_all('a'))
        return len(link_text) / len(text) if text else 0.0

    def has_sufficient_content(self, element: Tag) -> bool:
        """Checks if the element has sufficient word count."""
        word_count = len(element.get_text(strip=True).split())
        return word_count >= self.min_word_count

    def calculate_dom_depth(self, element: Tag) -> int:
        """Calculates the depth of an element in the DOM tree."""
        depth = 0
        current_element = element
        while current_element.parent and depth < self.max_dom_depth:
            depth += 1
            current_element = current_element.parent
        return depth

    def has_headings(self, element: Tag) -> bool:
        """Checks if the element contains heading tags."""
        return bool(element.find(['h1', 'h2', 'h3']))

    def clean_element(self, element: Tag) -> Tag:
        """
        Cleans the selected element by removing unnecessary attributes and nested non-content elements.

        Args:
            element (Tag): The HTML element to clean.

        Returns:
            Tag: The cleaned HTML element.
        """
        for tag in element.find_all(['script', 'style', 'aside']):
            tag.decompose()
        for tag in element.find_all():
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr in ['style', 'onclick', 'onmouseover', 'align', 'bgcolor']:
                    del tag.attrs[attr]
        return element
