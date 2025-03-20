import random
from typing import Optional, Literal, List, Dict, Tuple
import re

from abc import ABC, abstractmethod
from fake_useragent import UserAgent
import requests
from lxml import html
import json
from typing import Union

class UAGen(ABC):
   @abstractmethod
   def generate(self, 
               browsers: Optional[List[str]] = None,
               os: Optional[Union[str, List[str]]] = None,
               min_version: float = 0.0,
               platforms: Optional[Union[str, List[str]]] = None,
               pct_threshold: Optional[float] = None,
               fallback: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36") -> Union[str, Dict]:
       pass
   
   @staticmethod
   def generate_client_hints( user_agent: str) -> str:
        """Generate Sec-CH-UA header value based on user agent string"""
        def _parse_user_agent(user_agent: str) -> Dict[str, str]:
            """Parse a user agent string to extract browser and version information"""
            browsers = {
                "chrome": r"Chrome/(\d+)",
                "edge": r"Edg/(\d+)",
                "safari": r"Version/(\d+)",
                "firefox": r"Firefox/(\d+)",
            }

            result = {}
            for browser, pattern in browsers.items():
                match = re.search(pattern, user_agent)
                if match:
                    result[browser] = match.group(1)

            return result
        browsers = _parse_user_agent(user_agent)

        # Client hints components
        hints = []

        # Handle different browser combinations
        if "chrome" in browsers:
            hints.append(f'"Chromium";v="{browsers["chrome"]}"')
            hints.append('"Not_A Brand";v="8"')

            if "edge" in browsers:
                hints.append(f'"Microsoft Edge";v="{browsers["edge"]}"')
            else:
                hints.append(f'"Google Chrome";v="{browsers["chrome"]}"')

        elif "firefox" in browsers:
            # Firefox doesn't typically send Sec-CH-UA
            return '""'

        elif "safari" in browsers:
            # Safari's format for client hints
            hints.append(f'"Safari";v="{browsers["safari"]}"')
            hints.append('"Not_A Brand";v="8"')

        return ", ".join(hints)

class ValidUAGenerator(UAGen):
   def __init__(self):
       self.ua = UserAgent()
       
   def generate(self,
               browsers: Optional[List[str]] = None,
               os: Optional[Union[str, List[str]]] = None, 
               min_version: float = 0.0,
               platforms: Optional[Union[str, List[str]]] = None,
               pct_threshold: Optional[float] = None,
               fallback: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36") -> str:
       
       self.ua = UserAgent(
           browsers=browsers or ['Chrome', 'Firefox', 'Edge'],
           os=os or ['Windows', 'Mac OS X'],
           min_version=min_version,
           platforms=platforms or ['desktop'],
           fallback=fallback
       )
       return self.ua.random

class OnlineUAGenerator(UAGen):
   def __init__(self):
       self.agents = []
       self._fetch_agents()
       
   def _fetch_agents(self):
       try:
           response = requests.get(
               'https://www.useragents.me/',
               timeout=5,
               headers={'Accept': 'text/html,application/xhtml+xml'}
           )
           response.raise_for_status()
           
           tree = html.fromstring(response.content)
           json_text = tree.cssselect('#most-common-desktop-useragents-json-csv > div:nth-child(1) > textarea')[0].text
           self.agents = json.loads(json_text)
       except Exception as e:
           print(f"Error fetching agents: {e}")
           
   def generate(self,
               browsers: Optional[List[str]] = None,
               os: Optional[Union[str, List[str]]] = None,
               min_version: float = 0.0,
               platforms: Optional[Union[str, List[str]]] = None, 
               pct_threshold: Optional[float] = None,
               fallback: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36") -> Dict:
       
       if not self.agents:
           self._fetch_agents()
           
       filtered_agents = self.agents
       
       if pct_threshold:
           filtered_agents = [a for a in filtered_agents if a['pct'] >= pct_threshold]
           
       if browsers:
           filtered_agents = [a for a in filtered_agents 
                            if any(b.lower() in a['ua'].lower() for b in browsers)]
           
       if os:
           os_list = [os] if isinstance(os, str) else os
           filtered_agents = [a for a in filtered_agents 
                            if any(o.lower() in a['ua'].lower() for o in os_list)]
           
       if platforms:
           platform_list = [platforms] if isinstance(platforms, str) else platforms
           filtered_agents = [a for a in filtered_agents 
                            if any(p.lower() in a['ua'].lower() for p in platform_list)]
           
       return filtered_agents[0] if filtered_agents else {'ua': fallback, 'pct': 0}



class UserAgentGenerator():
    """
    Generate random user agents with specified constraints.

    Attributes:
        desktop_platforms (dict): A dictionary of possible desktop platforms and their corresponding user agent strings.
        mobile_platforms (dict): A dictionary of possible mobile platforms and their corresponding user agent strings.
        browser_combinations (dict): A dictionary of possible browser combinations and their corresponding user agent strings.
        rendering_engines (dict): A dictionary of possible rendering engines and their corresponding user agent strings.
        chrome_versions (list): A list of possible Chrome browser versions.
        firefox_versions (list): A list of possible Firefox browser versions.
        edge_versions (list): A list of possible Edge browser versions.
        safari_versions (list): A list of possible Safari browser versions.
        ios_versions (list): A list of possible iOS browser versions.
        android_versions (list): A list of possible Android browser versions.

        Methods:
            generate_user_agent(
                platform: Literal["desktop", "mobile"] = "desktop",
                browser: str = "chrome",
                rendering_engine: str = "chrome_webkit",
                chrome_version: Optional[str] = None,
                firefox_version: Optional[str] = None,
                edge_version: Optional[str] = None,
                safari_version: Optional[str] = None,
                ios_version: Optional[str] = None,
                android_version: Optional[str] = None
            ): Generates a random user agent string based on the specified parameters.
    """

    def __init__(self):
        # Previous platform definitions remain the same...
        self.desktop_platforms = {
            "windows": {
                "10_64": "(Windows NT 10.0; Win64; x64)",
                "10_32": "(Windows NT 10.0; WOW64)",
            },
            "macos": {
                "intel": "(Macintosh; Intel Mac OS X 10_15_7)",
                "newer": "(Macintosh; Intel Mac OS X 10.15; rv:109.0)",
            },
            "linux": {
                "generic": "(X11; Linux x86_64)",
                "ubuntu": "(X11; Ubuntu; Linux x86_64)",
                "chrome_os": "(X11; CrOS x86_64 14541.0.0)",
            },
        }

        self.mobile_platforms = {
            "android": {
                "samsung": "(Linux; Android 13; SM-S901B)",
                "pixel": "(Linux; Android 12; Pixel 6)",
                "oneplus": "(Linux; Android 13; OnePlus 9 Pro)",
                "xiaomi": "(Linux; Android 12; M2102J20SG)",
            },
            "ios": {
                "iphone": "(iPhone; CPU iPhone OS 16_5 like Mac OS X)",
                "ipad": "(iPad; CPU OS 16_5 like Mac OS X)",
            },
        }

        # Browser Combinations
        self.browser_combinations = {
            1: [["chrome"], ["firefox"], ["safari"], ["edge"]],
            2: [["gecko", "firefox"], ["chrome", "safari"], ["webkit", "safari"]],
            3: [["chrome", "safari", "edge"], ["webkit", "chrome", "safari"]],
        }

        # Rendering Engines with versions
        self.rendering_engines = {
            "chrome_webkit": "AppleWebKit/537.36",
            "safari_webkit": "AppleWebKit/605.1.15",
            "gecko": [  # Added Gecko versions
                "Gecko/20100101",
                "Gecko/20100101",  # Firefox usually uses this constant version
                "Gecko/2010010",
            ],
        }

        # Browser Versions
        self.chrome_versions = [
            "Chrome/119.0.6045.199",
            "Chrome/118.0.5993.117",
            "Chrome/117.0.5938.149",
            "Chrome/116.0.5845.187",
            "Chrome/115.0.5790.171",
        ]

        self.edge_versions = [
            "Edg/119.0.2151.97",
            "Edg/118.0.2088.76",
            "Edg/117.0.2045.47",
            "Edg/116.0.1938.81",
            "Edg/115.0.1901.203",
        ]

        self.safari_versions = [
            "Safari/537.36",  # For Chrome-based
            "Safari/605.1.15",
            "Safari/604.1",
            "Safari/602.1",
            "Safari/601.5.17",
        ]

        # Added Firefox versions
        self.firefox_versions = [
            "Firefox/119.0",
            "Firefox/118.0.2",
            "Firefox/117.0.1",
            "Firefox/116.0",
            "Firefox/115.0.3",
            "Firefox/114.0.2",
            "Firefox/113.0.1",
            "Firefox/112.0",
            "Firefox/111.0.1",
            "Firefox/110.0",
        ]

    def get_browser_stack(self, num_browsers: int = 1) -> List[str]:
        """
        Get a valid combination of browser versions.

        How it works:
        1. Check if the number of browsers is supported.
        2. Randomly choose a combination of browsers.
        3. Iterate through the combination and add browser versions.
        4. Return the browser stack.

        Args:
            num_browsers: Number of browser specifications (1-3)

        Returns:
            List[str]: A list of browser versions.
        """
        if num_browsers not in self.browser_combinations:
            raise ValueError(f"Unsupported number of browsers: {num_browsers}")

        combination = random.choice(self.browser_combinations[num_browsers])
        browser_stack = []

        for browser in combination:
            if browser == "chrome":
                browser_stack.append(random.choice(self.chrome_versions))
            elif browser == "firefox":
                browser_stack.append(random.choice(self.firefox_versions))
            elif browser == "safari":
                browser_stack.append(random.choice(self.safari_versions))
            elif browser == "edge":
                browser_stack.append(random.choice(self.edge_versions))
            elif browser == "gecko":
                browser_stack.append(random.choice(self.rendering_engines["gecko"]))
            elif browser == "webkit":
                browser_stack.append(self.rendering_engines["chrome_webkit"])

        return browser_stack

    def generate(
        self,
        device_type: Optional[Literal["desktop", "mobile"]] = None,
        os_type: Optional[str] = None,
        device_brand: Optional[str] = None,
        browser_type: Optional[Literal["chrome", "edge", "safari", "firefox"]] = None,
        num_browsers: int = 3,
    ) -> str:
        """
        Generate a random user agent with specified constraints.

        Args:
            device_type: 'desktop' or 'mobile'
            os_type: 'windows', 'macos', 'linux', 'android', 'ios'
            device_brand: Specific device brand
            browser_type: 'chrome', 'edge', 'safari', or 'firefox'
            num_browsers: Number of browser specifications (1-3)
        """
        # Get platform string
        platform = self.get_random_platform(device_type, os_type, device_brand)

        # Start with Mozilla
        components = ["Mozilla/5.0", platform]

        # Add browser stack
        browser_stack = self.get_browser_stack(num_browsers)

        # Add appropriate legacy token based on browser stack
        if "Firefox" in str(browser_stack) or browser_type == "firefox":
            components.append(random.choice(self.rendering_engines["gecko"]))
        elif "Chrome" in str(browser_stack) or "Safari" in str(browser_stack) or browser_type == "chrome":
            components.append(self.rendering_engines["chrome_webkit"])
            components.append("(KHTML, like Gecko)")
        elif "Edge" in str(browser_stack) or browser_type == "edge":
            components.append(self.rendering_engines["safari_webkit"])
            components.append("(KHTML, like Gecko)")
        elif "Safari" in str(browser_stack) or browser_type == "safari":
            components.append(self.rendering_engines["chrome_webkit"])
            components.append("(KHTML, like Gecko)")

        # Add browser versions
        components.extend(browser_stack)

        return " ".join(components)

    def generate_with_client_hints(self, **kwargs) -> Tuple[str, str]:
        """Generate both user agent and matching client hints"""
        user_agent = self.generate(**kwargs)
        client_hints = self.generate_client_hints(user_agent)
        return user_agent, client_hints

    def get_random_platform(self, device_type, os_type, device_brand):
        """Helper method to get random platform based on constraints"""
        platforms = (
            self.desktop_platforms
            if device_type == "desktop"
            else self.mobile_platforms
            if device_type == "mobile"
            else {**self.desktop_platforms, **self.mobile_platforms}
        )

        if os_type:
            for platform_group in [self.desktop_platforms, self.mobile_platforms]:
                if os_type in platform_group:
                    platforms = {os_type: platform_group[os_type]}
                    break

        os_key = random.choice(list(platforms.keys()))
        if device_brand and device_brand in platforms[os_key]:
            return platforms[os_key][device_brand]
        return random.choice(list(platforms[os_key].values()))

    def parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """Parse a user agent string to extract browser and version information"""
        browsers = {
            "chrome": r"Chrome/(\d+)",
            "edge": r"Edg/(\d+)",
            "safari": r"Version/(\d+)",
            "firefox": r"Firefox/(\d+)",
        }

        result = {}
        for browser, pattern in browsers.items():
            match = re.search(pattern, user_agent)
            if match:
                result[browser] = match.group(1)

        return result

    def generate_client_hints(self, user_agent: str) -> str:
        """Generate Sec-CH-UA header value based on user agent string"""
        browsers = self.parse_user_agent(user_agent)

        # Client hints components
        hints = []

        # Handle different browser combinations
        if "chrome" in browsers:
            hints.append(f'"Chromium";v="{browsers["chrome"]}"')
            hints.append('"Not_A Brand";v="8"')

            if "edge" in browsers:
                hints.append(f'"Microsoft Edge";v="{browsers["edge"]}"')
            else:
                hints.append(f'"Google Chrome";v="{browsers["chrome"]}"')

        elif "firefox" in browsers:
            # Firefox doesn't typically send Sec-CH-UA
            return '""'

        elif "safari" in browsers:
            # Safari's format for client hints
            hints.append(f'"Safari";v="{browsers["safari"]}"')
            hints.append('"Not_A Brand";v="8"')

        return ", ".join(hints)


# Example usage:
if __name__ == "__main__":
    
    # Usage example:
    generator = ValidUAGenerator()
    ua = generator.generate()
    print(ua)
    
    generator = OnlineUAGenerator()
    ua = generator.generate()
    print(ua)

