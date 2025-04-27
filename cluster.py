import json
import numpy as np
import pandas as pd
import umap
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_distances

INPUT_FILE = "prepared_messages.json"
OUTPUT_FILE = "graph_data.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
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

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=2, ensure_ascii=False)

print("✅ Готово: данные для графа сохранены в", OUTPUT_FILE)
