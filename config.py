import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

USE_WEB_SEARCH = True
USE_TIE_BREAKER = True

TIE_BREAKER_MODEL = "claude-haiku-4-5-20251001"
TIE_BREAKER_PENALTY = 10

VOTING_MODELS = [
    {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    {"provider": "gemini", "model": "gemini-3.5-flash"},
    {"provider": "mistral", "model": "mistral-small-latest"},
]

CONSISTENCY_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}
CONSISTENCY_RUNS = 4
CONSISTENCY_TEMPERATURE = 0.9

TEMPERATURES = [0.9, 0.9, 0.9]

HIGH_CONFIDENCE_THRESHOLD = 0.80
MEDIUM_CONFIDENCE_THRESHOLD = 0.75