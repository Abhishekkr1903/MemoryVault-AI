from rag.memory_retriever import retrieve_memories


query = "What is Machine Learning?"

results = retrieve_memories(
    question=query,
    document_ids=[2],
    top_k=3,
)


print("\nRESULT COUNT:", len(results))


for i, result in enumerate(results, start=1):

    print("\n" + "=" * 60)

    print("RESULT:", i)

    print("Document ID:", result.get("document_id"))

    print("Filename:", result.get("filename"))

    print("Category:", result.get("category"))

    print("Summary:", result.get("summary"))

    print("Keywords:", result.get("keywords"))

    print("Language:", result.get("language"))

    print("Position:", result.get("position"))

    print("Score:", result.get("score"))

    print("Chunk:")
    print(result.get("chunk"))