"""Reads a blood test report's OCR text into structured rows.

Only the supported metrics are read. A value is kept only if it passes every
check, because a missing value is safer than a wrong one.
"""

import difflib
import re
from datetime import date

from app.services.reference_ranges import (
    BMP,
    CBC,
    LIPID,
    METRICS,
    get_status,
    printed_range_matches_standard,
)

SIMILARITY_THRESHOLD = 0.75
VALUE_WINDOW = 3  # tokens after a test name to search for its result
RANGE_TOLERANCE = 1.5  # a result may sit this far outside the printed range
MIN_REPORT_YEAR = 2000
FILLER_WORDS = {"count", "level", "total", "serum", "cholesterol", "blood", "nitrogen"}
SKIP_IF_NEXT_WORD = {"volume", "distribution"}  # "Mean Platelet Volume" is not Platelets

UNIT_TOKENS = {("mg", "dl"): "mg/dL", ("g", "dl"): "g/dL", ("mmol", "l"): "mmol/L"}
# Count units printed before a range. "cells" means per uL, so 4,200 cells = 4.2 x10^3/uL.
COUNT_UNIT_SCALE = {"cells": 0.001, "million": 1.0}

TOKEN_PATTERN = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
NUMBER_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")

# Thousands separators: "1,32,000" (Indian grouping) and "4,200" (standard grouping)
INDIAN_THOUSANDS = re.compile(r"(\d),(\d{2}),(\d{3})\b")
STANDARD_THOUSANDS = re.compile(r"(\d),(\d{3})\b")

NUMERIC_DATE = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-]?(\d{4,5})")
MONTH_NAME_DATE = re.compile(r"(\d{1,2})[\s/-]*([a-z]{3,9})[\s/-]*(\d{4})", re.IGNORECASE)
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
# OCR often misreads "Report" (for example "Repor", "Rcported", "Aepon").
# The label is followed by "Date" or "On", and the date is read after it.
REPORT_DATE_LABEL = re.compile(r"(?:rep|rcp|aep)\w{0,8}\s+(?:date|on)\b", re.IGNORECASE)
LABEL_LOOKAHEAD_CHARS = 80  # the date may sit on the next line after the label
# Month names that OCR misreads so badly that the normal lookup cannot match them
MONTH_OCR_FIXES = {"vsy": 5, "mav": 5, "msy": 5}

LAB_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z.&' -]{2,40}?\s(?:clinic|laboratory|laboratories|hospital|medical cent(?:re|er)))\b",
    re.IGNORECASE,
)
PANEL_PATTERNS = [
    (re.compile(r"complete blood count|\bcbc\b", re.IGNORECASE), CBC),
    (re.compile(r"lipid profile|lipid panel", re.IGNORECASE), LIPID),
    (re.compile(r"kidney|electrolyte|renal|basic metabolic", re.IGNORECASE), BMP),
]


def _build_date(day: int, month: int, year: int) -> date | None:
    """Returns a date if the parts form a valid date in a plausible year, otherwise None."""
    if not MIN_REPORT_YEAR <= year <= date.today().year + 1:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _month_number(word: str) -> int | None:
    """Returns the month number for a month name, including known OCR misreadings."""
    key = word.lower()
    if key[:3] in MONTHS:
        return MONTHS[key[:3]]
    return MONTH_OCR_FIXES.get(key)


def _first_valid_date(text: str) -> date | None:
    """
    Returns the first valid date in the text. Numeric dates are read as
    day/month/year, and month-name dates such as "25-May-2024" are also accepted.
    """
    for match in NUMERIC_DATE.finditer(text):
        # Keep the last four digits, so "07/1122021" reads as 2021
        found = _build_date(int(match.group(1)), int(match.group(2)), int(match.group(3)[-4:]))
        if found:
            return found

    for match in MONTH_NAME_DATE.finditer(text):
        month_number = _month_number(match.group(2))
        if month_number is None:
            continue
        found = _build_date(int(match.group(1)), month_number, int(match.group(3)))
        if found:
            return found
    return None


def extract_report_date(ocr_text: str) -> date | None:
    """
    Returns the report date. A date found just after a "Report" label is preferred,
    because a report also prints other dates, such as the collection date.
    Falls back to the first valid date in the text.
    """
    label = REPORT_DATE_LABEL.search(ocr_text)
    if label:
        start = label.end()
        window = ocr_text[start:start + LABEL_LOOKAHEAD_CHARS]
        found = _first_valid_date(window)
        if found:
            return found
    return _first_valid_date(ocr_text)


def extract_lab_name(ocr_text: str) -> str | None:
    """Returns the first clinic or laboratory name printed on the report, for display only."""
    for match in LAB_PATTERN.finditer(ocr_text):
        name = match.group(1).strip()
        # Column headings such as "DEPARTMENT Of LABORATORY" are not the lab's name
        if "department" not in name.lower():
            return name.title()
    return None


def extract_panel_name(ocr_text: str) -> str | None:
    """Returns the panel named first in the report, such as CBC or Lipid Profile."""
    earliest_panel = None
    earliest_position = None
    for pattern, panel in PANEL_PATTERNS:
        match = pattern.search(ocr_text)
        if match and (earliest_position is None or match.start() < earliest_position):
            earliest_position = match.start()
            earliest_panel = panel
    return earliest_panel


