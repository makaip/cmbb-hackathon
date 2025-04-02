import json

class Node:
    id: int = None
    label: str = None
    def __init__(self,id,label):
        self.id = id
        self.label = label
class Edge:
    id: str = None
    source: Node = None
    target: Node = None
    label: str = None
    def __init__(self,source: Node, target: Node):
        self.source = source
        self.target = target
        self.label = source.label + "->" +  target.label
        self.id = str(source.id) + "->" + str(target.id)
    def to_dict(self):
        """Convert Edge to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source.id,
            "target": self.target.id,
            "label": self.label
        }

def export_edges_to_dict(nodes, edges):
    """
    Export nodes and edges to a JSON file.
    
    Args:
        nodes: List of Node objects or dictionary of Node objects
        edges: List of Edge objects
        file_path: Path to save the JSON file
    """
    
    # Convert nodes to list if it's a dictionary
    if isinstance(nodes, dict):
        nodes_list = list(nodes.values())
    else:
        nodes_list = nodes
    
    # Convert to dictionaries for JSON serialization
    nodes_data = [{"id": node.id, "label": node.label} for node in nodes_list]
    edges_data = [edge.to_dict() for edge in edges]
    
    data = {
        "nodes": nodes_data,
        "edges": edges_data
    }
    
    return data

def relationships_to_edges(relationships, nodes_dict=None):
    """
    Convert a list of Relationships to a list of Edges.
    
    Args:
        relationships: A list of dictionaries with 'gene_ids' and 'description'.
        nodes_dict: A dictionary mapping gene_ids to Node objects. If None, creates a new dictionary.
    
    Returns:
        A list of Edge objects representing the relationships.
    """
    edges = []
    if nodes_dict is None:
        nodes_dict = {}
    
    # First, ensure all genes have nodes
    for relationship in relationships:
        gene_ids = relationship['gene_ids']
        for gene_id in gene_ids:
            if gene_id not in nodes_dict:
                nodes_dict[gene_id] = Node(id=gene_id, label=gene_id)
    
    # Then create edges
    for relationship in relationships:
        gene_ids = relationship['gene_ids']
        for i in range(len(gene_ids) - 1):
            source_node = nodes_dict[gene_ids[i]]
            target_node = nodes_dict[gene_ids[i+1]]
            edge = Edge(source_node, target_node)
            edges.append(edge)
            ##
    
    return edges, nodes_dict