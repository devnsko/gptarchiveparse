import io
import json
import pprint

class TreeNode:
    def __init__(self, id: str, message: str | None = None):
        self.id: str = id
        self.message: str = message
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "children": [child.to_dict() for child in self.children]
        }
    
    def show(self, prefix=""):
        print(prefix + self.id)
        prefix += "*"
        for i, child in enumerate(self.children):
            if len(self.children) > 1:
                child.show(prefix=str(i+1)+prefix)
            else:
                child.show(prefix=prefix)

def structure_to_dict(structure):
    if isinstance(structure, frozenset):
        result = {}
        for item in structure:
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str):
                key, val = item
                result[key] = structure_to_dict(val)
            else:
                # Неизвестная структура, сохраняем как есть (например, примитив или тип)
                result[str(item)] = "?"
        return result
    elif isinstance(structure, tuple):
        return [structure_to_dict(x) for x in structure]
    else:
        return structure  # например, 'str', 'NoneType', 'int' и т.п.


def compare_structures(s1, s2):
    """Возвращает различающиеся ключи между двумя структурами-словами"""
    d1 = structure_to_dict(s1)
    d2 = structure_to_dict(s2)

    def walk_diff(a, b, prefix=''):
        diffs = []
        a_keys = set(a.keys()) if isinstance(a, dict) else set()
        b_keys = set(b.keys()) if isinstance(b, dict) else set()
        all_keys = a_keys | b_keys
        for key in all_keys:
            full_key = f"{prefix}.{key}" if prefix else key
            if key not in a:
                diffs.append(f"+ {full_key} (only in B)")
            elif key not in b:
                diffs.append(f"- {full_key} (only in A)")
            else:
                if type(a[key]) != type(b[key]):
                    diffs.append(f"! {full_key} (type mismatch: {type(a[key]).__name__} vs {type(b[key]).__name__})")
                elif isinstance(a[key], dict):
                    diffs += walk_diff(a[key], b[key], full_key)
        return diffs

    return walk_diff(d1, d2)

def analyze_all_differences(structures):
    structures = list(structures)
    for i in range(len(structures)):
        for j in range(i + 1, len(structures)):
            print(f"\n📌 Сравнение структуры {i + 1} и {j + 1}:")
            diffs = compare_structures(structures[i], structures[j])
            if diffs:
                for diff in diffs:
                    print("  ", diff)
            else:
                print("  🔁 Структуры идентичны")


def extract_structure(obj):
    if isinstance(obj, dict):
        return frozenset((k, extract_structure(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return frozenset(extract_structure(v) for v in obj)
    else:
        return type(obj).__name__

def count_unique_structure(content_list):
    structures = set()
    for item in content_list:
        structure = extract_structure(item)
        structures.add(structure)
    return structures
    
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

with open("example.json", "r") as f:
    data = json.load(f)
    # chat: TreeNode = TreeNode("client-created-root")
    chat: TreeNode = ChatTree(data["mapping"], "client-created-root")
    chat.show()
    
    objs = []

    def collect_objects(node, mapping):
        if node.id in mapping:
            objs.append(mapping[node.id]["message"])
        for child in node.children:
            collect_objects(child, mapping)

    collect_objects(chat, data["mapping"])
    uni = count_unique_structure(objs)
    
with open("structure_report.txt", "w", encoding="utf-8") as output:
    output.write(f"\nВсего уникальных структур: {len(uni)}\n")
    
    for idx, struct in enumerate(uni, 1):
        output.write(f"\n--- Структура {idx} ---\n")
        output.write(pprint.pformat(structure_to_dict(struct), width=120))
        output.write("\n")
    
    structures = list(uni)
    for i in range(len(structures)):
        for j in range(i + 1, len(structures)):
            output.write(f"\n📌 Сравнение структуры {i + 1} и {j + 1}:\n")
            diffs = compare_structures(structures[i], structures[j])
            if diffs:
                for diff in diffs:
                    output.write("  " + diff + "\n")
            else:
                output.write("  🔁 Структуры идентичны\n")
