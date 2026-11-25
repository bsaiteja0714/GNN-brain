from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import networkx as nx

from app.api.assistant import router as assistant_router
from app.api.chat import router as chat_router
from app.graph.brain import bot_engine

app = FastAPI(title="GNN Brain")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Provider-Key"],
)
app.include_router(chat_router)
app.include_router(assistant_router)


@app.get("/")
def root():
    return {"message": "GNN Brain backend is alive"}


@app.get("/graph")
def get_graph():
    return bot_engine.graph_data()


@app.get("/path/{node_id}")
def get_path(node_id: str):
    start = bot_engine.resolve(node_id)
    if start is None:
        raise HTTPException(404, detail="School node not found.")
    return {"path": nx.shortest_path(bot_engine.G, start, "director")}
