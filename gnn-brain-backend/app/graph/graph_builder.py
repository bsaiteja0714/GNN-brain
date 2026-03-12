import networkx as nx

def build_nx_graph(raw_nodes: list):
    G = nx.DiGraph()
    node_metadata = {}
    
    for node in raw_nodes:
        n_id = node.get("node_id")
        G.add_node(n_id, **node)
        node_metadata[n_id] = node
        
    for node in raw_nodes:
        src = node.get("node_id")
        for target in node.get("connections", []):
            G.add_edge(src, target)
            
    return G, node_metadata
