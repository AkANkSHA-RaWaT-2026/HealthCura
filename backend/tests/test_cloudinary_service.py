import cloudinary.uploader

from app.services import cloudinary_service


def test_public_id_drops_version_folder_and_extension():
    url = "https://res.cloudinary.com/demo/image/upload/v1793708010/healthcura_documents/abc123.png"
    assert cloudinary_service.get_public_id_from_url(url) == "healthcura_documents/abc123"


def test_public_id_for_pdf_drops_pdf_extension():
    url = "https://res.cloudinary.com/demo/image/upload/v1793708010/healthcura_documents/auedh2.pdf"
    assert cloudinary_service.get_public_id_from_url(url) == "healthcura_documents/auedh2"


def test_public_id_works_without_version_segment():
    url = "https://res.cloudinary.com/demo/image/upload/healthcura_documents/abc123.jpg"
    assert cloudinary_service.get_public_id_from_url(url) == "healthcura_documents/abc123"


def test_non_cloudinary_url_has_no_public_id():
    assert cloudinary_service.get_public_id_from_url("https://example.com/file.png") is None


def test_delete_calls_cloudinary_with_public_id(monkeypatch):
    calls = []

    def fake_destroy(public_id, **kwargs):
        calls.append((public_id, kwargs))
        return {"result": "ok"}

    monkeypatch.setattr(cloudinary.uploader, "destroy", fake_destroy)
    url = "https://res.cloudinary.com/demo/image/upload/v1/healthcura_documents/abc123.png"

    assert cloudinary_service.delete_file_from_cloudinary(url) is True
    assert calls[0][0] == "healthcura_documents/abc123"


def test_delete_returns_false_when_cloudinary_does_not_confirm(monkeypatch):
    monkeypatch.setattr(
        cloudinary.uploader, "destroy", lambda public_id, **kwargs: {"result": "not found"}
    )
    url = "https://res.cloudinary.com/demo/image/upload/v1/healthcura_documents/abc123.png"

    assert cloudinary_service.delete_file_from_cloudinary(url) is False