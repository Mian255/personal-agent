"""
Free Web Search & Content Tool
Uses DuckDuckGo Search and requests without requiring paid API keys.
"""

from typing import List, Dict, Any
import requests

class WebSearchTool:
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Searches the live web and returns titles, snippets, and links."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", "")
                    }
                    for r in results
                ]
        except Exception as e:
            return [{"title": "Search Error", "snippet": f"Could not perform search: {e}", "url": ""}]

    def fetch_url(self, url: str) -> str:
        """Fetches and extracts plain text from a URL."""
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            resp.raise_for_status()
            text = resp.text[:3000]
            return text
        except Exception as e:
            return f"Error fetching {url}: {e}"
