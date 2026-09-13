import os
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Small/fast model - used for quick, interactive requests (Summary, Chat)
FAST_MODEL = "openai/gpt-oss-20b"
# Larger model - used for one-time, quality-matters generation (Discharge Summary)
QUALITY_MODEL = "openai/gpt-oss-120b"


class GroqRateLimitError(Exception):
    """Raised when Groq returns a 429 after all retries are exhausted."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
)
def _call_groq(model: str, prompt: str, max_tokens: int = 1000) -> str:
    """Internal helper - sends a prompt to Groq, retries on transient failures."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,  # lower = more consistent/factual, less creative - important for medical content
    )
    return response.choices[0].message.content


def generate_medical_summary(ocr_text: str) -> str:
    """
    Takes raw OCR text from a medical document and returns a
    plain-language summary a patient can understand.
    """
    if not ocr_text or not ocr_text.strip():
        raise ValueError("Cannot summarize empty document text.")

    prompt = f"""You are a medical assistant helping a patient understand their document.
Summarize the following medical document in simple, plain language a non-medical
person can understand. Explain any medical terms. Keep it concise - 3 to 5 sentences.
Do not give medical advice or recommendations - only explain what the document says.

Document text:
{ocr_text}

Plain-language summary:"""

    try:
        return _call_groq(FAST_MODEL, prompt, max_tokens=400)
    except Exception as e:
        raise RuntimeError(f"Failed to generate summary: {str(e)}")


def generate_discharge_summary(patient_name: str, documents_context: str) -> str:
    """
    Generates a structured discharge-style summary from a patient's
    combined document history. Uses the larger/quality model since this
    is generated once and read carefully, not an interactive request.
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

Do not invent information not present in the documents. Do not give new medical advice -
only organize and summarize what the documents actually say. If information for a section
isn't available, say so briefly rather than making something up.

Document excerpts:
{documents_context}

Structured summary:"""

    try:
        return _call_groq(QUALITY_MODEL, prompt, max_tokens=1200)
    except Exception as e:
        raise RuntimeError(f"Failed to generate discharge summary: {str(e)}")