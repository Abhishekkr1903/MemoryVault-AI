from database.db import get_documents_with_metadata
from rag.metadata_filter import filter_documents_by_metadata


documents = get_documents_with_metadata()

query = "Tell me about my research memories"

document_ids = filter_documents_by_metadata(
    documents,
    query,
)

print("Matching document IDs:")
print(document_ids)