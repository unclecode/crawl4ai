from .url_filter import URLFilter

class ContentTypeFilter(URLFilter):
    def __init__(self, contentType: str):
        self.contentType = contentType
    def apply(self, url: str) -> bool:
        #TODO: This is a stub. Will implement this later
        return True