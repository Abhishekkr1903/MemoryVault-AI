"""
Retrieve memories using metadata-aware document filtering
and hybrid retrieval.
"""

from database.db import get_documents_with_metadata
from rag.metadata_filter import filter_documents_by_metadata
from rag.query_router import detect_metadata_intent
from rag.vectorstore import load_vectorstore
from rag.hybrid_search import hybrid_search


def retrieve_memories(
    question,
    document_ids=None,
    top_k=5,
):
    """
    Search one, many, or all memories.

    Parameters
    ----------
    question : str
        User's rewritten question.

    document_ids : list[int] | None
        None -> Search memories based on query intent.
        [1] -> Search one memory.
        [1, 2, 3] -> Search selected memories.

    top_k : int
        Number of final chunks returned.
    """

    all_results = []

    # ============================================
    # STEP 1 — Get documents with metadata
    # ============================================

    documents = get_documents_with_metadata()

    # ============================================
    # STEP 2 — Explicit memory selection
    # ============================================

    if document_ids is not None:

        documents = [
            document
            for document in documents
            if document[0] in document_ids
        ]

    # ============================================
    # STEP 3 — Automatic metadata filtering
    # ============================================

    else:

        category = detect_metadata_intent(question)

        if category:

            filtered_document_ids = filter_documents_by_metadata(
                documents,
                question,
            )

            documents = [
                document
                for document in documents
                if document[0] in filtered_document_ids
            ]

    # ============================================
    # STEP 4 — Search selected documents
    # ============================================

    for document in documents:

        document_id = document[0]
        filename = document[1]
        category = document[4]
        summary = document[5]
        keywords = document[6]
        language = document[7]

        chunks, embeddings, index = load_vectorstore(
            document_id
        )

        if chunks is None or index is None:
            continue

        # ----------------------------------------
        # Hybrid Search
        # ----------------------------------------

        results = hybrid_search(
            question=question,
            chunks=chunks,
            index=index,
            top_k=5,
        )

        # ----------------------------------------
        # Attach metadata
        # ----------------------------------------

        for result in results:

            result["document_id"] = document_id
            result["filename"] = filename
            result["category"] = category
            result["summary"] = summary
            result["keywords"] = keywords
            result["language"] = language

            all_results.append(result)

    # ============================================
    # STEP 5 — Global ranking
    # ============================================

    all_results.sort(
        key=lambda x: x.get(
            "rerank_score",
            x.get("rrf_score", 0),
        ),
        reverse=True,
    )

    return all_results[:top_k]