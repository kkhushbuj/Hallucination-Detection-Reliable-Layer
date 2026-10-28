from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from graph import build_graph

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
async def serve_home():
    return FileResponse("static/index.html")


@app.post("/api/verify")
def verify_question(req: QuestionRequest):
    trust_graph = build_graph()
    result = trust_graph.invoke({"question": req.question})
    return result["verification_result"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
