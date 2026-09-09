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