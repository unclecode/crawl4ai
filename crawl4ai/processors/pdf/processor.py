import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from time import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Union
import base64
import tempfile
from .utils import *
from .utils import (
    apply_png_predictor,
    clean_pdf_text,
    clean_pdf_text_to_html,
)

# Remove direct PyPDF2 imports from the top
# import PyPDF2
# from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

@dataclass
class PDFMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    producer: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    pages: int = 0
    encrypted: bool = False
    file_size: Optional[int] = None

@dataclass
class PDFPage:
    page_number: int
    raw_text: str = ""
    markdown: str = ""
    html: str = ""
    images: List[Dict] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    layout: List[Dict] = field(default_factory=list)

@dataclass
class PDFProcessResult:
    metadata: PDFMetadata
    pages: List[PDFPage]
    processing_time: float = 0.0
    version: str = "1.0"

class PDFProcessorStrategy(ABC):
    @abstractmethod
    def process(self, pdf_path: Path) -> PDFProcessResult:
        pass

class NaivePDFProcessorStrategy(PDFProcessorStrategy):
    def __init__(self, image_dpi: int = 144, image_quality: int = 85, extract_images: bool = True, 
                 save_images_locally: bool = False, image_save_dir: Optional[Path] = None, batch_size: int = 4):
        # Import check at initialization time
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")
            
        self.image_dpi = image_dpi
        self.image_quality = image_quality
        self.current_page_number = 0
        self.extract_images = extract_images
        self.save_images_locally = save_images_locally
        self.image_save_dir = image_save_dir
        self.batch_size = batch_size
        self._temp_dir = None

    def process(self, pdf_path: Path) -> PDFProcessResult:
        # Import inside method to allow dependency to be optional
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")
            
        start_time = time()
        result = PDFProcessResult(
            metadata=PDFMetadata(),
            pages=[],
            version="1.1"
        )

        try:
            with pdf_path.open('rb') as file:
                reader = PdfReader(file)
                result.metadata = self._extract_metadata(pdf_path, reader)
                
                # Handle image directory
                image_dir = None
                if self.extract_images and self.save_images_locally:
                    if self.image_save_dir:
                        image_dir = Path(self.image_save_dir)
                        image_dir.mkdir(exist_ok=True, parents=True)
                    else:
                        self._temp_dir = tempfile.mkdtemp(prefix='pdf_images_')
                        image_dir = Path(self._temp_dir)

                for page_num, page in enumerate(reader.pages):
                    self.current_page_number = page_num + 1
                    pdf_page = self._process_page(page, image_dir)
                    result.pages.append(pdf_page)

        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise
        finally:
            # Cleanup temp directory if it was created
            if self._temp_dir and not self.image_save_dir:
                import shutil
                try:
                    shutil.rmtree(self._temp_dir)
                except Exception as e:
                    logger.error(f"Failed to cleanup temp directory: {str(e)}")

        result.processing_time = time() - start_time
        return result

    def process_batch(self, pdf_path: Path) -> PDFProcessResult:
        """Like process() but processes PDF pages in parallel batches"""
        # Import inside method to allow dependency to be optional
        try:
            from PyPDF2 import PdfReader
            import PyPDF2  # For type checking
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")
            
        import concurrent.futures
        import threading
        
        # Initialize PyPDF2 thread support
        if not hasattr(threading.current_thread(), "_children"): 
            threading.current_thread()._children = set()
        
        start_time = time()
        result = PDFProcessResult(
            metadata=PDFMetadata(),
            pages=[],
            version="1.1" 
        )

        try:
            # Get metadata and page count from main thread
            with pdf_path.open('rb') as file:
                reader = PdfReader(file)
                result.metadata = self._extract_metadata(pdf_path, reader)
                total_pages = len(reader.pages)

            # Handle image directory setup
            image_dir = None
            if self.extract_images and self.save_images_locally:
                if self.image_save_dir:
                    image_dir = Path(self.image_save_dir)
                    image_dir.mkdir(exist_ok=True, parents=True)
                else:
                    self._temp_dir = tempfile.mkdtemp(prefix='pdf_images_')
                    image_dir = Path(self._temp_dir)

            def process_page_safely(page_num: int):
                # Each thread opens its own file handle
                with pdf_path.open('rb') as file:
                    thread_reader = PdfReader(file)
                    page = thread_reader.pages[page_num]
                    self.current_page_number = page_num + 1
                    return self._process_page(page, image_dir)

            # Process pages in parallel batches
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                futures = []
                for page_num in range(total_pages):
                    future = executor.submit(process_page_safely, page_num)
                    futures.append((page_num + 1, future))

                # Collect results in order
                result.pages = [None] * total_pages
                for page_num, future in futures:
                    try:
                        pdf_page = future.result()
                        result.pages[page_num - 1] = pdf_page
                    except Exception as e:
                        logger.error(f"Failed to process page {page_num}: {str(e)}")
                        raise

        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise
        finally:
            # Cleanup temp directory if it was created
            if self._temp_dir and not self.image_save_dir:
                import shutil
                try:
                    shutil.rmtree(self._temp_dir)
                except Exception as e:
                    logger.error(f"Failed to cleanup temp directory: {str(e)}")

        result.processing_time = time() - start_time
        return result

    def _process_page(self, page, image_dir: Optional[Path]) -> PDFPage:
        pdf_page = PDFPage(
            page_number=self.current_page_number,
        )

        # Text and font extraction
        def visitor_text(text, cm, tm, font_dict, font_size):
            pdf_page.raw_text += text
            pdf_page.layout.append({
                "type": "text",
                "text": text,
                "x": tm[4],
                "y": tm[5],
            })
        
        page.extract_text(visitor_text=visitor_text)

        # Image extraction
        if self.extract_images:
            pdf_page.images = self._extract_images(page, image_dir)

        # Link extraction
        pdf_page.links = self._extract_links(page)
        
        # Add markdown content
        pdf_page.markdown = clean_pdf_text(self.current_page_number, pdf_page.raw_text)
        pdf_page.html = clean_pdf_text_to_html(self.current_page_number, pdf_page.raw_text)

        return pdf_page

    def _extract_images(self, page, image_dir: Optional[Path]) -> List[Dict]:
        # Import PyPDF2 for type checking only when needed
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")
            
        if not self.extract_images:
            return []

        images = []
        try:
            resources = page.get("/Resources")
            if resources:  # Check if resources exist
                resources = resources.get_object()  # Resolve IndirectObject
                if '/XObject' in resources:
                    xobjects = resources['/XObject'].get_object()
                    img_count = 0
                    for obj_name in xobjects:
                        xobj = xobjects[obj_name]
                        if hasattr(xobj, 'get_object') and callable(xobj.get_object):
                            xobj = xobj.get_object()
                            if xobj.get('/Subtype') == '/Image':
                                try:
                                    img_count += 1
                                    img_filename = f"page_{self.current_page_number}_img_{img_count}"
                                    data = xobj.get_data()
                                    filters = xobj.get('/Filter', [])
                                    if not isinstance(filters, list):
                                        filters = [filters]

                                    # Resolve IndirectObjects in properties
                                    width = xobj.get('/Width', 0)
                                    height = xobj.get('/Height', 0)
                                    color_space = xobj.get('/ColorSpace', '/DeviceRGB')
                                    if isinstance(color_space, PyPDF2.generic.IndirectObject):
                                        color_space = color_space.get_object()

                                    # Handle different image encodings
                                    success = False
                                    image_format = 'bin'
                                    image_data = None
                                    
                                    if '/FlateDecode' in filters:
                                        try:
                                            decode_parms = xobj.get('/DecodeParms', {})
                                            if isinstance(decode_parms, PyPDF2.generic.IndirectObject):
                                                decode_parms = decode_parms.get_object()
                                            
                                            predictor = decode_parms.get('/Predictor', 1)
                                            bits = xobj.get('/BitsPerComponent', 8)
                                            colors = 3 if color_space == '/DeviceRGB' else 1

                                            if predictor >= 10:
                                                data = apply_png_predictor(data, width, bits, colors)

                                            # Create PIL Image
                                            from PIL import Image
                                            mode = 'RGB' if color_space == '/DeviceRGB' else 'L'
                                            img = Image.frombytes(mode, (width, height), data)
                                            
                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.png')
                                                img.save(final_path)
                                                image_data = str(final_path)
                                            else:
                                                import io
                                                img_byte_arr = io.BytesIO()
                                                img.save(img_byte_arr, format='PNG')
                                                image_data = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                                            
                                            success = True
                                            image_format = 'png'
                                        except Exception as e:
                                            logger.error(f"FlateDecode error: {str(e)}")

                                    elif '/DCTDecode' in filters:
                                        # JPEG image
                                        try:
                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.jpg')
                                                with open(final_path, 'wb') as f:
                                                    f.write(data)
                                                image_data = str(final_path)
                                            else:
                                                image_data = base64.b64encode(data).decode('utf-8')
                                            success = True
                                            image_format = 'jpeg'
                                        except Exception as e:
                                            logger.error(f"JPEG save error: {str(e)}")

                                    elif '/CCITTFaxDecode' in filters:
                                        try:
                                            if data[:4] != b'II*\x00':
                                                # Add TIFF header if missing
                                                tiff_header = b'II*\x00\x08\x00\x00\x00\x0e\x00\x00\x01\x03\x00\x01\x00\x00\x00' + \
                                                            width.to_bytes(4, 'little') + \
                                                            b'\x01\x03\x00\x01\x00\x00\x00' + \
                                                            height.to_bytes(4, 'little') + \
                                                            b'\x01\x12\x00\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01\x17\x00\x04\x00\x00\x00\x01\x00\x00\x00J\x01\x1B\x00\x05\x00\x00\x00\x01\x00\x00\x00R\x01\x28\x00\x03\x00\x00\x00\x01\x00\x02\x00\x00'
                                                data = tiff_header + data
                                            
                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.tiff')
                                                with open(final_path, 'wb') as f:
                                                    f.write(data)
                                                image_data = str(final_path)
                                            else:
                                                image_data = base64.b64encode(data).decode('utf-8')
                                            success = True
                                            image_format = 'tiff'
                                        except Exception as e:
                                            logger.error(f"CCITT save error: {str(e)}")

                                    elif '/JPXDecode' in filters:
                                        # JPEG 2000
                                        try:
                                            if self.save_images_locally:
                                                final_path = (image_dir / img_filename).with_suffix('.jp2')
                                                with open(final_path, 'wb') as f:
                                                    f.write(data)
                                                image_data = str(final_path)
                                            else:
                                                image_data = base64.b64encode(data).decode('utf-8')
                                            success = True
                                            image_format = 'jpeg2000'
                                        except Exception as e:
                                            logger.error(f"JPEG2000 save error: {str(e)}")

                                    if success and image_data:
                                        image_info = {
                                            "format": image_format,
                                            "width": width,
                                            "height": height,
                                            "color_space": str(color_space),
                                            "bits_per_component": xobj.get('/BitsPerComponent', 1)
                                        }
                                        
                                        if self.save_images_locally:
                                            image_info["path"] = image_data
                                        else:
                                            image_info["data"] = image_data
                                            
                                        images.append(image_info)
                                    else:
                                        # Fallback: Save raw data
                                        if self.save_images_locally:
                                            final_path = (image_dir / img_filename).with_suffix('.bin')
                                            with open(final_path, 'wb') as f:
                                                f.write(data)
                                            logger.warning(f"Saved raw image data to {final_path}")
                                        else:
                                            image_data = base64.b64encode(data).decode('utf-8')
                                            images.append({
                                                "format": "bin",
                                                "width": width,
                                                "height": height,
                                                "color_space": str(color_space),
                                                "bits_per_component": xobj.get('/BitsPerComponent', 1),
                                                "data": image_data
                                            })

                                except Exception as e:
                                    logger.error(f"Error processing image: {str(e)}")
        except Exception as e:
            logger.error(f"Image extraction error: {str(e)}")
        
        return images

    def _extract_links(self, page) -> List[str]:
        links = []
        if '/Annots' in page:
            try:
                for annot in page['/Annots']:
                    a = annot.get_object()
                    if '/A' in a and '/URI' in a['/A']:
                        links.append(a['/A']['/URI'])
            except Exception as e:
                print(f"Link error: {str(e)}")
        return links

    def _extract_metadata(self, pdf_path: Path, reader = None) -> PDFMetadata:
        # Import inside method to allow dependency to be optional 
        if reader is None:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")

        meta = reader.metadata or {}
        created = self._parse_pdf_date(meta.get('/CreationDate', ''))
        modified = self._parse_pdf_date(meta.get('/ModDate', ''))
        
        return PDFMetadata(
            title=meta.get('/Title'),
            author=meta.get('/Author'),
            producer=meta.get('/Producer'),
            created=created,
            modified=modified,
            pages=len(reader.pages),
            encrypted=reader.is_encrypted,
            file_size=pdf_path.stat().st_size
        )

    def _parse_pdf_date(self, date_str: str) -> Optional[datetime]:
        try:
            match = re.match(r'D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', date_str)
            if not match:
                return None
                
            return datetime(
                year=int(match[1]),
                month=int(match[2]),
                day=int(match[3]),
                hour=int(match[4]),
                minute=int(match[5]),
                second=int(match[6])
            )
        except:
            return None

# Usage example
if __name__ == "__main__":
    import json
    from pathlib import Path
    
    try:
        # Import PyPDF2 only when running the file directly
        import PyPDF2
        from PyPDF2 import PdfReader
    except ImportError:
        print("PyPDF2 is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")
        exit(1)
        
    current_dir = Path(__file__).resolve().parent
    pdf_path = f'{current_dir}/test.pdf'
    
    strategy = NaivePDFProcessorStrategy()
    result = strategy.process(Path(pdf_path))
    
    # Convert to JSON
    json_output = asdict(result)
    print(json.dumps(json_output, indent=2, default=str))
    
    with open(f'{current_dir}/test.html', 'w') as f:
        for page in result.pages:
            f.write(f'<h1>Page {page["page_number"]}</h1>')
            f.write(page['html'])
    with open(f'{current_dir}/test.md', 'w') as f:
        for page in result.pages:
            f.write(f'# Page {page["page_number"]}\n\n')
            f.write(clean_pdf_text(page["page_number"], page['raw_text']))
            f.write('\n\n')
