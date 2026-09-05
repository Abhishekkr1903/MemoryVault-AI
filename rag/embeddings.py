#step 3

from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load and cache the embedding model."""

    return SentenceTransformer(MODEL_NAME)


def create_embeddings(chunks):
    """Convert text chunks into normalized numerical vectors."""

    model = get_embedding_model()

    return model.encode(
        chunks,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )