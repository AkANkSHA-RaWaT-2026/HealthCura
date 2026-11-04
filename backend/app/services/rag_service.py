"""Retrieves a user's relevant document excerpts and answers chat questions from them."""

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import embed_text
from app.services.llm_service import FAST_MODEL, _call_groq
from app.services.text_cleaner import clean_markdown

# Cosine distance: smaller means more similar. Chunks at or above this distance are
# treated as unrelated. 0.5 is a starting value and should be tuned with real documents.
SIMILARITY_CUTOFF = 0.7
TOP_K = 5
NOT_FOUND_MESSAGE = "I couldn't find that in your documents."


def retrieve_relevant_chunks(db: Session, user_id: int, question: str) -> list[str]:
    """
    Returns up to TOP_K chunk texts from the user's own documents that are closer
    to the question than SIMILARITY_CUTOFF. Returns an empty list if none qualify.
    """
    question_embedding = embed_text(question)
    distance = DocumentChunk.embedding.cosine_distance(question_embedding)

    rows = (
        db.query(DocumentChunk.chunk_text)
        .filter(DocumentChunk.user_id == user_id)
        .filter(distance < SIMILARITY_CUTOFF)
        .order_by(distance)
        .limit(TOP_K)
        .all()
    )
    return [row.chunk_text for row in rows]


def build_rag_prompt(question: str, context_chunks: list[str]) -> str:
    """Builds a prompt that limits the answer to the retrieved excerpts."""
    context = "\n\n---\n\n".join(context_chunks)
    return f"""You are a medical assistant helping a patient understand their own medical documents.
Answer the patient's question using ONLY the information in the document excerpts below.
If the excerpts don't contain enough information to answer, say so honestly - do not guess
or use outside medical knowledge. Do not give medical advice or diagnoses - only explain
what the documents say. Keep your answer concise and in plain language.

Document excerpts:
{context}

Patient's question: {question}

Answer:"""


def get_chat_history(db: Session, user_id: int, limit: int = 20) -> list[ChatMessage]:
    """Returns the user's recent chat messages, oldest first."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


def ask_question(db: Session, user_id: int, question: str) -> str:
    """
    Answers a question from the user's documents. If no excerpt is close enough,
    returns NOT_FOUND_MESSAGE without calling the language model.
    Both the question and the answer are saved to chat history.
    """
    chunks = retrieve_relevant_chunks(db, user_id, question)

    if not chunks:
        answer = NOT_FOUND_MESSAGE
    else:
        prompt = build_rag_prompt(question, chunks)
        try:
            raw_answer = _call_groq(FAST_MODEL, prompt, max_tokens=500)
        except Exception as e:
            raise RuntimeError(f"Failed to generate answer: {str(e)}")
        answer = clean_markdown(raw_answer)

    db.add(ChatMessage(user_id=user_id, role="user", content=question))
    db.add(ChatMessage(user_id=user_id, role="assistant", content=answer))
    db.commit()

    return answer