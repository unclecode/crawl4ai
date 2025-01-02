from .service import BrowserFarmService

class DockerBrowser:
    """Client to get browser endpoints from BrowserFarmService"""
    
    def __init__(self):
        self.service = BrowserFarmService()
    
    async def get_browser_endpoint(self) -> tuple[str, int]:
        """Get host/port for the browser"""
        endpoint = await self.service.get_available_browser()
        return endpoint.host, endpoint.port
