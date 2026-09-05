#Step 5

from rag.embeddings import create_embeddings


def retrieve_relevant_chunks(question, chunks, index, top_k=3):
    """Find the most relevant text chunks for a user question."""

    question_embedding = create_embeddings([question])

    scores, positions = index.search(question_embedding, top_k)

    results = []

    for score, position in zip(scores[0], positions[0]):
        if position != -1:
            results.append(
                {
                    "chunk": chunks[position],
                    "score": float(score),
                    "position": int(position),
                }
            )

    return results

