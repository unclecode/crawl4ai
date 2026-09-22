from pathlib import Path
import asyncio
from dataclasses import asdict
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.async_crawler_strategy import AsyncCrawlerStrategy
from crawl4ai.models import AsyncCrawlResponse, ScrapingResult 
from crawl4ai.content_scraping_strategy import ContentScrapingStrategy
from .processor import NaivePDFProcessorStrategy  # Assuming your current PDF code is in pdf_processor.py

# Default resource bounds for remote PDF fetches. These cap what an untrusted
# caller can make the process download and parse; see set_url_validator() for
# the destination side of the same problem.
DEFAULT_MAX_PDF_BYTES = 100 * 1024 * 1024  # 100 MiB
DEFAULT_MAX_PDF_PAGES = 2000
DEFAULT_MAX_REDIRECTS = 5

_REDIRECT_STATUSES = (301, 302, 303, 307, 308)

# Destination-policy hooks, injected by whoever embeds the library.
#
# The library deliberately has no egress policy of its own: as a plain library
# the caller already chooses the URL, so there is nothing to defend against.
# It matters when the URL comes from an untrusted API client, which is the
# Docker server's situation -- deploy/docker/server.py installs the egress
# broker here at boot so the PDF path enforces the same non-global-IP policy
# the browser path already gets via enforce_egress().
#
# _url_validator runs on every hop (initial URL and each redirect Location).
# _peer_ip_validator runs on the IP actually connected to; without it a name
# that passed validation could still resolve to an internal address on the
# second lookup requests performs (DNS rebinding).
# Both must raise to block; returning anything is treated as "allowed".
_url_validator = None
_peer_ip_validator = None


def set_url_validator(fn):
    """Install a per-hop destination validator: fn(url) -> None, raises to block."""
    global _url_validator
    _url_validator = fn


def set_peer_ip_validator(fn):
    """Install a connected-peer check: fn(ip: str) -> None, raises to block."""
    global _peer_ip_validator
    _peer_ip_validator = fn


class PDFCrawlerStrategy(AsyncCrawlerStrategy):
    """Crawler strategy for PDF documents.

    This strategy does not fetch or parse anything itself — it returns a
    placeholder response (``placeholder_html=True``). It MUST be paired with
    ``PDFContentScrapingStrategy`` (via ``CrawlerRunConfig.scraping_strategy``),
    which performs the actual PDF download and content extraction. With any
    other scraping strategy the result will contain only the placeholder text.
    """
    def __init__(self, logger: AsyncLogger = None):
        self.logger = logger
        
    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        # Just pass through with empty HTML - scraper will handle actual processing
        return AsyncCrawlResponse(
            html="Scraper will handle the real work",  # Scraper will handle the real work
            response_headers={"Content-Type": "application/pdf"},
            status_code=200,
            placeholder_html=True, # HTML is a placeholder for the actual content, which will be produced by the PDFContentScrapingStrategy
        )
    
    async def close(self):
        pass        
        
    async def __aenter__(self):        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

