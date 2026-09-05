import faiss
import numpy as np
import pickle
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_ROOT = ROOT_DIR / "data" / "vectorstore"


def create_faiss_index(embeddings):
    """Create a FAISS vector index from embeddings."""
    embeddings = np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def save_vectorstore(document_id, chunks, embeddings, index):
    """Save chunks, embeddings, and FAISS index to disk."""
    store_dir = VECTORSTORE_ROOT / str(document_id)
    store_dir.mkdir(parents=True, exist_ok=True)

    with open(store_dir / "chunks.pkl", "wb") as file:
        pickle.dump(chunks, file)

    np.save(store_dir / "embeddings.npy", embeddings)
    faiss.write_index(index, str(store_dir / "index.faiss"))


def load_vectorstore(document_id):
    """Load saved chunks, embeddings, and FAISS index from disk."""
    store_dir = VECTORSTORE_ROOT / str(document_id)

    chunks_path = store_dir / "chunks.pkl"
    embeddings_path = store_dir / "embeddings.npy"
    index_path = store_dir / "index.faiss"

    if not chunks_path.exists() or not embeddings_path.exists() or not index_path.exists():
        return None, None, None

    with open(chunks_path, "rb") as file:
        chunks = pickle.load(file)

    index = faiss.read_index(str(index_path))
    embeddings = np.load(embeddings_path)

    return chunks, embeddings, index
