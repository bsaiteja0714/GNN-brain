from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph.data import RAW_NODES
from app.api.chat import router as chat_router


app = FastAPI()

# Allow frontend (Vite) to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "GNN Brain backend is alive 🧠"}

@app.get("/graph")
def get_graph():
    nodes = []
    links = []
    for node in RAW_NODES:
        nodes.append({
            "id": node["node_id"],
            "label": node.get("label", node["node_id"]),
            "role": node.get("type", "Other"), 
            "section": node.get("section"),
            "importance": node.get("importance", 1),
            "text": node.get("text", "")
        })
        for target in node.get("connections", []):
            links.append({"source": node["node_id"], "target": target})
            
    return {"nodes": nodes, "links": links}

@app.get("/path/{node_id}")
def get_path(node_id: str):
    return {"path": []}

