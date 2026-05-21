"""
Small wrapper for the local LLM client.
Uses Ollama's OpenAI-compatible endpoint.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("OLLAMA_API_KEY", "ollama")  # required by SDK, ignored by Ollama
    return OpenAI(base_url=base_url, api_key=api_key)
