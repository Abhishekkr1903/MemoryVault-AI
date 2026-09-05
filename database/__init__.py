"""Database package for MemoryVault."""

from .db import get_all_documents, initialize_database, save_document_record

__all__ = [
    "get_all_documents",
    "initialize_database",
    "save_document_record",
]
