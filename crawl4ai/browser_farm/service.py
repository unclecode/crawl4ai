from dataclasses import dataclass
import aiohttp

@dataclass
class BrowserEndpoint:
    """Represents a browser endpoint in the farm"""
    host: str
    port: int

class BrowserFarmService:
    """MVP: Returns hardcoded browser endpoint"""
    def __init__(self):
        # For MVP, hardcode the values 
        self._browser = BrowserEndpoint(
            host="localhost",
            port=9333  # Mapped from Docker's 9223
        )
    
    async def get_available_browser(self) -> BrowserEndpoint:
        """Returns our single browser endpoint"""
        if not await self.health_check():
            raise ConnectionError("No healthy browser available")
        return self._browser

    async def health_check(self) -> bool:
        """Basic health check - verify endpoint responds"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self._browser.host}:{self._browser.port}/json/version"
                async with session.get(url) as response:
                    return response.status == 200
        except:
            return False
