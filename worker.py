
import json
import numpy as np
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import os
from Message import Message, MessageVectors, MessageManager, VectorsManager

INPUT_FILE = fr"unzipped/conversations.json"
OUTPUT_FILE = "graphs/prepared_messages_v2.json"
MAX_TOKENS = 400

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, tokenizer, max_tokens=MAX_TOKENS):
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
    if msg is None:
        return ""
    text = '\n'.join(part['text'] for part in msg.parts if isinstance(part.get('text', None), str))
    return text

def get_parent_user(id: str) -> Message:
    msg = manager.getMessageByID(id)
    if msg is None:
        return None
    if msg.author in ["Custom user info", "ChatGPT"]:
        msg = get_parent_user(msg.parent)
    return msg

def prepare_vector(text):
    token_count = len(tokenizer.tokenize(text))
    if token_count > MAX_TOKENS:
        chunks = chunk_text(text, tokenizer)
        chunk_vecs = model.encode(chunks)
        return np.mean(chunk_vecs, axis=0).tolist()
    else:
        return model.encode(text).tolist()

def getConversationMessages(conversation):
    messages: list[Message] = []
    currentNode = conversation.get("current_node", {})
    while currentNode is not None:
        node = conversation["mapping"][currentNode]
        node_message = node.get("message", {})
        node_content = node_message.get("content", {}) if node_message else None
        node_content_parts = node_content.get("parts", "") if node_content else None
        print(node.get("id", "-"))
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
                    newmsg = Message(
                        id=node.get("id", ""),
                        conversation_id=conversation.get("conversation_id", ""),
                        title=conversation.get("title", ""),
                        author=author,
                        parts=parts,
                        parent=node.get("parent", ""),
                        children=node.get("children", [])
                    )
                    messages.append(newmsg)
        currentNode = node["parent"]
    messages.reverse()
    return messages

manager: MessageManager = MessageManager()
vectorManager: VectorsManager = VectorsManager()

input_file_path = os.path.join(os.path.expanduser("~"), '.treegpt', *INPUT_FILE.replace("\\", "/").split("/"))
with open(input_file_path, "r", encoding="utf-8") as f:
    conversations = json.load(f)

# TODO: Combine pairs with question and answer

all_messages_vectors: list[MessageVectors] = []
for i, convo in enumerate(conversations[:30]):
    newmsgs = getConversationMessages(convo)
    manager.addMessages(newmsgs)

for msg in manager.getAllMessages():
    try:
        if msg.author != 'ChatGPT':
            continue
        text = get_message_text(msg)
        parent: Message = get_parent_user(msg.parent)
        if parent and len(get_message_text(parent)) > 0:
            text = get_message_text(parent) + "\n" + text

        if text:
            vectors = prepare_vector(text)
            vectorManager.addVectors(parent=parent, child=msg, vectors=vectors)

    except Exception as e:
        print(f"[Ошибка] в сообщении {msg.message_id}: {e}")

output_file_path = os.path.join(os.path.expanduser("~"), '.treegpt', *OUTPUT_FILE.replace("\\", "/").split("/"))
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump([vec.to_dict() for vec in vectorManager.getAllVectors()], f, indent=4, ensure_ascii=False)

print("[Success] Сообщения обработаны и сохранены в", OUTPUT_FILE)
