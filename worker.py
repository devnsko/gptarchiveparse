import json

jsonpath = fr"../gptchats/conversations.json"

with open(jsonpath, "r") as file:
    chats = json.load(file)
    print(chats[0]["mapping"]["7b0d8574-8536-4a11-b7c4-da368a1a6de4"]["message"]["content"])

# import json

# def print_json_structure(data, indent=0):
#     """Recursively print the structure of a JSON object with parameter names and data types."""
#     if isinstance(data, dict):
#         for key, value in data.items():
#             print(" " * indent + f"{key}: {type(value).__name__}")
#             print_json_structure(value, indent + 4)
#     elif isinstance(data, list):
#         print(" " * indent + f"List[{len(data)}]:")
#         if len(data) > 0:
#             print_json_structure(data[0], indent + 4)

# jsonpath = fr"../gptchats/conversations.json"

# with open(jsonpath, "r") as file:
#     chats = json.load(file)
#     print_json_structure(chats)