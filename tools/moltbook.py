"""
Moltbook API Client
Official Base URL: https://www.moltbook.com/api/v1
Note: Always use 'www.moltbook.com' to avoid redirects stripping auth headers.
"""

import json
import os
from typing import Any, Dict, List, Optional
import requests

BASE_URL = "https://www.moltbook.com/api/v1"
CONFIG_FILE = os.path.expanduser("~/.config/moltbook/credentials.json")


class MoltbookClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_saved_key()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "MoltbookAssistantAgent/1.0",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _load_saved_key(self) -> Optional[str]:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("api_key")
            except Exception:
                return None
        return os.getenv("MOLTBOOK_API_KEY")

    def save_credentials(self, api_key: str, agent_name: str, claim_url: Optional[str] = None):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        self.api_key = api_key
        self.headers["Authorization"] = f"Bearer {api_key}"
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "api_key": api_key,
                "agent_name": agent_name,
                "claim_url": claim_url
            }, f, indent=2)

    def register_agent(self, name: str, description: str) -> Dict[str, Any]:
        """
        Registers a new AI agent on Moltbook.
        Returns: { 'api_key': '...', 'claim_url': '...', ... }
        """
        url = f"{BASE_URL}/agents/register"
        payload = {
            "name": name,
            "description": description
        }
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        data = response.json()
        
        api_key = data.get("api_key")
        claim_url = data.get("claim_url")
        if api_key:
            self.save_credentials(api_key=api_key, agent_name=name, claim_url=claim_url)
        return data

    def get_me(self) -> Dict[str, Any]:
        """Gets current agent profile and verification status."""
        url = f"{BASE_URL}/agents/me"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_feed(self, sort: str = "hot", limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches the Moltbook feed.
        sort options: 'hot', 'new', 'top'
        """
        url = f"{BASE_URL}/feed"
        params = {"sort": sort, "limit": limit}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        res_data = response.json()
        if isinstance(res_data, list):
            return res_data
        return res_data.get("posts", res_data.get("data", []))

    def create_post(self, title: str, content: str, submolt: Optional[str] = None) -> Dict[str, Any]:
        """Creates a post on Moltbook."""
        url = f"{BASE_URL}/posts"
        payload = {"title": title, "content": content}
        if submolt:
            payload["submolt"] = submolt
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def upvote_post(self, post_id: str) -> Dict[str, Any]:
        """Upvotes a post by ID."""
        url = f"{BASE_URL}/posts/{post_id}/upvote"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def comment_on_post(self, post_id: str, content: str) -> Dict[str, Any]:
        """Adds a comment to a post."""
        url = f"{BASE_URL}/posts/{post_id}/comments"
        payload = {"content": content}
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
