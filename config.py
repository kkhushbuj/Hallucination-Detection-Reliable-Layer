import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

USE_WEB_SEARCH = True
USE_TIE_BREAKER = True

# Runs via Groq, sharing the same GROQ_API_KEY/quota as VOTING_MODELS - no separate key needed.
TIE_BREAKER_MODEL = {"provider": "groq", "model": "openai/gpt-oss-20b"}
TIE_BREAKER_PENALTY = 10

VOTING_MODELS = [
    {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    {"provider": "gemini", "model": "gemini-3.5-flash"},
    {"provider": "mistral", "model": "mistral-small-latest"},
]

# Mistral's free tier has a tight rate limit that 3 calls per question (one per
# generated answer) trips reliably. Cap how many of those 3 calls actually go to
# Mistral per question; the rest simply skip it rather than show a rate-limit warning.
MISTRAL_MAX_CALLS_PER_QUESTION = 1

CONSISTENCY_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}
CONSISTENCY_RUNS = 4
CONSISTENCY_TEMPERATURE = 0.9

TEMPERATURES = [0.9, 0.9, 0.9]

HIGH_CONFIDENCE_THRESHOLD = 0.80
MEDIUM_CONFIDENCE_THRESHOLD = 0.75