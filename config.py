import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Dedicated key for the tie-breaker so it doesn't share quota with the main judge
# panel's Groq calls (VOTING_MODELS). Falls back to GROQ_API_KEY if not set.
GROQ_TIEBREAKER_API_KEY = os.getenv("GROQ_TIEBREAKER_API_KEY", GROQ_API_KEY)

USE_WEB_SEARCH = True
USE_TIE_BREAKER = True

# Llama 3.3 70B via Groq - a different model family from the OpenAI generator, on its
# own dedicated key/quota (GROQ_TIEBREAKER_API_KEY) rather than sharing the panel's.
TIE_BREAKER_MODEL = {"provider": "groq", "model": "llama-3.3-70b-versatile"}
TIE_BREAKER_PENALTY = 10

VOTING_MODELS = [
    {"provider": "groq", "model": "qwen/qwen3.8-27b"},
    {"provider": "gemini", "model": "gemini-3.5-flash"},
    {"provider": "cohere", "model": "command-r-08-2024"},
]

CONSISTENCY_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}
CONSISTENCY_RUNS = 4
CONSISTENCY_TEMPERATURE = 0.9

TEMPERATURES = [0.9, 0.9, 0.9]

HIGH_CONFIDENCE_THRESHOLD = 0.80
MEDIUM_CONFIDENCE_THRESHOLD = 0.75