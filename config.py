import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

USE_WEB_SEARCH = True
USE_TIE_BREAKER = True

# Each job is done by a model from a different lab. Provider names map to an API key in
# models/llm_providers.py (the OpenRouter providers each use their own key).

# Writes the 3 candidate answers (OpenAI).
CONSISTENCY_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}

# The 3 judges: Alibaba Qwen, Mistral and Meta Llama.
VOTING_MODELS = [
    {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    {"provider": "openrouter_mistral", "model": "mistralai/mistral-medium-3-5"},
    {"provider": "openrouter_llama", "model": "meta-llama/llama-3.3-70b-instruct"},
]

# Decides whether two generated answers reach the same conclusion (Google Gemini).
AGREEMENT_MODEL = {"provider": "gemini", "model": "gemini-3.5-flash-lite"}

# Independent second opinion on the winning answer (NVIDIA Nemotron).
TIE_BREAKER_MODEL = {"provider": "nvidia", "model": "nvidia/nemotron-3.5-lightning-30b-a3b"}
TIE_BREAKER_PENALTY = 10

CONSISTENCY_TEMPERATURE = 0.9

TEMPERATURES = [0.9, 0.9, 0.9]

HIGH_CONFIDENCE_THRESHOLD = 0.80
MEDIUM_CONFIDENCE_THRESHOLD = 0.75