def _normalize_numbers(text: str) -> str:
    """
    Removes thousands separators, then turns any remaining comma into a decimal point.
    "1,32,000" becomes "132000", "4,200" becomes "4200", and "265,00" becomes "265.00".
    """
    text = INDIAN_THOUSANDS.sub(r"\1\2\3", text)
    text = STANDARD_THOUSANDS.sub(r"\1\2", text)
    return text.replace(",", ".")


def _tokenize(ocr_text: str) -> list[str]:
    """Lowercases the text, normalizes numbers, and splits it into words and numbers."""
    return TOKEN_PATTERN.findall(_normalize_numbers(ocr_text.lower()))


def _is_name_match(token: str, alias: str) -> bool:
    """Short words must match exactly. Longer words allow small spelling mistakes."""
    if len(token) <= 4 or len(alias) <= 4:
        return token == alias
    ratio = difflib.SequenceMatcher(None, token, alias).ratio()
    return ratio >= SIMILARITY_THRESHOLD


def _find_value_index(tokens: list[str], name_index: int) -> int | None:
    """
    Returns the position of the result number after a test name, or None.
    Only filler words may appear before the number. Anything else stops the search.
    """
    end = min(name_index + 1 + VALUE_WINDOW, len(tokens))
    for position in range(name_index + 1, end):
        token = tokens[position]
        if token in FILLER_WORDS:
            continue
        return position if NUMBER_PATTERN.match(token) else None
    return None


def _read_unit(tokens: list[str], start: int, default_unit: str) -> tuple[str, int, float]:
    """
    Returns (unit, next position, scale). The scale converts the result to the
    unit stored for the metric. A count unit such as "cells / µL" is divided by 1000.
    """
    for words, unit in UNIT_TOKENS.items():
        if tuple(tokens[start:start + len(words)]) == words:
            return unit, start + len(words), 1.0

    if start < len(tokens) and tokens[start] in COUNT_UNIT_SCALE:
        next_position = start + 1
        # Skip the "l" left over from the micro sign (µL)
        if next_position < len(tokens) and tokens[next_position] == "l":
            next_position += 1
        return default_unit, next_position, COUNT_UNIT_SCALE[tokens[start]]

    return default_unit, start, 1.0


def _read_printed_range(tokens: list[str], start: int) -> tuple[float, float] | None:
    """Returns (low, high) if two numbers in increasing order follow, otherwise None."""
    numbers = []
    for token in tokens[start:start + 2]:
        if not NUMBER_PATTERN.match(token):
            break
        numbers.append(float(token))

    if len(numbers) != 2 or numbers[0] >= numbers[1]:
        return None
    return numbers[0], numbers[1]


def _passes_checks(metric, value: float, trusted_range) -> bool:
    """
    Rejects zero, values outside the plausible range, and values far outside
    the printed range. Only a printed range that matched the standard is passed in.
    """
    low, high = metric.plausible_range
    if value == 0 or not low <= value <= high:
        return False

    if trusted_range is not None:
        printed_low, printed_high = trusted_range
        if value < printed_low / RANGE_TOLERANCE or value > printed_high * RANGE_TOLERANCE:
            return False
    return True


def _find_row(tokens: list[str], metric) -> dict | None:
    """Returns the first valid row for a metric, or None if no valid value is found."""
    for name_index, token in enumerate(tokens):
        if not any(_is_name_match(token, alias) for alias in metric.aliases):
            continue
        if name_index > 0 and tokens[name_index - 1] in metric.excluded_previous:
            continue
        if name_index + 1 < len(tokens) and tokens[name_index + 1] in SKIP_IF_NEXT_WORD:
            continue

        value_index = _find_value_index(tokens, name_index)
        if value_index is None:
            continue

        unit, after_unit, scale = _read_unit(tokens, value_index + 1, metric.unit)
        value = round(float(tokens[value_index]) * scale, 4)

        printed = _read_printed_range(tokens, after_unit)
        if printed is not None:
            printed = (round(printed[0] * scale, 4), round(printed[1] * scale, 4))
            # A printed range that does not look like the standard one is probably OCR noise
            if not printed_range_matches_standard(metric, printed):
                printed = None

        if not _passes_checks(metric, value, printed):
            continue

        printed_low, printed_high = printed if printed else (None, None)
        return {
            "metric_name": metric.name,
            "panel": metric.panel,
            "value": value,
            "unit": unit,
            "printed_low": printed_low,
            "printed_high": printed_high,
            "status": get_status(metric.name, value, printed),
        }
    return None


def _extract_panel_and_lab(ocr_text: str) -> tuple[str | None, str | None]:
    """Returns the lab name and panel name for display."""
    return extract_lab_name(ocr_text), extract_panel_name(ocr_text)


def parse_blood_report(ocr_text: str | None) -> dict:
    """
    Returns the report header and one row per supported test that was found.
    document_type is "Blood Test Report" only when at least one test is found,
    so other documents never produce health records.
    """
    ocr_text = ocr_text or ""
    tokens = _tokenize(ocr_text)

    rows = []
    for metric in METRICS:
        row = _find_row(tokens, metric)
        if row is not None:
            rows.append(row)

    lab_name, panel_name = _extract_panel_and_lab(ocr_text)

    return {
        "document_type": "Blood Test Report" if rows else "Other",
        "report_date": extract_report_date(ocr_text),
        "lab_name": lab_name,
        "panel_name": panel_name,
        "rows": rows,
    }

