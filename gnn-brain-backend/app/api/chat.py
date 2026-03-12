from fastapi import APIRouter
from app.graph.brain import bot_engine

router = APIRouter()

from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    node: str | None = None

@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    return bot_engine.chat(request.node, request.query)

# --- legacy simple in-memory message store ---
MESSAGES = {}

@router.get("/messages")
def get_messages(nodeId: str):
    return {"messages": MESSAGES.get(nodeId, [])}

@router.post("/messages")
def post_message(payload: dict):
    node_id = payload["nodeId"]
    text = payload["text"]

    MESSAGES.setdefault(node_id, []).append({"text": text, "sender": "user"})

    # Let the chatbot brain generate a response
    bot_text = bot_engine.generate_response(node_id, text)

    MESSAGES[node_id].append({"text": bot_text, "sender": "bot"})

    return {"message": {"text": bot_text, "sender": "bot"}}
