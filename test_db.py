from database.db import (
    initialize_database,
    create_conversation,
    get_conversations,
    save_message,
    get_messages,
    rename_conversation,
    delete_conversation,
)

print("=" * 50)
print("Initializing Database...")
initialize_database()

print("=" * 50)
print("Creating Conversation...")
conversation_id = create_conversation("My First Chat")
print(f"Conversation ID: {conversation_id}")

print("=" * 50)
print("Saving Messages...")
save_message(conversation_id, "user", "Hello")
save_message(conversation_id, "assistant", "Hi! How can I help you?")

print("=" * 50)
print("Loading Messages...")
messages = get_messages(conversation_id)

for msg in messages:
    print(msg)

print("=" * 50)
print("Renaming Conversation...")
rename_conversation(conversation_id, "Python Learning")

print(get_conversations())

print("=" * 50)
print("Deleting Conversation...")
delete_conversation(conversation_id)

print(get_conversations())

print("=" * 50)
print("Database Test Completed Successfully!")