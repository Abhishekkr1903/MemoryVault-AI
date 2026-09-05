"""
Hybrid retrieval using:
1. FAISS semantic search
2. BM25 keyword search
3. Reciprocal Rank Fusion (RRF)
4. Cross Encoder reranking
"""

from rag.bm25 import build_bm25, bm25_search
from rag.retriever import retrieve_relevant_chunks
from rag.reranker import rerank_chunks


def reciprocal_rank_fusion(
    vector_results,
    bm25_results,
    k=60,
):
    """
    Combine FAISS and BM25 results using
    Reciprocal Rank Fusion (RRF).

    RRF score:
        1 / (k + rank)
    """

    scores = {}

    # --------------------------------
    # FAISS ranking
    # --------------------------------

    for rank, result in enumerate(vector_results):

        chunk = result["chunk"]

        if chunk not in scores:

            scores[chunk] = result.copy()

            scores[chunk]["rrf_score"] = 0.0

        scores[chunk]["rrf_score"] += (
            1 / (k + rank + 1)
        )

    # --------------------------------
    # BM25 ranking
    # --------------------------------

    for rank, result in enumerate(bm25_results):

        chunk = result["chunk"]

        if chunk not in scores:

            scores[chunk] = result.copy()

            scores[chunk]["rrf_score"] = 0.0

        scores[chunk]["rrf_score"] += (
            1 / (k + rank + 1)
        )

    # --------------------------------
    # Sort using RRF score
    # --------------------------------

    results = list(scores.values())

    results.sort(
        key=lambda x: x["rrf_score"],
        reverse=True,
    )

    return results


def hybrid_search(
    question,
    chunks,
    index,
    top_k=5,
):
    """
    Complete hybrid retrieval pipeline.

    Pipeline:

        Question
            ↓
        FAISS
            +
        BM25
            ↓
        RRF
            ↓
        Cross Encoder
            ↓
        Top K results
    """

    # ============================================
    # STEP 1 — Dense Search using FAISS
    # ============================================

    faiss_results = retrieve_relevant_chunks(
        question=question,
        chunks=chunks,
        index=index,
        top_k=top_k,
    )

    # ============================================
    # STEP 2 — Sparse Search using BM25
    # ============================================

    bm25 = build_bm25(chunks)

    bm25_results = bm25_search(
        bm25,
        chunks,
        question,
        top_k=top_k,
    )

    # ============================================
    # STEP 3 — Combine using RRF
    # ============================================

    rrf_results = reciprocal_rank_fusion(
        vector_results=faiss_results,
        bm25_results=bm25_results,
    )

    # ============================================
    # STEP 4 — Cross Encoder Reranking
    # ============================================

    final_results = rerank_chunks(
        question=question,
        results=rrf_results,
        top_k=3,
    )

    return final_results