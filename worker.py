import json
import os
import numpy as np
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import umap
from sklearn.cluster import KMeans

from Message import Message, MessageVectors, MessageManager, VectorsManager

# Configurable paths
INPUT_FILE = os.path.join(os.path.expanduser("~"), '.treegpt', 'unzipped', 'conversations.json')
OUTPUT_VECTORS_FILE = os.path.join(os.path.expanduser("~"), '.treegpt', 'graphs', 'prepared_messages_v2.json')
OUTPUT_GRAPH_FILE = os.path.join(os.path.expanduser("~"), '.treegpt', 'graphs', 'graph_data_combined.json')
MAX_TOKENS = 400
N_CLUSTERS = 15

# Initialize models
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text: str, tokenizer, max_tokens: int = MAX_TOKENS) -> list[str]:
    words = text.split()
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(tokenizer.tokenize(" ".join(current))) >= max_tokens:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks

def get_message_text(msg: Message) -> str:
    if not msg or not msg.parts:
        return ""
    return '\n'.join(p['text'] for p in msg.parts if 'text' in p)


def get_parent_user(message_id: str | None, manager: MessageManager) -> Message | None:
    # Walk up until find the first user message
    current_id = message_id
    while current_id:
        msg = manager.getMessageByID(current_id)
        if not msg:
            return None
        if msg.author.lower() == 'user':
            return msg
        current_id = msg.parent
    return None

def prepare_vector(text: str) -> list[float]:
    tokens = tokenizer.tokenize(text)
    if len(tokens) > MAX_TOKENS:
        chunks = chunk_text(text, tokenizer)
        chunk_vecs = model.encode(chunks)
        return np.mean(chunk_vecs, axis=0).tolist()
    return model.encode(text).tolist()

def getConversationMessages(conversation: dict) -> list[Message]:
    manager_msgs: list[Message] = []
    # Traverse chain to collect all nodes in this conversation
    current = conversation.get('current_node')
    while current:
        node = conversation['mapping'].get(current)
        if not node:
            break
        nm = node.get('message') or {}
        # Determine author
        role = nm.get('author', {}).get('role', '')
        if role in ('assistant', 'tool'):
            author = 'ChatGPT'
        elif role == 'system' and nm.get('metadata', {}).get('is_user_system_message', False):
            author = 'Custom user info'
        else:
            author = role
        # Extract parts
        parts = []
        content = nm.get('content', {})
        for part in content.get('parts', []):
            # first handle dicts
            if isinstance(part, dict) and part.get('content_type') == 'audio_transcription':
                parts.append({'text': part.get('text', '')})
            # then non-empty strings
            elif isinstance(part, str) and part:
                parts.append({'text': part})
            # else ignore empty strings or unexpected types
        # Build Message
        msg = Message(
            id=node.get('id', ''),
            conversation_id=conversation.get('conversation_id', ''),
            title=conversation.get('title', ''),
            author=author,
            parts=parts,
            parent=node.get('parent'),
            children=node.get('children', [])
        )
        manager_msgs.append(msg)
        current = node.get('parent')
    manager_msgs.reverse()
    return manager_msgs

def cluster_vectors(vecs: list[MessageVectors]) -> list[dict]:
    # Prepare data and initial graph entries
    data = []
    graph = []
    for mv in vecs:
        if mv.vectors:
            data.append(mv.vectors)
            graph.append({
                'prompt': mv.parent.to_dict() if mv.parent else None,
                'reply': mv.child.to_dict(),
                'title': mv.child.conversation_title,
                'conversation_id': mv.child.conversation_id,
                'parent_id': mv.parent.parent if mv.parent else None,
                'children_id': mv.child.children
            })
    X = np.array(data)
    umap_3d = umap.UMAP(n_components=3, metric='cosine', n_neighbors=10)
    proj = umap_3d.fit_transform(X)
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42).fit(proj)
    for i, item in enumerate(graph):
        item['cluster'] = int(kmeans.labels_[i])
        x, y, z = proj[i]
        item['position'] = {'x': float(x), 'y': float(y), 'z': float(z)}
    return graph

if __name__ == '__main__':
    # Initialize managers
    msg_manager = MessageManager()
    vec_manager = VectorsManager()

    # Load raw conversations
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        convos = json.load(f)

    # First pass: collect all messages
    for convo in convos:
        msgs = getConversationMessages(convo)
        msg_manager.addMessages(msgs)

    # Second pass: vectorize ChatGPT replies with user context
    for msg in msg_manager.getAllMessages():
        if msg.author != 'ChatGPT':
            continue
        text = get_message_text(msg)
        parent = get_parent_user(msg.parent, msg_manager)
        if parent and get_message_text(parent):
            text = get_message_text(parent) + '\n' + text
        if not text:
            continue
        vec = prepare_vector(text)
        vec_manager.addVectors(parent=parent, child=msg, vectors=vec)

    # Save prepared vectors
    with open(OUTPUT_VECTORS_FILE, 'w', encoding='utf-8') as f:
        json.dump([mv.to_dict() for mv in vec_manager.getAllVectors()], f, indent=2, ensure_ascii=False)

    # Cluster and save graph data
    graph_data = cluster_vectors(vec_manager.getAllVectors())
    with open(OUTPUT_GRAPH_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Pipeline complete. Vectors: {OUTPUT_VECTORS_FILE}, Graph: {OUTPUT_GRAPH_FILE}")
