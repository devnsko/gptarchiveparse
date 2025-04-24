import json

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def to_dict(self):
        return {
            "value": self.value,
            "children": [child.to_dict() for child in self.children]
        }
    
    def show(self, prefix=""):
        print(prefix + self.value)
        prefix += "*"
        for i, child in enumerate(self.children):
            if len(self.children) > 1:
                child.show(prefix=str(i+1)+prefix)
            else:
                child.show(prefix=prefix)

    
def ChatTree(map, id, root=None):
    if root is None:
        root = TreeNode("client-created-root")
    
    node = map.get(id)
    if node:
        children = node.get("children", [])
        for child_id in children:
            child_node = TreeNode(child_id)
            root.add_child(child_node)
            ChatTree(map, child_id, child_node)
    
    return root

# def ShowTree(root, prefix=""):
#     print(root)


with open("example.json", "r") as f:
    data = json.load(f)
    # chat: TreeNode = TreeNode("client-created-root")
    chat: TreeNode = ChatTree(data["mapping"], "client-created-root")
    chat.show()
