import os
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urljoin, urlparse

def scrape_docs(base_url, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all links in the navigation
    nav = soup.find('nav', class_='md-nav')
    links = set()
    if nav:
        for a in nav.find_all('a', href=True):
            href = a['href']
            # Make sure it's a documentation link and not an external one
            if not href.startswith('http'):
                full_url = urljoin(base_url, href)
                # Add only unique URLs
                links.add(full_url)

    # Also, get links from the initial page content if nav is not sufficient
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not href.startswith('http'):
            full_url = urljoin(base_url, href)
            if '/core/' in full_url or '/advanced/' in full_url or '/extraction/' in full_url or '/api/' in full_url:
                links.add(full_url)

    # Add the base url as well to scrape the landing page
    links.add(base_url)

    for link in links:
        try:
            page_response = requests.get(link)
            page_soup = BeautifulSoup(page_response.content, 'html.parser')

            # Try to find the main content, assuming it's in a specific element
            # This might need adjustment based on the actual page structure.
            # Common for MkDocs is 'div.md-content'
            content_element = page_soup.find('div', class_='md-content')
            if not content_element:
                # Fallback to article tag
                content_element = page_soup.find('article')
            if not content_element:
                # Fallback to main tag
                content_element = page_soup.find('main')

            if content_element:
                # Convert the content HTML to Markdown
                markdown_content = md(str(content_element))

                # Create a filename from the URL
                path = urlparse(link).path
                # A / path should be index.md
                if path == '/' or path == '':
                    filename = 'index.md'
                else:
                    filename = os.path.basename(path.strip('/')) + '.md'

                # if the filename is just .md, it means it was a directory, so use index.md
                if filename == '.md':
                    filename = 'index.md'

                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"Saved {link} to {filepath}")
            else:
                print(f"Could not find main content for {link}")

        except requests.exceptions.RequestException as e:
            print(f"Could not fetch {link}: {e}")

if __name__ == '__main__':
    BASE_URL = 'https://docs.crawl4ai.com/'
    OUTPUT_DIR = 'documentation'
    scrape_docs(BASE_URL, OUTPUT_DIR)
