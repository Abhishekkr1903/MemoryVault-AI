import json


ALLOWED_CATEGORIES = {
    "resume",
    "invoice",
    "receipt",
    "passport",
    "travel",
    "medical",
    "notes",
    "research",
    "book",
    "general",
}


def detect_category(query):
    """
    Detect a document category from the user's query.
    """

    query_lower = query.lower()

    for category in ALLOWED_CATEGORIES:

        if category in query_lower:
            return category

    return None


def filter_documents_by_metadata(
    documents,
    query,
):
    """
    Filter documents using document metadata.

    Returns a list of matching document IDs.

    If no category is detected, all documents are returned.
    """

    category = detect_category(query)

    # No metadata filter required.
    if category is None:

        return [
            document[0]
            for document in documents
        ]

    matching_document_ids = []

    for document in documents:

        (
            document_id,
            filename,
            file_path,
            created_at,
            document_category,
            summary,
            keywords,
            language,
        ) = document

        if document_category == category:

            matching_document_ids.append(
                document_id
            )

    return matching_document_ids