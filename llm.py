"""
Universal LLM Provider Integration
Supports ANY OpenAI-compatible API endpoint or dedicated providers:
- Custom / Generic (OpenAI, DeepSeek, Together, Mistral, LocalAI, vLLM, LM Studio)
- Groq (Ultra-fast)
- OpenRouter (Free & Paid models)
- Google Gemini (Gemini API)
- Ollama (Local offline)
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
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "custom")).lower()
        
        # 1. Check for Universal / Custom OpenAI-compatible configuration
        custom_base_url = base_url or os.getenv("LLM_BASE_URL")
        custom_api_key = api_key or os.getenv("LLM_API_KEY")
        custom_model = model or os.getenv("LLM_MODEL")

        if self.provider == "groq":
            self.base_url = "https://api.groq.com/openai/v1"
            self.api_key = api_key or os.getenv("GROQ_API_KEY") or custom_api_key or ""
            self.model = model or os.getenv("GROQ_MODEL") or custom_model or "openai/gpt-oss-120b"
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        elif self.provider == "openrouter":
            self.base_url = "https://openrouter.ai/api/v1"
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or custom_api_key or ""
            self.model = model or os.getenv("OPENROUTER_MODEL") or custom_model or "meta-llama/llama-3.3-70b-instruct:free"
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/Mian255/personal-agent",
                    "X-Title": "Bob Personal AI Agent",
                }
            )

        elif self.provider == "gemini":
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            self.api_key = api_key or os.getenv("GEMINI_API_KEY") or custom_api_key or ""
            self.model = model or os.getenv("GEMINI_MODEL") or custom_model or "gemini-2.0-flash"
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        elif self.provider == "ollama":
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            self.api_key = "ollama"
            self.model = model or os.getenv("OLLAMA_MODEL") or custom_model or "llama3.2"
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        elif self.provider == "deepseek":
            self.base_url = "https://api.deepseek.com/v1"
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or custom_api_key or ""
            self.model = model or os.getenv("DEEPSEEK_MODEL") or custom_model or "deepseek-chat"
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        elif self.provider == "openai":
            self.base_url = "https://api.openai.com/v1"
            self.api_key = api_key or os.getenv("OPENAI_API_KEY") or custom_api_key or ""
            self.model = model or os.getenv("OPENAI_MODEL") or custom_model or "gpt-4o-mini"
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        else:
            # Universal Custom OpenAI-Compatible Provider
            self.base_url = custom_base_url or "https://api.openai.com/v1"
            self.api_key = custom_api_key or os.getenv("OPENAI_API_KEY", "")
            self.model = custom_model or "gpt-4o-mini"
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> Any:
        """Sends chat messages and returns the assistant's message object."""
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
