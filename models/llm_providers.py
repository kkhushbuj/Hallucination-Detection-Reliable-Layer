"""Single entry point for calling every LLM provider the pipeline uses."""

import os
import re

import openai
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_INSTRUCTION = (
    "If the user asks about something that does not exist (a fake study, "
    "fake person, fake event, fake citation, etc.), clearly state that it "
    "does not exist and STOP there. Do not invent hypothetical details, "
    "fake findings, fake quotes, or fictional elaboration — even if you "
    "label it as imaginative or hypothetical."
)

OPENROUTER_URL = "https://openrouter.ai/api/v1"

# OpenRouter reserves credit for the largest possible reply when no limit is set, which fails
# on small balances. Every OpenRouter role here returns a short verdict, so cap it.
OPENROUTER_ARGS = {"max_tokens": 512}

# Providers that speak the OpenAI chat API: name -> (base URL, env var holding the key, extra request args).
# Each OpenRouter provider has its own key so the roles keep separate quotas.
OPENAI_COMPATIBLE = {
    "openai": (None, "OPENAI_API_KEY", {}),
    "openrouter_mistral": (OPENROUTER_URL, "OPENROUTER_MISTRAL_API_KEY", OPENROUTER_ARGS),
    "openrouter_llama": (OPENROUTER_URL, "OPENROUTER_API_KEY", OPENROUTER_ARGS),
    "openrouter_checker": (OPENROUTER_URL, "OPENROUTER_CHECKER_API_KEY", OPENROUTER_ARGS),
    "openrouter_grader": (OPENROUTER_URL, "OPENROUTER_GRADER_API_KEY", OPENROUTER_ARGS),
    # Nemotron reasons before it answers, so it needs room beyond the one-word verdict.
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", {"max_tokens": 2048}),
}

_clients: dict = {}


def _client_for(provider: str):
    """Build each API client on first use, so a missing key only fails the role that needs it."""
    if provider not in _clients:
        if provider == "groq":
            _clients[provider] = Groq(api_key=os.getenv("GROQ_API_KEY"))
        else:
            base_url, key_env, _ = OPENAI_COMPATIBLE[provider]
            _clients[provider] = openai.OpenAI(api_key=os.getenv(key_env), base_url=base_url)
    return _clients[provider]


def _strip_thinking(text: str | None) -> str:
    """Remove <think>...</think> blocks that some reasoning models include."""
    cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    return cleaned.strip()


def call_model(provider: str, model: str, question: str, temperature: float = 0.7) -> str:
    """Send one prompt to a provider and return the reply text with any thinking removed."""
    if provider != "groq" and provider not in OPENAI_COMPATIBLE:
        raise ValueError(f"Unknown provider: {provider}")

    extra_args = {"reasoning_effort": "low"} if provider == "groq" else OPENAI_COMPATIBLE[provider][2]
    response = _client_for(provider).chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": question},
        ],
        temperature=temperature,
        **extra_args,
    )
    return _strip_thinking(response.choices[0].message.content)
