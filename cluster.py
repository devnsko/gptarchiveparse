import json
import os
import numpy as np
import pandas as pd
import umap
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_distances
from Message import MessageVectors, VectorsManager

INPUT_FILE = "graphs/prepared_messages_v2.json"
OUTPUT_FILE_START_NAME = "graph_data_"

def parse_message(d):
    return Message(
        id=d["message_id"],
        conversation_id=d["conversation_id"],
        title=d["conversation_title"],
        author=d["author"],
        parts=d["parts"],
        parent=d.get("parent"),
        children=d.get("children", [])
    )

def parse_message_vectors(d):
    parent = parse_message(d["parent"]) if d["parent"] else None
    child = parse_message(d["child"])
    return MessageVectors(parent=parent, child=child, vectors=d["vectors"])

input_file_path = os.path.join(os.path.expanduser("~"), '.treegpt', *INPUT_FILE.replace("\\", "/").split("/"))
with open(input_file_path, "r", encoding="utf-8") as f:
    raw = json.load(f)
    messages: list[MessageVectors] = [parse_message_vectors(x) for x in raw]

vectors = []
graph_data = []

for msg in messages:
    print(msg)
    if msg.vectors and len(msg.vectors) > 0:
        vectors.append(msg.vectors)
        graph_data.append({
            "propmt": msg.parent,
            "reply": msg.child,
            "title": msg.child.conversation_title,
            "conversation_id": msg.child.conversation_id,
            "parent_id": msg.parent.parent,
            "children_id": msg.child.children
        })

X = np.array(vectors)
umap_3d = umap.UMAP(n_components=3, metric="cosine", n_neighbors=10)
projected = umap_3d.fit_transform(X)

kmeans = KMeans(n_clusters=15, random_state=42).fit(projected)
labels = kmeans.labels_

for i, item in enumerate(graph_data):
    item["cluster"] = int(labels[i])
    item["position"] = {
        "x": float(projected[i][0]),
        "y": float(projected[i][1]),
        "z": float(projected[i][2])
    }

output_file_path = os.path.join(os.path.expanduser("~"), '.treegpt', 'graphs', OUTPUT_FILE_START_NAME + 'v2_latest.json')
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=4, ensure_ascii=False)

print("✅ Готово: данные для графа сохранены в", output_file_path)
