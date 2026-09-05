from rag.graph import memory_graph


initial_state = {
    "question": "What is machine learning?",
    "chat_history": [],

    "search_scope": "Current Memory",
    "selected_document_ids": [2],

    "rewritten_question": "",
    "document_ids": None,
    "retrieved_chunks": [],
    "answer": "",
}


result = memory_graph.invoke(initial_state)


print("\n==============================")
print("FINAL ANSWER")
print("==============================")

print(result["answer"])