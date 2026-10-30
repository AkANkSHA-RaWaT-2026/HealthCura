import re
from datetime import datetime
from typing import Optional

from app.services.fuzzy_lab_parser import extract_lab_values

# Flexible separator: matches whitespace, colons, dashes, parentheses
SEP = r"[\s():\-]*"

# Each pattern: (metric_name, regex, default_unit)
METRIC_PATTERNS = [
    ("Glucose", rf"glucose{SEP}(\d+\.?\d*){SEP}(mg/dl|mg%)?", "mg/dL"),
    ("Hemoglobin", rf"h(?:a)?emoglobin{SEP}(\d+\.?\d*){SEP}(g/dl)?", "g/dL"),
    ("Total Cholesterol", rf"(?<!hdl\s)(?<!ldl\s)cholesterol{SEP}(?:total{SEP})?(\d+\.?\d*){SEP}(mg/dl)?", "mg/dL"),
    ("HDL Cholesterol", rf"hdl(?:\s*cholesterol)?{SEP}(\d+\.?\d*){SEP}(mg/dl)?", "mg/dL"),
    ("LDL Cholesterol", rf"ldl(?:\s*cholesterol)?{SEP}(\d+\.?\d*){SEP}(mg/dl)?", "mg/dL"),
    ("Triglycerides", rf"tri[a-z]*rides{SEP}(\d+\.?\d*){SEP}(mg/dl)?", "mg/dL"),
    ("WBC", rf"w(?:hite)?\s*b(?:lood)?\s*c(?:ells?)?\s*(?:count)?{SEP}\(?wbc\)?{SEP}(\d+\.?\d*)", "x10³/uL"),
    ("RBC", rf"r(?:ed)?\s*b(?:lood)?\s*c(?:ells?)?\s*(?:count)?{SEP}\(?rbc\)?{SEP}(\d+\.?\d*)", "x10³/uL"),
    ("Hematocrit", rf"h(?:a)?ematocrit{SEP}(\d+\.?\d*){SEP}(%)?", "%"),
    ("Platelets", rf"platelets?{SEP}(?:count)?{SEP}(\d+\.?\d*)", "x10³/uL"),
    ("BUN", rf"(?:blood\s*urea\s*nitrogen|bun){SEP}(\d+\.?\d*){SEP}(mg/dl)?", "mg/dL"),
    ("Creatinine", rf"creatinine{SEP}(\d+\.?\d*){SEP}(mg/dl)?", "mg/dL"),
    ("Sodium", rf"sodium{SEP}(\d+\.?\d*){SEP}(mmol/l)?", "mmol/L"),
    ("Potassium", rf"potassium{SEP}(\d+\.?\d*){SEP}(mmol/l)?", "mmol/L"),
    ("Blood Pressure Systolic", r"(?:bp|blood\s+pressure)\s*[:\-]?\s*(\d+)\s*/\s*\d+", "mmHg"),
    ("Blood Pressure Diastolic", r"(?:bp|blood\s+pressure)\s*[:\-]?\s*\d+\s*/\s*(\d+)", "mmHg"),
    ("Heart Rate", rf"(?:heart\s*rate|pulse){SEP}(\d+)", "bpm"),
]

DATE_PATTERNS = [
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
]


def extract_document_date(text: str) -> Optional[str]:
    """Finds the first date in the text and returns it as an ISO string, or None."""
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
    Returns metrics found in the OCR text. Exact regex matches come first.
    Fuzzy matches are added only for tests the regex did not find.
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

            unit = default_unit
            if match.lastindex and match.lastindex >= 2 and match.group(2):
                unit = match.group(2)

            results.append({
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "recorded_date": document_date,
            })

    found_names = {result["metric_name"] for result in results}
    for lab_value in extract_lab_values(ocr_text):
        if lab_value["metric_name"] not in found_names:
            results.append({**lab_value, "recorded_date": document_date})

    return results