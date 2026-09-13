from pydantic import BaseModel, Field
from datetime import datetime


class ChatQuestion(BaseModel):
    """A question the patient asks the RAG chat assistant."""
    question: str = Field(min_length=1, max_length=1000)


class ChatAnswer(BaseModel):
    """The assistant's answer to a question."""
    answer: str


class ChatMessageResponse(BaseModel):
    """A single message in chat history."""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True