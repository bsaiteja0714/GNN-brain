from app.graph.data import RAW_NODES
from app.graph.graph_builder import build_nx_graph
from app.graph.retriever import GraphRetriever, FAISSRetriever
from app.ai.embedder import embed_nodes
from app.ai.llm import generate_answer

class ChatbotEngine:
    def __init__(self):
        # 1. Build Graph
        self.G, self.node_metadata = build_nx_graph(RAW_NODES)
        self.retriever = GraphRetriever(self.G, self.node_metadata)
        
        # 2. Populate embeddings in the dicts
        embed_nodes(RAW_NODES)
            
        # 3. Setup Vector Searcher
        self.embedder = FAISSRetriever(RAW_NODES)

    def chat(self, sender_node_label_or_id: str | None, message: str):
        sender_node_id = None
        selected_node_context = ""
        
        if sender_node_label_or_id:
            sender_node_id = sender_node_label_or_id
            if sender_node_id not in self.node_metadata:
                # Try to resolve by label
                for nid, meta in self.node_metadata.items():
                    if meta.get("label") == sender_node_label_or_id:
                        sender_node_id = nid
                        break
                        
            if sender_node_id not in self.node_metadata:
                return {
                    "answer": f"I couldn't find your node '{sender_node_label_or_id}' in the graph. But I heard: '{message}'",
                    "sources": []
                }
            
            # Build selected node context
            meta = self.node_metadata[sender_node_id]
            label = meta.get("label", sender_node_id)
            role = meta.get("type", "Unknown")
            selected_node_context = f"Selected Node:\n{label} ({role})\n\n"

        # 1. Semantic search to find relevant nodes
        search_results = self.embedder.search_graph(message, top_k=2)
        initial_node_ids = [res["node_id"] for res in search_results]
        
        # 2. Expand search using graph connectivity
        relevant_node_ids = self.retriever.get_expanded_neighbors(initial_node_ids)
        
        # 3. Extract node data
        relevant_nodes_info = []
        for nid in relevant_node_ids:
            meta = self.node_metadata[nid]
            label = meta.get("label", nid)
            role = meta.get("type", "Unknown") # 'type' replaced 'role'
            relevant_nodes_info.append(f"{label} ({role})")
            
        # 4. Graph paths to those nodes
        paths_context = []
        if sender_node_id:
            paths_context = self.retriever.get_shortest_path_context(sender_node_id, relevant_node_ids)
        
        # 5. Construct answer
        sender_label = self.node_metadata.get(sender_node_id, {}).get("label", sender_node_id) if sender_node_id else ""
        
        answer = generate_answer(
            sender_label,
            relevant_nodes_info,
            paths_context,
            message,
            selected_node_context,
            node_metadata=self.node_metadata,
            sender_node_id=sender_node_id,
        )
        
        return {
            "answer": answer,
            "sources": relevant_node_ids
        }
        
    def generate_response(self, sender_node_id: str, message: str):
        # Legacy method for backwards compatibility
        return self.chat(sender_node_id, message)["answer"]

bot_engine = ChatbotEngine()
