import json
import time
from bs4 import BeautifulSoup
from crawl4ai.content_scraping_strategy import (
    WebScrapingStrategy,
    LXMLWebScrapingStrategy,
)
from typing import Dict, List, Tuple
import difflib
from lxml import html as lhtml, etree


def normalize_dom(element):
    """
    Recursively normalizes an lxml HTML element:
      - Removes comment nodes
      - Sorts attributes on each node
      - Removes <head> if you want (optional)
    Returns the same element (mutated).
    """
    # Remove comment nodes
    comments = element.xpath("//comment()")
    for c in comments:
        p = c.getparent()
        if p is not None:
            p.remove(c)

    # If you'd like to remove <head>, or unify <html>/<body>, you could do so here.
    # For example, remove <head> entirely:
    # heads = element.xpath('//head')
    # for h in heads:
    #     parent = h.getparent()
    #     if parent is not None:
    #         parent.remove(h)

    # Sort attributes (to avoid false positives due to attr order)
    for el in element.iter():
        if el.attrib:
            # Convert to a sorted list of (k, v), then reassign
            sorted_attribs = sorted(el.attrib.items())
            el.attrib.clear()
            for k, v in sorted_attribs:
                el.set(k, v)

    return element


def strip_html_body(root):
    """
    If 'root' is <html>, find its <body> child and move all of <body>'s children
    into a new <div>. Return that <div>.

    If 'root' is <body>, similarly move all of its children into a new <div> and return it.

    Otherwise, return 'root' as-is.
    """
    tag_name = (root.tag or "").lower()

    # Case 1: The root is <html>
    if tag_name == "html":
        bodies = root.xpath("./body")
        if bodies:
            body = bodies[0]
            new_div = lhtml.Element("div")
            for child in body:
                new_div.append(child)
            return new_div
        else:
            # No <body> found; just return the <html> root
            return root

    # Case 2: The root is <body>
    elif tag_name == "body":
        new_div = lhtml.Element("div")
        for child in root:
            new_div.append(child)
        return new_div

    # Case 3: Neither <html> nor <body>
    else:
        return root


def compare_nodes(node1, node2, differences, path="/"):
    """
    Recursively compare two lxml nodes, appending textual differences to `differences`.
    `path` is used to indicate the location in the tree (like an XPath).
    """
    # 1) Compare tag names
    if node1.tag != node2.tag:
        differences.append(f"Tag mismatch at {path}: '{node1.tag}' vs. '{node2.tag}'")
        return

    # 2) Compare attributes
    # By now, they are sorted in normalize_dom()
    attrs1 = list(node1.attrib.items())
    attrs2 = list(node2.attrib.items())
    if attrs1 != attrs2:
        differences.append(
            f"Attribute mismatch at {path}/{node1.tag}: {attrs1} vs. {attrs2}"
        )

    # 3) Compare text (trim or unify whitespace as needed)
    text1 = (node1.text or "").strip()
    text2 = (node2.text or "").strip()
    # Normalize whitespace
    text1 = " ".join(text1.split())
    text2 = " ".join(text2.split())
    if text1 != text2:
        # If you prefer ignoring newlines or multiple whitespace, do a more robust cleanup
        differences.append(
            f"Text mismatch at {path}/{node1.tag}: '{text1}' vs. '{text2}'"
        )

    # 4) Compare number of children
    children1 = list(node1)
    children2 = list(node2)
    if len(children1) != len(children2):
        differences.append(
            f"Child count mismatch at {path}/{node1.tag}: {len(children1)} vs. {len(children2)}"
        )
        return  # If counts differ, no point comparing child by child

    # 5) Recursively compare each child
    for i, (c1, c2) in enumerate(zip(children1, children2)):
        # Build a path for child
        child_path = f"{path}/{node1.tag}[{i}]"
        compare_nodes(c1, c2, differences, child_path)

    # 6) Compare tail text
    tail1 = (node1.tail or "").strip()
    tail2 = (node2.tail or "").strip()
    if tail1 != tail2:
        differences.append(
            f"Tail mismatch after {path}/{node1.tag}: '{tail1}' vs. '{tail2}'"
        )


