from rag.memory_retriever import retrieve_memories


query = "Tell me about my research memories"


results = retrieve_memories(
    question=query,
    document_ids=None,
    top_k=5,
)


print("\n")
print("=" * 70)
print("FINAL RESULTS")
print("=" * 70)


for i, result in enumerate(results, start=1):

    print("\n")
    print(f"RESULT {i}")
    print("-" * 70)

    print("Document ID:", result.get("document_id"))
    print("Filename:", result.get("filename"))

    print("RRF Score:", result.get("rrf_score"))

    print(
        "Rerank Score:",
        result.get("rerank_score")
    )

    print("\nChunk:")
    print(result.get("chunk"))