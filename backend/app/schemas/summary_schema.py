"""Response shape for generated and saved summaries."""

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    """A summary with its flagged results and disclaimer."""

    document_id: int
    document_type: str
    summary: str
    flagged: list[str]
    disclaimer: str
    summary_source: str  # "ai", "template", or "saved"