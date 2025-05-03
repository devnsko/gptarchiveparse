import json
import os
import numpy as np
import pandas as pd
import umap
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_distances

INPUT_FILE = "graphs/prepared_messages.json"
OUTPUT_FILE_START_NAME = "graph_data_"

input_file_path = os.path.join(os.path.expanduser("~"), '.treegpt', *INPUT_FILE.replace("\\", "/").split("/"))
with open(input_file_path, "r", encoding="utf-8") as f:
    messages = json.load(f)

vectors = []
graph_data = []

for msg in messages:
    if isinstance(msg.get("vector"), list):
        vectors.append(msg["vector"])
        graph_data.append({
            "id": msg.get("message_id"),
            "parts": msg.get("parts", {}),
            "author": msg.get("author", ""),
            "title": msg.get("title", ""),
            "conversation_id": msg.get("conversation_id"),
            "parent": msg.get("parent"),
            "children": msg.get("children", []),
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

output_file_path = os.path.join(os.path.expanduser("~"), '.treegpt', 'graphs', OUTPUT_FILE_START_NAME + 'latest.json')
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=2, ensure_ascii=False)

print("✅ Готово: данные для графа сохранены в", output_file_path)
