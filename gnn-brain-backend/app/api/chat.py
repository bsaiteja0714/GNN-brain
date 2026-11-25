from collections import defaultdict
from threading import Lock

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.graph.brain import bot_engine

router = APIRouter()


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    node: str | None = Field(default=None, max_length=120)
    previousQuestion: str | None = Field(default=None, max_length=1000)


@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(422, detail="Enter a question.")
    try:
        return bot_engine.chat(request.node, query, request.previousQuestion)
    except KeyError:
        raise HTTPException(404, detail="School node not found.") from None


class MessageRequest(BaseModel):
    nodeId: str
    text: str


MESSAGES = defaultdict(list)
message_lock = Lock()


@router.get("/messages")
def get_messages(nodeId: str):
    with message_lock:
        return {"messages": list(MESSAGES.get(nodeId, []))}


@router.post("/messages")
def post_message(payload: MessageRequest):
    if not payload.text.strip() or len(payload.text) > 1000 or len(payload.nodeId) > 120:
        raise HTTPException(422, detail="Enter a valid node and a question of up to 1000 characters.")
    answer = chat_endpoint(ChatRequest(node=payload.nodeId, query=payload.text))
    reply = {"text": answer["answer"], "sender": "bot"}
    with message_lock:
        MESSAGES[payload.nodeId].extend(({"text": payload.text, "sender": "user"}, reply))
    return {"message": reply}
