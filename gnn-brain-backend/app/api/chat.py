from collections import defaultdict
from threading import Lock

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.assistant import Connection, ProviderKey, plan_conversation, school_answer
from app.graph.brain import bot_engine
from app.graph.conversation import classify, compact, social_reply, without_lead_in
from app.graph.workspace import Workspace

router = APIRouter()


class ChatTurn(BaseModel):
    question: str = Field(max_length=1000)
    answer: str = Field(max_length=8000)
    context: str | None = Field(default=None, max_length=1000)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    node: str | None = Field(default=None, max_length=120)
    previousQuestion: str | None = Field(default=None, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)
    graph: Workspace | None = None
    provider: Connection | None = None


def custom_chat(request, query, previous, *, institutional=False):
    graph = request.graph
    node = next((item for item in graph.nodes if item.id == request.node), None)
    intent = classify(query, previous_graph=bool(previous))
    social = social_reply(intent, name=node.label if node else None, has_history=bool(request.history))
    if social:
        return bot_engine.result(social, "local", [])
    if node is None:
        return bot_engine.result("Select a node so I can answer questions about it.", "clarify", [])
    if not institutional and intent not in {"graph", "follow-up"} and compact(query) not in {"who are you", "tell me about yourself"}:
        return bot_engine.result("What would you like to know about this node or its connections?", "clarify", [])
    neighbors = {link.target for link in graph.links if link.source == node.id}
    neighbors.update(link.source for link in graph.links if link.target == node.id)
    labels = [item.label for item in graph.nodes if item.id in neighbors]
    connections = "Connected to " + ", ".join(labels) + "." if labels else "This node has no connections."
    return bot_engine.result("\n\n".join(filter(None, (node.text, connections))), "local", [], context=previous if intent == "follow-up" else query)


@router.post("/chat")
def chat_endpoint(request: ChatRequest, key: ProviderKey = None):
    query = request.query.strip()
    if not query:
        raise HTTPException(422, detail="Enter a question.")
    prior = next((turn for turn in reversed(request.history) if turn.context), None)
    previous = prior.context if prior else request.previousQuestion
    if request.provider and key:
        history = [item for turn in request.history[-4:] for item in (
            {"role": "user", "content": turn.question},
            {"role": "assistant", "content": turn.answer},
        )]
        if previous and not history:
            history = [{"role": "user", "content": previous}]
        plan = plan_conversation(request.provider, key, query, history, request.node, request.graph)
        if plan.action in {"reply", "clarify"}:
            return bot_engine.result(plan.answer, "local" if plan.action == "reply" else "clarify", [])
        if request.graph is None:
            return school_answer(request.provider, key, query, history, plan, request.node)
        return custom_chat(request, plan.query or query, previous, institutional=True)
    if prior and compact(without_lead_in(query)) in {"could you repeat that", "can you repeat that", "say that again"}:
        return bot_engine.result(prior.answer, "local", [], context=previous)
    if request.graph is not None:
        return custom_chat(request, without_lead_in(query), previous)
    try:
        return bot_engine.chat(request.node, query, previous, bool(request.history))
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