class PDFContentScrapingStrategy(ContentScrapingStrategy):
    """
    A content scraping strategy for PDF files.
    
    Attributes:
        save_images_locally (bool): Whether to save images locally.
        extract_images (bool): Whether to extract images from PDF.
        image_save_dir (str): Directory to save extracted images.
        logger (AsyncLogger): Logger instance for recording events and errors.
        
    Methods:
        scrap(url: str, html: str, **params) -> ScrapingResult:
            Scrap content from a PDF file.
        ascrap(url: str, html: str, **kwargs) -> ScrapingResult:
            Asynchronous version of scrap.
            
    Usage:
        strategy = PDFContentScrapingStrategy(
            save_images_locally=False,
            extract_images=False,
            image_save_dir=None,
            logger=logger
        )
        
    """
    def __init__(self,
                 save_images_locally : bool = False,
                 extract_images : bool = False,
                 image_save_dir : str = None,
                 batch_size: int = 4,
                 max_pdf_bytes: int = DEFAULT_MAX_PDF_BYTES,
                 max_pdf_pages: int = DEFAULT_MAX_PDF_PAGES,
                 max_redirects: int = DEFAULT_MAX_REDIRECTS,
                 logger: AsyncLogger = None,
                 url_validator=None):
        self.logger = logger
        # Per-instance validator, set by deploy/docker/api.py on the strategy it
        # builds for a request. It runs in addition to the module-level policy
        # installed at server boot, not instead of it.
        self.url_validator = url_validator
        self.max_pdf_bytes = max_pdf_bytes
        self.max_pdf_pages = max_pdf_pages
        self.max_redirects = max_redirects
        self.pdf_processor = NaivePDFProcessorStrategy(
            save_images_locally=save_images_locally,
            extract_images=extract_images,
            image_save_dir=image_save_dir,
            batch_size=batch_size,
            max_pages=max_pdf_pages
        )
        self._temp_files = []  # Track temp files for cleanup

    def scrap(self, url: str, html: str, **params) -> ScrapingResult:
        """
        Scrap content from a PDF file.
        
        Args:
            url (str): The URL of the PDF file.
            html (str): The HTML content of the page.
            **params: Additional parameters.
        
        Returns:
            ScrapingResult: The scraped content.
        """
        # Download if URL or use local path
        pdf_path = self._get_pdf_path(url)
        try:
            # Process PDF
            # result = self.pdf_processor.process(Path(pdf_path))
            result = self.pdf_processor.process_batch(Path(pdf_path))
            
            # Combine page HTML
            cleaned_html = f"""
        <html>
            <head><meta name="pdf-pages" content="{len(result.pages)}"></head>
            <body>
                {''.join(f'<div class="pdf-page" data-page="{i+1}">{page.html}</div>'
                         for i, page in enumerate(result.pages))}
            </body>
        </html>
        """
            
            # Accumulate media and links with page numbers
            media = {"images": []}
            links = {"urls": []}
            
            for page in result.pages:
                # Add page number to each image
                for img in page.images:
                    img["page"] = page.page_number
                    media["images"].append(img)
                
                # Add page number to each link
                for link in page.links:
                    links["urls"].append({
                        "url": link,
                        "page": page.page_number
                    })

            return ScrapingResult(
                cleaned_html=cleaned_html,
                success=True,
                media=media,
                links=links,
                metadata=asdict(result.metadata)
            )
        finally:
            # Cleanup temp file if downloaded
            if url.startswith(("http://", "https://")):
                try:
                    Path(pdf_path).unlink(missing_ok=True)
                    if pdf_path in self._temp_files:
                        self._temp_files.remove(pdf_path)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Failed to cleanup temp file {pdf_path}: {e}")

    async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # For simple cases, you can use the sync version
        return await asyncio.to_thread(self.scrap, url, html, **kwargs)
        

    def _discard_temp_file(self, path: str) -> None:
        Path(path).unlink(missing_ok=True)
        if path in self._temp_files:
            self._temp_files.remove(path)

    @staticmethod
    def _peer_ip(response):
        """Best-effort peer address of a streaming response, or None.

        The socket lives in a different place across urllib3 majors, and on a
        bodyless response (a redirect) it is already released -- hence None
        rather than an exception, and hence `strict` in _check_peer_ip.
        """
        for get_sock in (
            lambda: response.raw._fp.fp.raw._sock,            # urllib3 2.x
            lambda: response.raw._original_response.fp.raw._sock,  # urllib3 1.x
            lambda: response.raw._connection.sock,
        ):
            try:
                sock = get_sock()
                if sock is not None:
                    return sock.getpeername()[0]
            except Exception:
                continue
        return None

    def _check_peer_ip(self, response, strict: bool = True) -> None:
        """Validate the address actually connected to.

        Validating the URL only proves the *name* resolved somewhere allowed;
        requests resolves it again when it dials, so a hostname with a short
        TTL can point somewhere internal by then (DNS rebinding). Checking the
        connected peer is what closes that window.

        `strict` is False for redirect hops, where urllib3 has already released
        the socket and no peer is observable. Those hops are still covered by
        the per-hop URL validation; what strict mode protects is the response
        whose body we are about to read back to the caller, which is where a
        rebound connection would actually exfiltrate something.
        """
        if not _peer_ip_validator:
            return

        peer = self._peer_ip(response)
        if peer is None:
            if not strict:
                return
            # Fail closed: a policy was installed, so an unverifiable peer on
            # the response we are about to read is not something to wave through.
            response.close()
            raise RuntimeError("Could not determine peer address for PDF download")

        try:
            _peer_ip_validator(peer)
        except Exception:
            response.close()
            raise

    def _fetch_with_redirect_checks(self, requests, url: str):
        """GET `url`, validating every hop against the injected destination policy.

        Redirects are followed by hand because requests would otherwise chase a
        Location into a private address without consulting the validator at all
        -- a public URL that 302s to 169.254.169.254 was the reported SSRF.
        Returns an open streaming response; the caller closes it.
        """
        from urllib.parse import urljoin

        current = url
        # One Session for the whole chain: a bare requests.get() per hop starts
        # with an empty cookie jar, so a host that sets a cookie and then
        # redirects (common for gated or CDN-signed PDFs) would never get it
        # back. allow_redirects=True used to carry cookies for us.
        session = requests.Session()
        for _ in range(self.max_redirects + 1):
            if self.url_validator:
                self.url_validator(current)
            if _url_validator:
                _url_validator(current)

            # Connection timeout: 20s, Read timeout: 600s (for large PDFs)
            response = session.get(
                current, stream=True, timeout=(20, 60 * 10), allow_redirects=False
            )
            is_redirect = response.status_code in _REDIRECT_STATUSES
            self._check_peer_ip(response, strict=not is_redirect)

            if is_redirect:
                location = response.headers.get('location')
                response.close()
                if not location:
                    raise RuntimeError(f"Redirect without Location header from {current}")
                # Relative Locations are legal, so resolve against the current
                # URL before validating -- the validator needs an absolute URL.
                current = urljoin(current, location)
                continue

            response.raise_for_status()
            return response

        raise RuntimeError(
            f"Too many redirects (>{self.max_redirects}) downloading PDF from {url}"
        )

    def _get_pdf_path(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            import tempfile
            import requests

            # Create temp file with .pdf extension
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()  # Close handle immediately; file persists due to delete=False
            self._temp_files.append(temp_file.name)

            try:
                if self.logger:
                    self.logger.info(f"Downloading PDF from {url}...")

                response = self._fetch_with_redirect_checks(requests, url)

                # content-length is a hint only: it is attacker-controlled and
                # may be absent or understated, so the running total is what
                # enforces the cap.
                total_size = int(response.headers.get('content-length', 0) or 0)
                downloaded = 0

                with response:
                    with open(temp_file.name, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            downloaded += len(chunk)
                            if downloaded > self.max_pdf_bytes:
                                raise RuntimeError(
                                    f"PDF from {url} exceeds max_pdf_bytes "
                                    f"({self.max_pdf_bytes} bytes)"
                                )
                            f.write(chunk)
                            if self.logger and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                if progress % 10 < 0.1:  # Log every 10%
                                    self.logger.debug(f"PDF download progress: {progress:.0f}%")

                if self.logger:
                    self.logger.info(f"PDF downloaded successfully: {temp_file.name}")

                return temp_file.name

            except requests.exceptions.Timeout as e:
                self._discard_temp_file(temp_file.name)
                raise RuntimeError(f"Timeout downloading PDF from {url}: {str(e)}")
            except Exception as e:
                self._discard_temp_file(temp_file.name)
                raise RuntimeError(f"Failed to download PDF from {url}: {str(e)}")

        elif url.startswith("file://"):
            return url[7:]  # Strip file:// prefix
            
        return url  # Assume local path
    

__all__ = ["PDFCrawlerStrategy", "PDFContentScrapingStrategy"]