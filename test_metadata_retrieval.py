from rag.memory_retriever import retrieve_memories


question = "Tell me about my research memories"


results = retrieve_memories(
    question=question,
    document_ids=None,
    top_k=5,
)


print("\n")
print("=" * 70)
print("METADATA-AWARE RETRIEVAL")
print("=" * 70)


print("\nRESULT COUNT:", len(results))


for i, result in enumerate(results, start=1):

    print("\n" + "-" * 70)

    print("RESULT:", i)
    print("Document ID:", result.get("document_id"))
    print("Filename:", result.get("filename"))
    print("Category:", result.get("category"))
    print("RRF Score:", result.get("rrf_score"))
    print("Rerank Score:", result.get("rerank_score"))

    print("\nChunk:")
    print(result.get("chunk"))