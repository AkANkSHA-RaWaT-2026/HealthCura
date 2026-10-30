from unittest.mock import MagicMock

from app.services import llm_service, rag_service


def test_summary_parses_bold_labels(monkeypatch):
    fake_reply = "**TYPE:** Lab Report\n**SUMMARY:** Your glucose is **102 mg/dL**."
    monkeypatch.setattr(llm_service, "_call_groq", lambda *args, **kwargs: fake_reply)

    result = llm_service.generate_medical_summary("Glucose 102 mg/dL")

    assert result["document_type"] == "Lab Report"
    assert result["summary"] == "Your glucose is 102 mg/dL."


def test_summary_without_labels_uses_cleaned_text(monkeypatch):
    monkeypatch.setattr(
        llm_service, "_call_groq", lambda *args, **kwargs: "**Plain** summary text."
    )

    result = llm_service.generate_medical_summary("Some text")

    assert result["document_type"] == "Other"
    assert result["summary"] == "Plain summary text."


def test_summary_rejects_empty_input():
    try:
        llm_service.generate_medical_summary("   ")
    except ValueError:
        return
    raise AssertionError("Expected ValueError for empty text")


def test_discharge_summary_removes_markdown(monkeypatch):
    monkeypatch.setattr(
        llm_service, "_call_groq", lambda *args, **kwargs: "## Overview\n**Stable** condition."
    )

    result = llm_service.generate_discharge_summary("Test Patient", "Some records")

    assert result == "Overview\nStable condition."


def test_chat_answer_is_cleaned_and_saved(monkeypatch):
    monkeypatch.setattr(rag_service, "retrieve_relevant_chunks", lambda *args: [])
    monkeypatch.setattr(
        rag_service, "_call_groq", lambda *args, **kwargs: "Your glucose is **102 mg/dL**."
    )
    fake_db = MagicMock()

    answer = rag_service.ask_question(fake_db, user_id=1, question="glucose?")

    assert answer == "Your glucose is 102 mg/dL."
    assert fake_db.add.call_count == 2
    fake_db.commit.assert_called_once()