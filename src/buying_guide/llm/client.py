"""
Small wrapper for the OpenAI client.
Automatically loads .env so environment variables are set.
"""

import os
from functools import lru_cache

import openai
from dotenv import load_dotenv

# Load .env automatically
load_dotenv()


@lru_cache(maxsize=1)
def get_openai_client() -> openai.OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Create a .env file with it.")
    return openai.OpenAI()
