from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Loaded once, reused across requests - same lazy-loading pattern as EasyOCR
_model = None


def get_embedding_model() -> SentenceTransformer:
    """Lazily loads the sentence embedding model once, then reuses it."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Splits long text into overlapping chunks suitable for embedding.
    Overlap helps avoid losing context at chunk boundaries.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)


def embed_text(text: str) -> list[float]:
    """Converts a piece of text into a 384-dimensional embedding vector."""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds multiple texts at once - more efficient than one at a time."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()