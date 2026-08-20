import os
import re
from dotenv import load_dotenv
import openai
from groq import Groq
from mistralai.client import Mistral
from google import genai

load_dotenv()

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = (
    "If the user asks about something that does not exist (a fake study, "
    "fake person, fake event, fake citation, etc.), clearly state that it "
    "does not exist and STOP there. Do not invent hypothetical details, "
    "fake findings, fake quotes, or fictional elaboration — even if you "
    "label it as imaginative or hypothetical."
)


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that some reasoning models include."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()


def call_model(provider: str, model: str, question: str, temperature: float = 0.7) -> str:
    if provider == "openai":
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
        )
        return _strip_thinking(response.choices[0].message.content)

    elif provider == "groq":
        response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
        )
        return _strip_thinking(response.choices[0].message.content)

    elif provider == "mistral":
        response = mistral_client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
        )
        return _strip_thinking(response.choices[0].message.content)

    elif provider == "gemini":
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nQuestion: {question}"
        response = gemini_client.models.generate_content(
            model=model,
            contents=full_prompt,
        )
        return _strip_thinking(response.text)

    else:
        raise ValueError(f"Unknown provider: {provider}")