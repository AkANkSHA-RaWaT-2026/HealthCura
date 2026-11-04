from app.services import rag_service


class FakeSession:
    """Records added messages so the tests can check what was saved."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass


def test_no_relevant_chunks_returns_not_found_without_calling_model(monkeypatch):
    calls = []

    monkeypatch.setattr(rag_service, "retrieve_relevant_chunks", lambda db, uid, q: [])
    monkeypatch.setattr(rag_service, "_call_groq", lambda *a, **k: calls.append(a) or "x")

    db = FakeSession()
    answer = rag_service.ask_question(db, 1, "What is the capital of France?")

    assert answer == rag_service.NOT_FOUND_MESSAGE
    assert calls == []
    assert [m.role for m in db.added] == ["user", "assistant"]


def test_relevant_chunks_are_sent_to_the_model(monkeypatch):
    seen_prompts = []

    monkeypatch.setattr(
        rag_service, "retrieve_relevant_chunks", lambda db, uid, q: ["Hemoglobin 14.2 g/dL"]
    )

    def fake_groq(model, prompt, max_tokens):
        seen_prompts.append(prompt)
        return "Your hemoglobin was 14.2 g/dL."

    monkeypatch.setattr(rag_service, "_call_groq", fake_groq)

    answer = rag_service.ask_question(FakeSession(), 1, "What was my hemoglobin?")

    assert answer == "Your hemoglobin was 14.2 g/dL."
    assert "Hemoglobin 14.2 g/dL" in seen_prompts[0]


def test_cutoff_constant_is_below_one():
    # Cosine distance ranges from 0 to 2. A cutoff of 1 or more would accept most chunks.
    assert 0 < rag_service.SIMILARITY_CUTOFF < 1