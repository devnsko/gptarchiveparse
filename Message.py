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

class MessageVectors:
    def __init__(self, message: Message, vectors: list[any]):
        self.message = message
        self.vectors = vectors

class MessageManager:
    messages: list[Message] = []

    def __init__(self, messages: list[Message] = []):
        self.messages = messages

    def addMessage(self, message: Message):
        self.messages.append(message)

    def addMessages(self, messages: list[Message]):
        self.messages.extend(messages)

    def getMessageByID(self, id: str):
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