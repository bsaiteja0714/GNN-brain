import networkx as nx
import faiss
import numpy as np
from app.ai.embedder import embed_text

class FAISSRetriever:
    def __init__(self, nodes: list[dict]):
        """Build FAISS index from node embeddings."""
        self.node_metadata = {node["node_id"]: node for node in nodes}
        self.node_ids = []
        embeddings = []
        
        for node in nodes:
            if node.get("embedding"):
                embeddings.append(node["embedding"])
                self.node_ids.append(node["node_id"])
                
        if embeddings:
            embeddings_np = np.array(embeddings, dtype=np.float32)
            dimension = embeddings_np.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_np)
        else:
            self.index = None

    def search_graph(self, query: str, top_k: int = 2) -> list[dict]:
        """Retrieve top K nodes for a query and return node IDs and text."""
        if not self.index:
            return []
            
        query_embedding = np.array([embed_text(query)], dtype=np.float32)
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.node_ids):
                node_id = self.node_ids[idx]
                node_data = self.node_metadata.get(node_id, {})
                results.append({
                    "node_id": node_id,
                    "text": node_data.get("text", "")
                })
        return results

class GraphRetriever:
    def __init__(self, G: nx.DiGraph, node_metadata: dict):
        self.G = G
        self.node_metadata = node_metadata

    def get_expanded_neighbors(self, node_ids: list) -> list:
        """Expand node list using graph neighbors (degree 1)"""
        expanded_ids = set(node_ids)
        undirected_G = self.G.to_undirected()
        
        for nid in node_ids:
            if undirected_G.has_node(nid):
                for neighbor in undirected_G.neighbors(nid):
                    expanded_ids.add(neighbor)
                    
        return list(expanded_ids)

    def get_shortest_path_context(self, source_id: str, target_ids: list):
        paths_context = []
        for target_id in target_ids:
            if source_id == target_id:
                paths_context.append(f"The topic is directly related to you ({source_id}).")
                continue
                
            try:
                undirected_G = self.G.to_undirected()
                path = nx.shortest_path(undirected_G, source=source_id, target=target_id)
                path_labels = [self.node_metadata[pid].get("label", pid) for pid in path]
                paths_context.append(f"Connection to {self.node_metadata[target_id].get('label', target_id)}: " + " -> ".join(path_labels))
            except nx.NetworkXNoPath:
                paths_context.append(f"No direct path to {self.node_metadata[target_id].get('label', target_id)}.")
        return paths_context
