from rag.graph import memory_graph


# ==================================================
# TEST QUESTION
# ==================================================

question = (
    "What do you know about my "
    "machine learning background?"
)


# ==================================================
# GRAPH STATE
# ==================================================

initial_state = {

    "question": question,

    "messages": [
        question
    ],

    "answer": "",

    "search_scope": "All Memories",

    "current_document_id": None,

    "selected_document_ids": [],
}


# ==================================================
# DEBUG
# ==================================================

print()
print("=" * 60)
print("MEMORYVAULT LANGGRAPH AGENT TEST")
print("=" * 60)

print()
print("QUESTION:")
print(
    initial_state["question"]
)

print()
print("SEARCH SCOPE:")
print(
    initial_state["search_scope"]
)

print()
print("CURRENT DOCUMENT:")
print(
    initial_state["current_document_id"]
)

print()
print("SELECTED DOCUMENTS:")
print(
    initial_state["selected_document_ids"]
)


# ==================================================
# RUN GRAPH
# ==================================================

result = memory_graph.invoke(
    initial_state
)


# ==================================================
# FINAL RESULT
# ==================================================

print()
print("=" * 60)
print("FINAL ANSWER")
print("=" * 60)

print(
    result["answer"]
)
