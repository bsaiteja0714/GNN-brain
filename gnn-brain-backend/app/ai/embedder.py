from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str):
    """Embeds a single string and returns it as a numpy array."""
    return model.encode(text)

def embed_nodes(nodes: list[dict]):
    """Iterates through graph nodes, generates embeddings for their text, and stores them inside the node."""
    texts = [node.get("text", "") for node in nodes]
    if not texts:
        return
        
    embeddings = model.encode(texts)
    
    for i, node in enumerate(nodes):
        node["embedding"] = embeddings[i].tolist()

