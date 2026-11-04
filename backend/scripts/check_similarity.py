"""Prints the cosine distance of each of a user's chunks for one question. Manual tuning only."""

import sys

from app.core.database import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import embed_text


def main() -> None:
    """Prints the closest eight chunks for the question, with their distances."""
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.check_similarity <user_id> <question>")
        return

    user_id = int(sys.argv[1])
    question = sys.argv[2]
    query_vector = embed_text(question)

    db = SessionLocal()
    try:
        distance = DocumentChunk.embedding.cosine_distance(query_vector)
        rows = (
            db.query(DocumentChunk.chunk_text, distance.label("distance"))
            .filter(DocumentChunk.user_id == user_id)
            .order_by(distance)
            .limit(8)
            .all()
        )
        for row in rows:
            print(f"{row.distance:.3f}  {row.chunk_text[:70]!r}")
    finally:
        db.close()


if __name__ == "__main__":
    main()