def compare_html_structurally(html1, html2):
    """
    Compare two HTML strings using a structural approach with lxml.
    Returns a list of differences (if any). If empty, they're effectively the same.
    """
    # 1) Parse both
    try:
        tree1 = lhtml.fromstring(html1)
    except etree.ParserError:
        return ["Error parsing HTML1"]

    try:
        tree2 = lhtml.fromstring(html2)
    except etree.ParserError:
        return ["Error parsing HTML2"]

    # 2) Normalize both DOMs (remove comments, sort attributes, etc.)
    tree1 = normalize_dom(tree1)
    tree2 = normalize_dom(tree2)

    # 3) Possibly strip <html>/<body> wrappers for better apples-to-apples comparison
    tree1 = strip_html_body(tree1)
    tree2 = strip_html_body(tree2)

    # 4) Compare recursively
    differences = []
    compare_nodes(tree1, tree2, differences, path="")
    return differences


def generate_large_html(n_elements=1000):
    html = ["<!DOCTYPE html><html><head></head><body>"]
    for i in range(n_elements):
        html.append(
            f"""
            <div class="article">
                <h2>Heading {i}</h2>
                <p>This is paragraph {i} with some content and a <a href="http://example.com/{i}">link</a></p>
                <img src="image{i}.jpg" alt="Image {i}">
                <ul>
                    <li>List item {i}.1</li>
                    <li>List item {i}.2</li>
                </ul>
            </div>
        """
        )
    html.append("</body></html>")
    return "".join(html)


