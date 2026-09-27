"""
LLM Provider Integration with Native Tool Calling
Supports:
1. Groq (openai/gpt-oss-120b, qwen3.8-27b)
2. OpenRouter (Free models)
3. Google Gemini (gemini-2.0-flash)
4. Ollama (Local)
"""

import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()
        
        if self.provider == "groq":
            self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
            self.model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.api_key
            )
        elif self.provider == "openrouter":
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
            self.model = model or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/Mian255/personal-agent",
                    "X-Title": "Personal AI Agent Hub",
                }
            )
        elif self.provider == "gemini":
            self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.client = OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=self.api_key
            )
        elif self.provider == "ollama":
            self.api_key = "ollama"
            self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
            self.client = OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key=self.api_key
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1200
    ) -> Any:
        """Sends chat messages and returns the assistant's response or tool calls."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message
