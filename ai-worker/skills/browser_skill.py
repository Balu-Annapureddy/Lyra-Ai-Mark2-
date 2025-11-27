"""
Browser Skill - Open URLs and Search
"""

from typing import Dict, Any
import webbrowser
import logging
from urllib.parse import quote_plus

from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class BrowserSkill(BaseSkill):
    """Skill for browser operations"""
    
    @property
    def name(self) -> str:
        return "browser"
    
    @property
    def description(self) -> str:
        return "Open URLs or perform web searches"
    
    @property
    def required_ram_mb(self) -> int:
        return 50  # Very lightweight
    
    @property
    def requires_internet(self) -> bool:
        return True
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute browser operation
        
        Params:
            action: "open" or "search"
            url: URL to open (for open action)
            query: Search query (for search action)
            engine: Search engine (default: "google")
        
        Returns:
            Result with success status
        """
        try:
            action = params.get("action", "open")
            
            if action == "open":
                url = params.get("url", "")
                if not url:
                    return self._error_response("No URL provided")
                
                # Add https:// if no protocol specified
                if not url.startswith(("http://", "https://")):
                    url = f"https://{url}"
                
                webbrowser.open(url)
                logger.info(f"Opened URL: {url}")
                
                return self._success_response({
                    "action": "open",
                    "url": url
                })
            
            elif action == "search":
                query = params.get("query", "")
                if not query:
                    return self._error_response("No search query provided")
                
                engine = params.get("engine", "google")
                
                # Search engine URLs
                search_urls = {
                    "google": f"https://www.google.com/search?q={quote_plus(query)}",
                    "bing": f"https://www.bing.com/search?q={quote_plus(query)}",
                    "duckduckgo": f"https://duckduckgo.com/?q={quote_plus(query)}",
                    "youtube": f"https://www.youtube.com/results?search_query={quote_plus(query)}"
                }
                
                url = search_urls.get(engine.lower())
                if not url:
                    return self._error_response(f"Unknown search engine: {engine}")
                
                webbrowser.open(url)
                logger.info(f"Searched '{query}' on {engine}")
                
                return self._success_response({
                    "action": "search",
                    "query": query,
                    "engine": engine,
                    "url": url
                })
            
            else:
                return self._error_response(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"Browser operation failed: {e}")
            return self._error_response(str(e))
