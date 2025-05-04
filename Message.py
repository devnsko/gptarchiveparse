from typing import TypedDict

class Position3D(TypedDict):
    x: float
    y: float
    z: float

class Message:
    # message_id: str
    # conversation_id: str
    # conversation_title: str
    # parent: str
    # children: list[str]
    # author: str
    # parts: list[any]


    def __init__(self, id, conversation_id, title, author, parts: list[any] = [], parent: str | None = None, children: list[str] = []):
        self.message_id: str = id
        self.conversation_id: str = conversation_id
        self.conversation_title: str = title
        self.parent: str = parent 
        self.children: list[str] = children
        self.author: str = author
        self.parts: list[any] = parts

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "conversation_title": self.conversation_title,
            "parent": self.parent,
            "children": self.children,
            "author": self.author,
            "parts": self.parts,
        }

class MessageVectors:
    def __init__(self, parent: Message, child: Message, vectors: list[any]):
        self.parent = parent
        self.child = child
        self.vectors = vectors

    def to_dict(self):
        return {
            "parent": self.parent.to_dict() if self.parent else None,
            "child": self.child.to_dict(),
            "vectors": self.vectors
        }

class GraphNode:
    def __init__(self, prompt, reply, title, conversation_id, parent_id, children_id, cluster, position):
        self.prompt: Message = prompt
        self.reply: Message = reply
        self.title: str = title
        self.conversation_id: str = conversation_id
        self.parent_id: str = parent_id
        self.children_id: str = children_id
        self.cluster: int = cluster
        self.position: Position3D = position
    
class VectorsManager:
    vectors: list[MessageVectors] = []

    def __init__(self, messages: list[MessageVectors] = []):
        self.vectors = messages

    def addVectors(self, parent: Message, child: Message, vectors: list[any]):
        msg = MessageVectors(parent=parent, child=child, vectors=vectors)
        self.vectors.append(msg)

    def getVectorByChildId(self, id: str) -> MessageVectors | None:
        for msg in self.vectors:
            if msg.child.message_id == id:
                return msg
        print(f"[Not Found] message vectors by child id: {id}")
        return None

    def getVectorByParentId(self, id: str) -> MessageVectors | None:
        for msg in self.vectors:
            if msg.parent.message_id == id:
                return msg
        print(f"[Not Found] message vectors by parent id: {id}")
        return None
    
    def getAllVectors(self) -> list[MessageVectors]:
        return self.vectors


class MessageManager:
    messages: list[Message] = []

    def __init__(self, messages: list[Message] = []):
        self.messages = messages

    def addMessage(self, message: Message):
        self.messages.append(message)

    def addMessages(self, messages: list[Message]):
        self.messages.extend(messages)

    def getMessageByID(self, id: str) -> Message | None:
        if id is None or not id:
            return None
        for msg in self.messages:
            if msg.message_id == id:
                return msg
    
    def getMessagesByConversationID(self, conv_id: str) -> list[Message]:
        msgs: list[Message] = []
        for msg in self.messages:
            if msg.conversation_id == conv_id:
                msgs.append(msg)
        return msgs
    
    def getAllMessages(self):
        return self.messages