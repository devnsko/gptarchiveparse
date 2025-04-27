import json
import numpy as np
from sklearn.metrics.pairwise import cosine_distances
from sklearn.cluster import DBSCAN
import umap
import pandas as pd


with open("prepared_messages.json", "r", encoding="utf-8") as f:
    messages = json.load(f)


vectors = []
graph_data = []

for msg in messages:
    if "vector" in msg and isinstance(msg["vector"], list):
        vectors.append(msg["vector"])
        graph_data.append({
            "id": msg.get("message_id", msg.get("id")),
            "parts": msg.get("parts", ""),
            "author": msg.get("author", ""),
            "title": msg.get("title", ""),
            "conversation_id": msg.get("conversation_id", ""),
            "parent": msg.get("parent", None),
            "children": msg.get("children", []),
        })

X = np.array(vectors)

distance_matrix = cosine_distances(X)
clustering = DBSCAN(eps=0.3, min_samples=2, metric="precomputed").fit(distance_matrix)

labels = clustering.labels_
for i, item in enumerate(graph_data):
    item["cluster"] = int(labels[i])

umap_3d = umap.UMAP(n_components=3, metric="cosine")
coords_3d = umap_3d.fit_transform(X)

for i, item in enumerate(graph_data):
    item["position"] = {
        "x": float(coords_3d[i][0]),
        "y": float(coords_3d[i][1]),
        "z": float(coords_3d[i][2])
    }

with open("graph_data.json", "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=2, ensure_ascii=False)

print("✅ Готово! Файл 'graph_data.json' можно использовать для визуализации в JavaFX.")