def generate_complicated_html():
    """
    HTML with multiple domains, forms, data attributes,
    various images, comments, style, and noscript to test all parameter toggles.
    """
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Complicated Test Page</title>
        <meta name="description" content="A very complicated page for testing.">
        
        <style>
          .hidden { display: none; }
          .highlight { color: red; }
        </style>
      </head>
      <body>
        <!-- This is a comment that we may remove if remove_comments=True -->
        
        <header>
          <h1>Main Title of the Page</h1>
          <nav>
            <a href="http://example.com/home">Home</a>
            <a href="http://social.com/profile">Social Profile</a>
            <a href="javascript:void(0)">JS Void Link</a>
          </nav>
        </header>
        
        <noscript>
          <p>JavaScript is disabled or not supported.</p>
        </noscript>
        
        <form action="submit.php" method="post">
          <input type="text" name="username" />
          <button type="submit">Submit</button>
        </form>
        
        <section>
          <article>
            <h2>Article Title</h2>
            <p>
              This paragraph has a good amount of text to exceed word_count_threshold if it's 
              set to something small. But it might not exceed a very high threshold.
            </p>
            
            <img src="http://images.example.com/photo.jpg" alt="Descriptive alt text"
                 style="width:200px;height:150px;" data-lazy="true">
            
            <img src="icon.png" alt="Icon" style="display:none;">
            
            <p>Another short text. <a href="/local-link">Local Link</a></p>
          </article>
        </section>
        
        <section id="promo-section">
          <p>Promo text <a href="http://ads.example.com/ad">Ad Link</a></p>
        </section>
        
        <aside class="sidebar">
          <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA..." alt="Base64 Image">
          <div data-info="secret" class="social-widget">
            <p>Follow us on <a href="http://facebook.com/brand">Facebook</a></p>
          </div>
        </aside>
        
        <!-- Another comment below this line -->
        <script>console.log("script that might be removed");</script>
        
        <div style="display:none;">
          <p>This is hidden</p>
        </div>
        
        <footer>
          <small>Footer Info &copy; 2025</small>
        </footer>
      </body>
    </html>
    """


def get_test_scenarios():
    """
    Returns a dictionary of parameter sets (test scenarios) for the scraper.
    Each scenario name maps to a dictionary of keyword arguments
    that will be passed into scrap() for testing various features.
    """
    TEST_SCENARIOS = {
        # "default": {},
        # "exclude_domains": {
        #     "exclude_domains": {"images.example.com", "ads.example.com"}
        # },
        # "exclude_social_media_links": {
        #     "exclude_social_media_links": True
        # },
        # "high_word_threshold": {
        #     "word_count_threshold": 100
        # },
        # "keep_data_attrs": {
        #     "keep_data_attributes": True
        # },
        # "remove_forms_and_comments": {
        #     "remove_forms": True,
        #     "remove_comments": True
        # },
        # "exclude_tags_and_selector": {
        #     "excluded_tags": ["aside", "script"],
        #     "excluded_selector": ".social-widget"
        # },
        # "only_text_mode": {
        #     "only_text": True
        # },
        # "combo_mode": {
        #     "exclude_domains": {"images.example.com", "ads.example.com"},
        #     "exclude_social_media_links": True,
        #     "remove_forms": True,
        #     "remove_comments": True,
        #     "excluded_tags": ["aside"],
        #     "excluded_selector": "#promo-section",
        #     "only_text": False,
        #     "keep_data_attributes": True,
        #     "word_count_threshold": 20
        # },
        # "exclude_external_images": {
        #     "exclude_external_images": True,
        #     "exclude_social_media_links": True
        # },
        # "strict_image_scoring": {
        #     "image_score_threshold": 3,
        #     "image_description_min_word_threshold": 10
        # },
        # "custom_css_selector": {
        #     "css_selector": "section#promo-section"
        # },
        # "remove_noscript": {
        #     "excluded_tags": ["noscript"]
        # },
        # "exclude_external_links": {
        #     "exclude_external_links": True
        # },
        # "large_word_count": {
        #     "word_count_threshold": 500
        # },
        # "super_strict_images": {
        #     "image_score_threshold": 5,
        #     "image_description_min_word_threshold": 15
        # },
        # "exclude_style_and_script": {
        #     "excluded_tags": ["style", "script"]
        # },
        # "keep_data_and_remove_forms": {
        #     "keep_data_attributes": True,
        #     "remove_forms": True
        # },
        # "only_text_high_word_count": {
        #     "only_text": True,
        #     "word_count_threshold": 40
        # },
        # "reduce_to_selector": {
        #     "css_selector": "section > article"
        # },
        # "exclude_all_links": {
        #     # Removes all external links and also excludes example.com & social.com
        #     "exclude_domains": {"example.com", "social.com", "facebook.com"},
        #     "exclude_external_links": True
        # },
        # "comprehensive_removal": {
        #     # Exclude multiple tags, remove forms & comments,
        #     # and also remove targeted selectors
        #     "excluded_tags": ["aside", "noscript", "script"],
        #     "excluded_selector": "#promo-section, .social-widget",
        #     "remove_comments": True,
        #     "remove_forms": True
        # }
    }
    return TEST_SCENARIOS


class ScraperEquivalenceTester:
    def __init__(self):
        self.test_cases = {
            "basic": self.generate_basic_html(),
            "complex": self.generate_complex_html(),
            "malformed": self.generate_malformed_html(),
            # 'real_world': self.load_real_samples()
        }

    def generate_basic_html(self):
        return generate_large_html(1000)  # Your existing function

    def generate_complex_html(self):
        return """
        <html><body>
            <div class="nested-content">
                <article>
                    <h1>Main Title</h1>
                    <img src="test.jpg" srcset="test-1x.jpg 1x, test-2x.jpg 2x" data-src="lazy.jpg">
                    <p>Text with <a href="http://test.com">mixed <b>formatting</b></a></p>
                    <iframe src="embedded.html"></iframe>
                </article>
                <nav>
                    <ul>
                        <li><a href="/page1">Link 1</a></li>
                        <li><a href="javascript:void(0)">JS Link</a></li>
                    </ul>
                </nav>
            </div>
        </body></html>
        """

    def generate_malformed_html(self):
        return """
        <div>Unclosed div
        <p>Unclosed paragraph
        <a href="test.com">Link</a>
        <img src=no-quotes>
        <script>document.write("<div>Dynamic</div>");</script>
        <!-- Malformed comment -- > -->
        <![CDATA[Test CDATA]]>
        """

    def load_real_samples(self):
        # Load some real-world HTML samples you've collected
        samples = {
            "article": open("tests/samples/article.html").read(),
            "product": open("tests/samples/product.html").read(),
            "blog": open("tests/samples/blog.html").read(),
        }
        return samples

    def deep_compare_links(self, old_links: Dict, new_links: Dict) -> List[str]:
        """Detailed comparison of link structures"""
        differences = []

        for category in ["internal", "external"]:
            old_urls = {link["href"] for link in old_links[category]}
            new_urls = {link["href"] for link in new_links[category]}

            missing = old_urls - new_urls
            extra = new_urls - old_urls

            if missing:
                differences.append(f"Missing {category} links: {missing}")
            if extra:
                differences.append(f"Extra {category} links: {extra}")

            # Compare link attributes for common URLs
            common = old_urls & new_urls
            for url in common:
                old_link = next(l for l in old_links[category] if l["href"] == url)
                new_link = next(l for l in new_links[category] if l["href"] == url)

                for attr in ["text", "title"]:
                    if old_link[attr] != new_link[attr]:
                        differences.append(
                            f"Link attribute mismatch for {url} - {attr}:"
                            f" old='{old_link[attr]}' vs new='{new_link[attr]}'"
                        )

        return differences

    def deep_compare_media(self, old_media: Dict, new_media: Dict) -> List[str]:
        """Detailed comparison of media elements"""
        differences = []

        for media_type in ["images", "videos", "audios"]:
            old_srcs = {item["src"] for item in old_media[media_type]}
            new_srcs = {item["src"] for item in new_media[media_type]}

            missing = old_srcs - new_srcs
            extra = new_srcs - old_srcs

            if missing:
                differences.append(f"Missing {media_type}: {missing}")
            if extra:
                differences.append(f"Extra {media_type}: {extra}")

            # Compare media attributes for common sources
            common = old_srcs & new_srcs
            for src in common:
                old_item = next(m for m in old_media[media_type] if m["src"] == src)
                new_item = next(m for m in new_media[media_type] if m["src"] == src)

                for attr in ["alt", "description"]:
                    if old_item.get(attr) != new_item.get(attr):
                        differences.append(
                            f"{media_type} attribute mismatch for {src} - {attr}:"
                            f" old='{old_item.get(attr)}' vs new='{new_item.get(attr)}'"
                        )

        return differences

    def compare_html_content(self, old_html: str, new_html: str) -> List[str]:
        """Compare HTML content structure and text"""
        # return compare_html_structurally(old_html, new_html)
        differences = []

        def normalize_html(html: str) -> Tuple[str, str]:
            soup = BeautifulSoup(html, "lxml")
            # Get both structure and text
            structure = " ".join(tag.name for tag in soup.find_all())
            text = " ".join(soup.get_text().split())
            return structure, text

        old_structure, old_text = normalize_html(old_html)
        new_structure, new_text = normalize_html(new_html)

        # Compare structure
        if abs(len(old_structure) - len(new_structure)) > 100:
            # if old_structure != new_structure:
            diff = difflib.unified_diff(
                old_structure.split(), new_structure.split(), lineterm=""
            )
            differences.append("HTML structure differences:\n" + "\n".join(diff))

        # Compare text content
        if abs(len(old_text) - len(new_text)) > 100:
            # if old_text != new_text:
            # Show detailed text differences
            text_diff = difflib.unified_diff(
                old_text.split(), new_text.split(), lineterm=""
            )
            differences.append("Text content differences:\n" + "\n".join(text_diff))

        return differences

    def compare_results(
        self, old_result: Dict, new_result: Dict
    ) -> Dict[str, List[str]]:
        """Comprehensive comparison of scraper outputs"""
        differences = {}

        # Compare links
        link_differences = self.deep_compare_links(
            old_result["links"], new_result["links"]
        )
        if link_differences:
            differences["links"] = link_differences

        # Compare media
        media_differences = self.deep_compare_media(
            old_result["media"], new_result["media"]
        )
        if media_differences:
            differences["media"] = media_differences

        # Compare HTML
        html_differences = self.compare_html_content(
            old_result["cleaned_html"], new_result["cleaned_html"]
        )
        if html_differences:
            differences["html"] = html_differences

        return differences

    def run_tests(self) -> Dict:
        """Run comparison tests using the complicated HTML with multiple parameter scenarios."""
        # We'll still keep some "test_cases" logic from above (basic, complex, malformed).
        # But we add a new section for the complicated HTML scenarios.

        results = {"tests": [], "summary": {"passed": 0, "failed": 0}}

        # 1) First, run the existing 3 built-in test cases (basic, complex, malformed).
        # for case_name, html in self.test_cases.items():
        #     print(f"\nTesting built-in case: {case_name}...")

        #     original = WebScrapingStrategy()
        #     lxml = LXMLWebScrapingStrategy()

        #     start = time.time()
        #     orig_result = original.scrap("http://test.com", html)
        #     orig_time = time.time() - start

        #     print("\nOriginal Mode:")
        #     print(f"Cleaned HTML size: {len(orig_result['cleaned_html'])/1024:.2f} KB")
        #     print(f"Images: {len(orig_result['media']['images'])}")
        #     print(f"External links: {len(orig_result['links']['external'])}")
        #     print(f"Times - Original: {orig_time:.3f}s")

        #     start = time.time()
        #     lxml_result = lxml.scrap("http://test.com", html)
        #     lxml_time = time.time() - start

        #     print("\nLXML Mode:")
        #     print(f"Cleaned HTML size: {len(lxml_result['cleaned_html'])/1024:.2f} KB")
        #     print(f"Images: {len(lxml_result['media']['images'])}")
        #     print(f"External links: {len(lxml_result['links']['external'])}")
        #     print(f"Times - LXML: {lxml_time:.3f}s")

        #     # Compare
        #     diffs = {}
        #     link_diff = self.deep_compare_links(orig_result['links'], lxml_result['links'])
        #     if link_diff:
        #         diffs['links'] = link_diff

        #     media_diff = self.deep_compare_media(orig_result['media'], lxml_result['media'])
        #     if media_diff:
        #         diffs['media'] = media_diff

        #     html_diff = self.compare_html_content(orig_result['cleaned_html'], lxml_result['cleaned_html'])
        #     if html_diff:
        #         diffs['html'] = html_diff

        #     test_result = {
        #         'case': case_name,
        #         'lxml_mode': {
        #             'differences': diffs,
        #             'execution_time': lxml_time
        #         },
        #         'original_time': orig_time
        #     }
        #     results['tests'].append(test_result)

        #     if not diffs:
        #         results['summary']['passed'] += 1
        #     else:
        #         results['summary']['failed'] += 1

        # 2) Now, run the complicated HTML with multiple parameter scenarios.
        complicated_html = generate_complicated_html()
        print("\n=== Testing complicated HTML with multiple parameter scenarios ===")

        # Create the scrapers once (or you can re-create if needed)
        original = WebScrapingStrategy()
        lxml = LXMLWebScrapingStrategy()

        for scenario_name, params in get_test_scenarios().items():
            print(f"\nScenario: {scenario_name}")

            start = time.time()
            orig_result = original.scrap("http://test.com", complicated_html, **params)
            orig_time = time.time() - start

            start = time.time()
            lxml_result = lxml.scrap("http://test.com", complicated_html, **params)
            lxml_time = time.time() - start

            diffs = {}
            link_diff = self.deep_compare_links(
                orig_result["links"], lxml_result["links"]
            )
            if link_diff:
                diffs["links"] = link_diff

            media_diff = self.deep_compare_media(
                orig_result["media"], lxml_result["media"]
            )
            if media_diff:
                diffs["media"] = media_diff

            html_diff = self.compare_html_content(
                orig_result["cleaned_html"], lxml_result["cleaned_html"]
            )
            if html_diff:
                diffs["html"] = html_diff

            test_result = {
                "case": f"complicated_{scenario_name}",
                "lxml_mode": {"differences": diffs, "execution_time": lxml_time},
                "original_time": orig_time,
            }
            results["tests"].append(test_result)

            if not diffs:
                results["summary"]["passed"] += 1
                print(
                    f"✅ [OK] No differences found. Time(Orig: {orig_time:.3f}s, LXML: {lxml_time:.3f}s)"
                )
            else:
                results["summary"]["failed"] += 1
                print("❌ Differences found:")
                for category, dlist in diffs.items():
                    print(f"  {category}:")
                    for d in dlist:
                        print(f"    - {d}")

        return results

    def print_report(self, results: Dict):
        """Generate detailed equivalence report"""
        print("\n=== Scraper Equivalence Test Report ===\n")
        print(f"Total Cases: {len(results['tests'])}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")

        for test in results["tests"]:
            print(f"\nTest Case: {test['case']}")

            if not test["lxml_mode"]["differences"]:
                print("✅ All implementations produced identical results")
                print(
                    f"Times - Original: {test['original_time']:.3f}s, "
                    f"LXML: {test['lxml_mode']['execution_time']:.3f}s"
                )
            else:
                print("❌ Differences found:")

                if test["lxml_mode"]["differences"]:
                    print("\nLXML Mode Differences:")
                    for category, diffs in test["lxml_mode"]["differences"].items():
                        print(f"\n{category}:")
                        for diff in diffs:
                            print(f"  - {diff}")


def main():
    tester = ScraperEquivalenceTester()
    results = tester.run_tests()
    tester.print_report(results)

    # Save detailed results for debugging
    with open("scraper_equivalence_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
