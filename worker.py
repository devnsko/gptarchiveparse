import json

class TreeNode:
    def __init__(self, id: str, role: str | None = None, message: str | None = None):
        self.id: str = id
        self.role = role
        self.message: str = message
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "message": self.message,
            "children": [child.to_dict() for child in self.children]
        }
    
    def show(self, prefix=""):
        print(prefix + self.id + " ? " + (self.role if self.role else 'None') + " = " + (self.message[:50].replace('\n', '') if self.message else ''))
        prefix += "*"
        for i, child in enumerate(self.children):
            if len(self.children) > 1:
                child.show(prefix=str(i+1)+prefix)
            else:
                child.show(prefix=prefix)

def ChatTree(map, id, root=None):
    node = map.get(id)
    message = node.get("message", {})
    msgText = None
    content = message.get("content", {}) if message else None
    if content and (content.get("content_type", "") == "text" or content.get("content_type", "") == "multimodal_text"):
        parts = content.get("parts", [])
        if isinstance(parts, list):
            msgText = '\n'.join(part if isinstance(part, str) else "file" for part in parts)
    role = None
    if message:
        role = message.get("author", {}).get("role", "") if message.get("author", {}) else None
    if root is None:
        root = TreeNode(id, role, msgText)
    
    if node:
        children = node.get("children", [])
        for child_id in children:
            child = map.get(child_id)
            child_message = child.get("message", {})
            child_msgText = None
            content = child.get("message", {}).get("content", {}) if child.get("message", {}) else None
            if content and (content.get("content_type", "") == "text" or content.get("content_type", "") == "multimodal_text"):
                parts = content.get("parts", [])
                if isinstance(parts, list):
                    child_msgText = '\n'.join(part if isinstance(part, str) else "file" for part in parts)
            child_role = None
            if child_message:
                child_role = child_message.get("author", {}).get("role", "") if child_message.get("author", {}) else None
            
            child_node = TreeNode(child_id, child_role, child_msgText)
            root.add_child(child_node)
            ChatTree(map, child_id, child_node)
    
    return root

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
            (node_message["author"]["role"] is not "system" or 
             node_message["metadata"].get("is_user_system_message", False))):
            
            author = node_message["author"]["role"]
            if author is "assistant" or author is "tool":
                author = "ChatGPT"
            elif author is "system" and node_message["metadata"].get("is_user_system_message", False):
                author = "Custom user info"
            
            if node_content["content_type"] is "text" or  node_content["content_type"] is "multimodal_text":
                parts = []
                for i in range(len(node_content_parts)):
                    part = node_content["parts"][i]
                    if type(part is str and len(part) > 0):
                        parts.append({"text": part})
                    elif part["content_type"] is "audio_transcription":
                        parts.append({"transcript": part["text"]})
                    elif (part["content_type"] is "audio_asset_pointer" or
                          part["content_type"] is "image_asset_pointer" or
                          part["content_type"] is "video_container_asset_pointer"):
                        parts.append({"asset": part})
                    elif part["content_type"] is "real_time_user_audio_video_asset_pointer":
                        if part.get("audio_asset_pointer", False):
                            parts.append({"asset": part["audio_asset_pointer"]})
                        if part.get("video_container_asset_pointer", False):
                            parts.append({"asset": part["video_container_asset_pointer"]})
                        for j in range(len(part.get("frames_asset_pointers", {}))):
                            parts.append({"asset": part["frames_asset_pointers"][j]})
            if len(parts) > 0:
                messages.append({"author": author, "parts": parts})
        currentNode = node["parent"]
    return messages.reverse()




with open("example.json", "r") as f:
    data = json.load(f)
    # chat: TreeNode = TreeNode("client-created-root")
    chat: TreeNode = ChatTree(data["mapping"], "client-created-root")
    print(data["title"])
    chat.show()