"""Builds the plain-language blood report summary from stored health records.

Flags are computed here from the database rows, never by the language model.
The model only writes sentences. Its text is rejected, and a template summary
is used instead, if it contains a number that is not in the data, has the wrong
number of sentences, or gives advice or interpretation.
"""

import logging
import re
from typing import Callable

from app.services.reference_ranges import METRICS_BY_NAME
from app.services.text_cleaner import clean_markdown

logger = logging.getLogger(__name__)

BLOOD_REPORT_TYPE = "Blood Test Report"
OTHER_TYPE = "Other"
MIN_SENTENCES = 2
MAX_SENTENCES = 5

DISCLAIMER = (
    "This summary describes the values printed on your document. It is an AI "
    "reference aid, not a diagnosis, and it does not replace advice from your doctor."
)
OTHER_SUMMARY = (
    "This document does not contain any of the supported blood test results, so no "
    "values are summarised. It is stored and can be searched in chat."
)

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
# Unit exponents such as "x10^3" are part of the unit, not a result value
UNIT_EXPONENT_PATTERN = re.compile(r"x?10\^\d+")
SENTENCE_BREAK = re.compile(r"[.!?]+(?:\s+|$)")
# Words that give interpretation or advice, which the summary must not contain
FORBIDDEN_WORDS = re.compile(
    r"\b(should|recommend\w*|consult\w*|diagnos\w*|risk\w*|indicat\w*|suggest\w*|"
    r"concern\w*|dangerous|healthy|treat\w*|medication\w*|anemi\w*|anaemi\w*|"
    r"diabet\w*|because|therefore|means?)\b",
    re.IGNORECASE,
)

SummaryWriter = Callable[[list[str]], str]


def format_number(value: float) -> str:
    """Formats a number without trailing zeros, so 13.80 becomes 13.8 and 265.0 becomes 265."""
    return f"{value:g}"


def value_with_unit(row: dict) -> str:
    """Returns the value followed by its unit, if one is stored."""
    unit = f" {row['unit']}" if row.get("unit") else ""
    return f"{format_number(row['value'])}{unit}"


def describe_range(low: float | None, high: float | None) -> str:
    """Returns a readable range such as "13 to 17", "up to 200", or "70 or more"."""
    if low is not None and high is not None:
        return f"{format_number(low)} to {format_number(high)}"
    if high is not None:
        return f"up to {format_number(high)}"
    if low is not None:
        return f"{format_number(low)} or more"
    return "not available"


def reference_for_row(row: dict) -> tuple[float | None, float | None, str]:
    """
    Returns (low, high, source) for a row. The range printed on the lab report
    is used when present, otherwise the standard range from reference_ranges.py.
    """
    printed_low = row.get("printed_low")
    printed_high = row.get("printed_high")
    if printed_low is not None or printed_high is not None:
        return printed_low, printed_high, "lab report"

    metric = METRICS_BY_NAME.get(row["metric_name"])
    if metric is None:
        return None, None, "not available"
    low, high = metric.standard_range
    return low, high, "standard"


def build_flagged(rows: list[dict]) -> list[str]:
    """
    Returns one sentence per result outside its reference range.
    The text is built from database values only, never from the language model.
    """
    flagged = []
    for row in rows:
        if row.get("status") not in ("low", "high"):
            continue
        low, high, source = reference_for_row(row)
        direction = "above" if row["status"] == "high" else "below"
        flagged.append(
            f"{row['metric_name']} was {value_with_unit(row)}, {direction} the reference "
            f"range of {describe_range(low, high)} ({source} range)."
        )
    return flagged


def build_facts(rows: list[dict]) -> list[str]:
    """Returns one plain line per result. These lines are the only input to the language model."""
    facts = []
    for row in rows:
        low, high, source = reference_for_row(row)
        if row.get("status") == "unknown" or (low is None and high is None):
            comparison = "no reference range available to compare"
        else:
            state = {"low": "below", "high": "above"}.get(row.get("status"), "within")
            comparison = f"{state} the reference range of {describe_range(low, high)} ({source} range)"
        facts.append(f"{row['metric_name']}: {value_with_unit(row)}, {comparison}")
    return facts


