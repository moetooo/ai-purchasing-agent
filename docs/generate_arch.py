import matplotlib.pyplot as plt
import networkx as nx
import os

def generate():
    os.makedirs('docs', exist_ok=True)
    G = nx.DiGraph()
    
    nodes = [
        ("Streamlit UI", (2, 5)),
        ("FastAPI Backend", (2, 4)),
        ("LangGraph Agent", (2, 3)),
        ("Tool Layer", (1, 2)),
        ("Constraints Engine", (3, 2)),
        ("SQLite DB", (2, 1)),
        ("Mock PO API", (4, 4)),
        ("Post-Action Validator", (4, 3))
    ]
    
    for label, pos in nodes:
        G.add_node(label, pos=pos)
        
    edges = [
        ("Streamlit UI", "FastAPI Backend"),
        ("FastAPI Backend", "LangGraph Agent"),
        ("LangGraph Agent", "Tool Layer"),
        ("LangGraph Agent", "Constraints Engine"),
        ("Tool Layer", "SQLite DB"),
        ("Constraints Engine", "SQLite DB"),
        ("FastAPI Backend", "Mock PO API"),
        ("Mock PO API", "Post-Action Validator"),
        ("Post-Action Validator", "Streamlit UI")
    ]
    
    for u, v in edges:
        G.add_edge(u, v)
        
    pos = nx.get_node_attributes(G, 'pos')
    
    plt.figure(figsize=(12, 8))
    nx.draw_networkx(
        G, pos,
        with_labels=True,
        node_color='lightblue',
        node_size=6000,
        font_size=10,
        font_weight='bold',
        edge_color='gray',
        arrows=True,
        arrowsize=20
    )
    
    plt.title("AI Purchasing Agent Architecture", size=15)
    plt.savefig('docs/architecture.png', format='png', bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    generate()
