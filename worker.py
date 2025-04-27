import re
import json
import numpy as np
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

def getConversationMessages(conversation):
    messages = []
    currentNode = conversation.get("current_node", {})
    while currentNode is not None:
        node = conversation["mapping"][currentNode]
        node_message = node.get("message", {})
        node_content = node_message.get("content", {}) if node_message else None
        node_content_parts = node_content.get("parts", "") if node_content else None
        if (node_message and 
            node_content and 
            node_content_parts and
            len(node_content_parts) > 0 and
            (node_message["author"]["role"] != "system" or 
             node_message["metadata"].get("is_user_system_message", False))):
            
            author = node_message["author"]["role"]
            if author == "assistant" or author == "tool":
                author = "ChatGPT"
            elif author == "system" and node_message["metadata"].get("is_user_system_message", False):
                author = "Custom user info"
            
            if node_content["content_type"] == "text" or  node_content["content_type"] == "multimodal_text":
                parts = []
                for i in range(len(node_content_parts)):
                    part = node_content["parts"][i]
                    if isinstance(part, str) and len(part) > 0:
                        parts.append({"text": part})
                    elif isinstance(part, str) and len(part) == 0:
                        continue
                    elif part.get("content_type", "") == "audio_transcription":
                        parts.append({"transcript": part["text"]})
                    elif (part["content_type"] == "audio_asset_pointer" or
                          part["content_type"] == "image_asset_pointer" or
                          part["content_type"] == "video_container_asset_pointer"):
                        parts.append({"asset": part})
                    elif part["content_type"] == "real_time_user_audio_video_asset_pointer":
                        if part.get("audio_asset_pointer", False):
                            parts.append({"asset": part["audio_asset_pointer"]})
                        if part.get("video_container_asset_pointer", False):
                            parts.append({"asset": part["video_container_asset_pointer"]})
                        for j in range(len(part.get("frames_asset_pointers", {}))):
                            parts.append({"asset": part["frames_asset_pointers"][j]})
                if len(parts) > 0:
                    messages.append({
                        "title": conversation.get("title", ""),
                        "conversation_id": conversation.get("conversation_id", ""),
                        "message_id": node.get("id", ""),
                        "parent": node.get("parent", ""),
                        "children": node.get("children", []),
                        "author": author, 
                        "parts": parts})
        currentNode = node["parent"]
    messages.reverse()
    return messages

def chunk_text(text: str, tokenizer, max_tokens=400):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        tokenized = tokenizer.tokenize(" ".join(current_chunk))
        if len(tokenized) >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def prepare_message_vector(text: str, tokenizer, model):
    token_count = len(tokenizer.tokenize(text))
    if token_count > 400:
        chunks = chunk_text(text, tokenizer)
        vectors = model.encode(chunks)
        return np.mean(vectors, axis=0).tolist()
    else:
        return model.encode(text).tolist()

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer("all-MiniLM-L6-v2")

with open("example.json", "r") as f:
    data = json.load(f)
    messages = getConversationMessages(data)

with open(rf"C:/Code/fx/treegpt/gptchats/conversations.json", "r") as jsn:
    data = json.load(jsn)

    messages = []
    for conversation in data[:10]:
        print(conversation.get("title", ""))
        messages.extend(getConversationMessages(conversation))
    
    for msg in messages:
        try:
            text = '\n'.join(part['text'] for part in msg["parts"] if isinstance(part.get('text', None), str))
            if text:
                msg["vector"] = prepare_message_vector(text, tokenizer, model)
        except TypeError as e:
            print(f"ERROR with {msg.get('message_id', msg.get('id'))} in chat: {msg.get('conversation_id', '#')} error: {e}")

with open("prepared_messages.json", "w", encoding="utf-8") as f:
    json.dump(messages, f, indent=2, ensure_ascii=False)

print("✅ Готово! Сообщения обработаны и готовы к кластеризации.")