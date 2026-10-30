from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import embed_text
from app.services.llm_service import FAST_MODEL, _call_groq
from app.services.text_cleaner import clean_markdown


def retrieve_relevant_chunks(db: Session, user_id: int, question: str, top_k: int = 5) -> list[str]:
    """
    Embeds the question and returns the most similar chunks from the
    user's own documents. Uses pgvector's cosine distance, where a
    smaller number means a closer match.
    """
    question_embedding = embed_text(question)

    results = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.user_id == user_id)
        .order_by(DocumentChunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
        .all()
    )
    return [chunk.chunk_text for chunk in results]


def build_rag_prompt(question: str, context_chunks: list[str]) -> str:
    """Builds a prompt that limits the LLM's answer to the retrieved chunks."""
    if not context_chunks:
        return f"""You are a medical assistant helping a patient understand their health records.
The patient has no uploaded documents yet, or none relevant to this question.

Patient's question: {question}

Politely explain that you don't have any relevant document information to answer this,
and suggest they upload a relevant document first. Do not make up information."""

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
    Runs the full chat pipeline: retrieve chunks, build the prompt, get
    a cleaned answer from the LLM, and save both messages to chat history.
    """
    chunks = retrieve_relevant_chunks(db, user_id, question)
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