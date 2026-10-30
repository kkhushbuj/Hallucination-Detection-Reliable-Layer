import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from graph import build_graph

app = FastAPI()

# Public traffic spends LLM quota, so cap each visitor and the total number of runs in flight.
RATE_LIMIT = 6
RATE_WINDOW = 60
MAX_CONCURRENT = 8
_hits = defaultdict(deque)
_hits_lock = threading.Lock()
_slots = threading.BoundedSemaphore(MAX_CONCURRENT)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else request.client.host


def _within_rate_limit(ip: str) -> bool:
    now = time.monotonic()
    with _hits_lock:
        recent = _hits[ip]
        while recent and now - recent[0] > RATE_WINDOW:
            recent.popleft()
        if len(recent) >= RATE_LIMIT:
            return False
        recent.append(now)
        return True

app.mount("/static", StaticFiles(directory="static"), name="static")


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
async def serve_home():
    # no-cache makes the browser recheck the page on every load, so edits show up without a hard refresh.
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/verify")
def verify_question(req: QuestionRequest, request: Request):
    if not _within_rate_limit(_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute and try again.")
    if not _slots.acquire(timeout=30):
        raise HTTPException(status_code=503, detail="The server is busy. Please try again shortly.")
    try:
        trust_graph = build_graph()
        result = trust_graph.invoke({"question": req.question})
        return result["verification_result"]
    finally:
        _slots.release()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
