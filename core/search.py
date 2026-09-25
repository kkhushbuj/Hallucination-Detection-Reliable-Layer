import requests
import config

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def search_web(query: str, timeout: float = 10.0) -> str:
    """Run a Tavily web search and return a short plain-text summary of the top results.

    Raises on failure (missing key, network error, timeout) - callers are expected to
    catch and fall back to judging from the model's own knowledge only.
    """
    if not config.TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set")

    response = requests.post(
        TAVILY_SEARCH_URL,
        json={
            "api_key": config.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 3,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()

    lines = []
    if data.get("answer"):
        lines.append(f"Summary: {data['answer']}")
    for result in data.get("results", [])[:3]:
        title = result.get("title", "").strip()
        content = result.get("content", "").strip()
        if title or content:
            lines.append(f"- {title}: {content}")

    if not lines:
        raise RuntimeError("Tavily returned no usable results")

    return "\n".join(lines)
