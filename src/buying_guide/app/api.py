"""
Optional HTTP API using FastAPI.

Run with: uvicorn buying_guide.app.api:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from .session import run_agentic_session


class RecommendRequest(BaseModel):
    query: str
    top_k: int = 5


app = FastAPI(title="Headphone Buying Guide API")


@app.post("/recommend")
def recommend(req: RecommendRequest):
    """
    POST /recommend
    Body: { "query": "...", "top_k": 5 }
    """
    result = run_agentic_session(req.query, top_k=req.top_k)
    return result
