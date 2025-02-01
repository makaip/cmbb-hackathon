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
