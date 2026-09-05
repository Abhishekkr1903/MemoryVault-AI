"""
Cross Encoder reranking for retrieved memory chunks.
"""

from sentence_transformers import CrossEncoder


# Load the model once when this module is imported.
reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def rerank_chunks(
    question,
    results,
    top_k=3,
):
    """
    Re-rank retrieved chunks using a Cross Encoder.

    The Cross Encoder receives:

        (question, chunk)

    and produces a relevance score.
    """

    if not results:
        return []

    # --------------------------------
    # Create question-chunk pairs
    # --------------------------------

    pairs = [
        (
            question,
            result["chunk"],
        )
        for result in results
    ]

    # --------------------------------
    # Predict relevance scores
    # --------------------------------

    scores = reranker.predict(pairs)

    # --------------------------------
    # Create new result objects
    # --------------------------------

    reranked_results = []

    for result, score in zip(results, scores):

        updated_result = result.copy()

        updated_result["rerank_score"] = float(score)

        reranked_results.append(
            updated_result
        )

    # --------------------------------
    # Highest relevance first
    # --------------------------------

    reranked_results.sort(
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    return reranked_results[:top_k]