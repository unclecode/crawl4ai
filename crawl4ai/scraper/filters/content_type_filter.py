from .url_filter import URLFilter
from typing import List, Union
from urllib.parse import urlparse
import mimetypes


class ContentTypeFilter(URLFilter):
    """Filter URLs based on expected content type"""
    
    def __init__(self, allowed_types: Union[str, List[str]], 
                 check_extension: bool = True):
        super().__init__()
        self.allowed_types = [allowed_types] if isinstance(allowed_types, str) else allowed_types
        self.check_extension = check_extension
        self._normalize_types()

    def _normalize_types(self):
        """Normalize content type strings"""
        self.allowed_types = [t.lower() for t in self.allowed_types]

    def _check_extension(self, url: str) -> bool:
        """Check URL's file extension"""
        ext = urlparse(url).path.split('.')[-1].lower() if '.' in urlparse(url).path else ''
        if not ext:
            return True  # No extension, might be dynamic content
            
        guessed_type = mimetypes.guess_type(url)[0]
        return any(allowed in (guessed_type or '').lower() for allowed in self.allowed_types)

    def apply(self, url: str) -> bool:
        """Check if URL's content type is allowed"""
        result = True
        if self.check_extension:
            result = self._check_extension(url)
        self._update_stats(result)
        return result

# class ContentTypeFilter(URLFilter):
#     def __init__(self, contentType: str):
#         self.contentType = contentType
#     def apply(self, url: str) -> bool:
#         #TODO: This is a stub. Will implement this later
#         return True