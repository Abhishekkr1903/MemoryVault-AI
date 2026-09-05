from rank_bm25 import BM25Okapi


def build_bm25(chunks):
    """
    Build a BM25 index from text chunks.
    """

    tokenized_chunks = [
        chunk.lower().split()
        for chunk in chunks
    ]

    bm25 = BM25Okapi(tokenized_chunks)

    return bm25


def bm25_search(
    bm25,
    chunks,
    query,
    top_k=5,
):
    """
    Search chunks using BM25.
    """

    tokenized_query = query.lower().split()

    scores = bm25.get_scores(
        tokenized_query
    )

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []

    for index, score in ranked[:top_k]:

        results.append(
            {
                "chunk": chunks[index],
                "score": float(score),
                "position": index,
            }
        )

    return results