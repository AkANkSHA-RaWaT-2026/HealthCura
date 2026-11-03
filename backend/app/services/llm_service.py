"""Calls the Groq language model for blood report wording and discharge summaries."""

import os

from dotenv import load_dotenv
from groq import Groq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.services.text_cleaner import clean_markdown

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FAST_MODEL = "openai/gpt-oss-20b"
QUALITY_MODEL = "openai/gpt-oss-120b"

# gpt-oss models spend part of this budget on hidden reasoning, so the
# visible summary needs enough room left over to be written.
BLOOD_SUMMARY_MAX_TOKENS = 1000


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
)
def _call_groq(model: str, prompt: str, max_tokens: int = 1000) -> str:
    """Sends a prompt to Groq and returns the reply text. Returns "" if the reply is empty."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def generate_blood_summary_text(facts: list[str]) -> str:
    """
    Writes a short summary from a list of verified facts.
    The model may only restate these facts. The summary service checks its output.
    """
    if not facts:
        raise ValueError("No facts were provided for the summary.")

    fact_lines = "\n".join(f"- {fact}" for fact in facts)
    prompt = f"""You are writing a short factual summary of a blood test report for a patient.

Use ONLY the facts listed below. Copy every number exactly as written.
Write 3 to 5 plain sentences. Name the tests that were done, give their values,
and say which results are outside their reference range.

Rules:
- Do not explain what any result means for the patient.
- Do not give advice, diagnoses, or next steps.
- Do not use the words: should, recommend, consult, risk, suggest, diagnose.
- Do not mention dates, doctors, or clinics.
- Write plain text. No markdown, bullets, or headings.

Facts:
{fact_lines}

Summary:"""

    raw_text = _call_groq(FAST_MODEL, prompt, max_tokens=BLOOD_SUMMARY_MAX_TOKENS)
    return clean_markdown(raw_text)


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