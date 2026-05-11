"""
main.py
───────
FastAPI backend for the TailorTalk Drive Agent.

Endpoints:
  POST /chat   — Send a message, receive agent reply
  GET  /health — Health check
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import run_agent

# ──────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────

app = FastAPI(
    title="TailorTalk Drive Agent API",
    description="Conversational AI agent for Google Drive file discovery",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Streamlit can call from any origin locally
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str        # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    status: str = "ok"


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TailorTalk Drive Agent"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts user message + conversation history.
    Returns agent reply.
    """
    try:
        history = [msg.model_dump() for msg in request.history]
        reply = run_agent(
            user_message=request.message,
            history=history,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
