from rag.query_router import detect_metadata_intent


queries = [
    "Tell me about my research memories",
    "Show my research documents",
    "What is machine learning?",
    "Tell me about my resume",
]


for query in queries:

    result = detect_metadata_intent(query)

    print(
        f"Query: {query}"
    )

    print(
        f"Detected intent: {result}"
    )

    print("-" * 50)
    