def allowed_numbers(rows: list[dict]) -> list[float]:
    """Returns every number the summary is allowed to mention."""
    numbers = {float(len(rows)), float(len(build_flagged(rows)))}
    for row in rows:
        numbers.add(float(row["value"]))
        for side in (row.get("printed_low"), row.get("printed_high")):
            if side is not None:
                numbers.add(float(side))
        low, high, _ = reference_for_row(row)
        for side in (low, high):
            if side is not None:
                numbers.add(float(side))
    return list(numbers)


def count_sentences(text: str) -> int:
    """Counts sentences. A decimal point such as 13.8 does not end a sentence."""
    return len([part for part in SENTENCE_BREAK.split(text.strip()) if part.strip()])

def numbers_in_text(text: str) -> list[str]:
    """Returns the numbers in the text, ignoring unit exponents such as x10^3."""
    without_units = UNIT_EXPONENT_PATTERN.sub("", text)
    return NUMBER_PATTERN.findall(without_units)

def check_ai_summary(text: str, rows: list[dict]) -> str | None:
    """Returns the reason the text is rejected, or None if it passes every check."""
    if not text:
        return "empty text"

    sentences = count_sentences(text)
    if not MIN_SENTENCES <= sentences <= MAX_SENTENCES:
        return f"{sentences} sentences"

    if FORBIDDEN_WORDS.search(text):
        return "contains interpretation or advice"

    allowed = allowed_numbers(rows)
    for number in numbers_in_text(text):
        if not any(abs(float(number) - known) < 1e-9 for known in allowed):
            return f"number {number} is not in the data"

    return None


def build_template_summary(rows: list[dict]) -> str:
    """Returns a fixed-format summary. Used when the language model is unavailable or rejected."""
    if not rows:
        return "No supported blood test results were found in this document."

    listed = ", ".join(f"{row['metric_name']} {value_with_unit(row)}" for row in rows)
    sentences = [f"This blood test report includes {len(rows)} supported results: {listed}."]

    flagged_count = len(build_flagged(rows))
    if flagged_count:
        noun = "result is" if flagged_count == 1 else "results are"
        sentences.append(f"{flagged_count} {noun} outside the reference range, as listed below.")
    else:
        sentences.append("None of the results are outside their reference ranges.")

    return " ".join(sentences)


def _default_writer(facts: list[str]) -> str:
    """Calls the language model. Imported here so tests can run without a Groq key."""
    from app.services.llm_service import generate_blood_summary_text

    return generate_blood_summary_text(facts)


def create_summary(
    rows: list[dict],
    document_type: str,
    writer: SummaryWriter | None = None,
) -> dict:
    """
    Returns the document type, summary, flagged list, and disclaimer.
    summary_source is "ai" when the model's text passed every check, otherwise "template".
    """
    if document_type != BLOOD_REPORT_TYPE or not rows:
        return {
            "document_type": OTHER_TYPE,
            "summary": OTHER_SUMMARY,
            "flagged": [],
            "disclaimer": DISCLAIMER,
            "summary_source": "template",
        }

    summary = None
    summary_source = "template"
    write = writer or _default_writer

    try:
        candidate = clean_markdown(write(build_facts(rows)))
        rejection = check_ai_summary(candidate, rows)
        if rejection is None:
            summary = candidate
            summary_source = "ai"
        else:
            logger.warning("AI summary rejected: %s", rejection)
    except Exception:
        logger.exception("AI summary generation failed; using template summary")

    if summary is None:
        summary = build_template_summary(rows)

    return {
        "document_type": BLOOD_REPORT_TYPE,
        "summary": summary,
        "flagged": build_flagged(rows),
        "disclaimer": DISCLAIMER,
        "summary_source": summary_source,
    }