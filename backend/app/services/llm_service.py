import os

from dotenv import load_dotenv
from groq import Groq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.services.text_cleaner import clean_markdown

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FAST_MODEL = "openai/gpt-oss-20b"
QUALITY_MODEL = "openai/gpt-oss-120b"

DOCUMENT_TYPES = [
    "Lab Report", "Prescription", "Discharge Summary", "Radiology Report",
    "Pathology Report", "Consultation Note", "Vaccination Record",
    "Medical Certificate", "Other",
]


class GroqRateLimitError(Exception):
    """Raised when Groq returns a 429 after all retries are exhausted."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
)
def _call_groq(model: str, prompt: str, max_tokens: int = 1000) -> str:
    """Sends a prompt to Groq and returns the raw text. Retries on failure."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content


def generate_medical_summary(ocr_text: str) -> dict:
    """
    Takes raw OCR text and returns a dict with a document type and a
    plain-language summary. Markdown is removed before parsing, so
    labels like "**TYPE:**" are still found.
    """
    if not ocr_text or not ocr_text.strip():
        raise ValueError("Cannot summarize empty document text.")

    type_list = ", ".join(DOCUMENT_TYPES)
    prompt = f"""You are a medical assistant helping a patient understand their document.

First, classify this document as exactly one of these types: {type_list}
Then summarize it in simple, plain language a non-medical person can understand.
Explain any medical terms. Keep the summary concise - 3 to 5 sentences.
Do not give medical advice or recommendations - only explain what the document says.

Document text:
{ocr_text}

Respond in exactly this format:
TYPE: <one of the document types listed above>
SUMMARY: <your plain-language summary>"""

    try:
        raw_response = _call_groq(FAST_MODEL, prompt, max_tokens=500)
    except Exception as e:
        raise RuntimeError(f"Failed to generate summary: {str(e)}")

    cleaned_response = clean_markdown(raw_response)

    document_type = "Other"
    summary = cleaned_response

    if "TYPE:" in cleaned_response and "SUMMARY:" in cleaned_response:
        type_part = cleaned_response.split("TYPE:")[1].split("SUMMARY:")[0].strip()
        summary_part = cleaned_response.split("SUMMARY:")[1].strip()
        if type_part in DOCUMENT_TYPES:
            document_type = type_part
        summary = summary_part

    return {"document_type": document_type, "summary": summary}


def generate_discharge_summary(patient_name: str, documents_context: str) -> str:
    """
    Generates a structured discharge-style summary from a patient's
    document history. Uses the larger model because it is generated
    once and read carefully.
    """
    if not documents_context or not documents_context.strip():
        raise ValueError("No document data available to generate a summary.")

    prompt = f"""You are helping prepare a plain-language health summary for a patient named {patient_name}.
This is an AI-generated reference document, NOT an official medical discharge summary.

Using the document excerpts below, write a structured summary with these sections:
1. Overview - brief summary of what documents/records exist
2. Key Findings - notable test results or observations, including anything outside normal ranges
3. Current Status - overall picture based on available records
4. Follow-up Notes - any follow-up instructions or recommendations mentioned in the documents

IMPORTANT FORMATTING RULES:
- Write in plain text only. Do NOT use Markdown syntax of any kind.
- Do NOT use asterisks for bold (**text**), pound signs for headings (###), pipe characters
  for tables (| | |), or dashes for horizontal rules (---).
- For section headings, just write the section name plainly on its own line (e.g. "Overview").
- For lists, use simple dashes or plain sentences, not tables.
- Use only standard ASCII punctuation - plain hyphens (-), not special dashes.

Do not invent information not present in the documents. Do not give new medical advice -
only organize and summarize what the documents actually say. If information for a section
isn't available, say so briefly rather than making something up.

Document excerpts:
{documents_context}

Structured summary:"""

    try:
        raw_summary = _call_groq(QUALITY_MODEL, prompt, max_tokens=1200)
    except Exception as e:
        raise RuntimeError(f"Failed to generate discharge summary: {str(e)}")

    return clean_markdown(raw_summary)