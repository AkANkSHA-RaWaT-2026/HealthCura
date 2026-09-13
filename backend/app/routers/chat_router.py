from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.schemas.chat_schema import ChatQuestion, ChatAnswer, ChatMessageResponse
from app.services.rag_service import ask_question, get_chat_history

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=ChatAnswer)
def ask(
    payload: ChatQuestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask a question about the user's own medical documents (RAG chat)."""
    try:
        answer = ask_question(db, current_user.id, payload.question)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to answer right now. Please try again.",
        )
    return ChatAnswer(answer=answer)


@router.get("/history", response_model=list[ChatMessageResponse])
def history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the user's recent chat history, oldest first."""
    return get_chat_history(db, current_user.id)