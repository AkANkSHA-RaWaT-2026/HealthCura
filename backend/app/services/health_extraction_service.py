import re
from datetime import datetime
from typing import Optional

# Each pattern: (metric_name, regex, default_unit)
# Regex captures the numeric value; unit is captured if present, else we use the default.
# These cover common formats seen in Indian lab reports (per project scope).
METRIC_PATTERNS = [
    ("Glucose", r"glucose\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dl|mg%)?", "mg/dL"),
    ("Hemoglobin", r"h(?:a)?emoglobin\s*[:\-]?\s*(\d+\.?\d*)\s*(g/dl)?", "g/dL"),
    ("Cholesterol", r"(?:total\s+)?cholesterol\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dl)?", "mg/dL"),
    ("WBC", r"wbc\s*(?:count)?\s*[:\-]?\s*(\d+\.?\d*)\s*(/ul|cells/cumm|/cumm)?", "/uL"),
    ("Platelets", r"platelets?\s*(?:count)?\s*[:\-]?\s*(\d+\.?\d*)\s*(/ul|lakhs?/cumm)?", "/uL"),
    ("Blood Pressure Systolic", r"(?:bp|blood\s+pressure)\s*[:\-]?\s*(\d+)\s*/\s*\d+", "mmHg"),
    ("Blood Pressure Diastolic", r"(?:bp|blood\s+pressure)\s*[:\-]?\s*\d+\s*/\s*(\d+)", "mmHg"),
    ("Heart Rate", r"(?:heart\s+rate|pulse)\s*[:\-]?\s*(\d+)\s*(bpm)?", "bpm"),
]

# Common date formats seen in medical documents
DATE_PATTERNS = [
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
]


def extract_document_date(text: str) -> Optional[str]:
    """
    Attempts to find a date in the document text.
    Returns an ISO date string (YYYY-MM-DD) or None if no date is confidently found.
    """
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%d %B %Y", "%d %b %Y"):
                try:
                    return datetime.strptime(date_str, fmt).date().isoformat()
                except ValueError:
                    continue
    return None


def extract_health_metrics(ocr_text: str) -> list[dict]:
    """
    Scans OCR text for known medical metric patterns and returns a list of
    extracted metrics as dicts: {metric_name, value, unit, recorded_date}.

    This is best-effort pattern matching, not guaranteed to catch every
    format - real lab reports vary widely. Only high-confidence matches
    (clear numeric value next to a recognized metric name) are returned.
    """
    if not ocr_text:
        return []

    document_date = extract_document_date(ocr_text)
    results = []

    for metric_name, pattern, default_unit in METRIC_PATTERNS:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
            except (ValueError, IndexError):
                continue

            # Use captured unit if the regex found one, else fall back to default
            unit = default_unit
            if match.lastindex and match.lastindex >= 2 and match.group(2):
                unit = match.group(2)

            results.append({
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "recorded_date": document_date,
            })

    return results