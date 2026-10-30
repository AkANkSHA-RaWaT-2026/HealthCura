"""Finds lab values in messy OCR text by matching test names approximately.

Runs as a fallback after the exact patterns in health_extraction_service.py.
A value is skipped when it looks wrong, because a missing value is safer
than a wrong one in a medical app.
"""

import difflib
import re

SIMILARITY_THRESHOLD = 0.75
VALUE_WINDOW = 3  # how many tokens after a test name to look for its value
FILLER_WORDS = {"count", "level"}  # words allowed between a name and its value
SKIP_IF_NEXT_WORD = {"volume"}  # "Mean Platelet Volume" is not "Platelets"
RANGE_TOLERANCE = 1.5  # a result may sit up to 50% outside the printed range

# (metric name, names OCR may produce, default unit, (min, max) plausible value)
LAB_TESTS = [
    # Red blood cell tests
    ("RBC", ["rbc"], "x10^6/uL", (2.0, 8.0)),
    ("Hemoglobin", ["hemoglobin", "haemoglobin"], "g/dL", (3.0, 25.0)),
    ("Hematocrit", ["hematocrit", "haematocrit"], "%", (20.0, 60.0)),
    ("MCV", ["mcv"], "fL", (50.0, 150.0)),
    ("MCH", ["mch"], "pg", (15.0, 45.0)),
    ("MCHC", ["mchc"], "g/dL", (25.0, 40.0)),
    # White blood cell tests
    ("WBC", ["wbc"], "x10³/uL", (0.5, 100.0)),
    ("Neutrophils", ["neutrophil", "neutrophils"], "%", (0.0, 100.0)),
    ("Lymphocytes", ["lymphocyte", "lymphocytes"], "%", (0.0, 100.0)),
    ("Eosinophils", ["eosinophil", "eosinophils"], "%", (0.0, 100.0)),
    ("Monocytes", ["monocyte", "monocytes"], "%", (0.0, 100.0)),
    ("Basophils", ["basophil", "basophils"], "%", (0.0, 100.0)),
    # Platelets
    ("Platelets", ["platelet", "platelets"], "x10³/uL", (10.0, 1500.0)),
]

# Splits text into words and numbers, such as "neutrophils", "13.80", "6"
TOKEN_PATTERN = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
NUMBER_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")


def _tokenize(ocr_text: str) -> list[str]:
    """Lowercases the text, turns commas into decimal points, and splits it into tokens."""
    normalized = ocr_text.lower().replace(",", ".")
    return TOKEN_PATTERN.findall(normalized)


def _is_name_match(token: str, name: str) -> bool:
    """
    Returns True if the token matches the test name.
    Short tokens or names must match exactly, so "mch" never matches "mchc".
    Longer names allow small spelling mistakes.
    """
    if len(token) <= 3 or len(name) <= 3:
        return token == name
    similarity = difflib.SequenceMatcher(None, token, name).ratio()
    return similarity >= SIMILARITY_THRESHOLD


def _value_index_after(tokens: list[str], name_index: int) -> int | None:
    """
    Returns the position of the result number after a test name, or None.
    Only filler words may appear before the number. Any other word stops the search.
    """
    for offset in range(1, VALUE_WINDOW + 1):
        position = name_index + offset
        if position >= len(tokens):
            break
        token = tokens[position]
        if token in FILLER_WORDS:
            continue
        if NUMBER_PATTERN.match(token):
            return position
        return None
    return None


def _reference_range_after(tokens: list[str], value_index: int) -> tuple[float, float] | None:
    """
    Returns the (low, high) normal range printed right after the result, or None.
    The report prints the range as two numbers, such as "20 -40".
    """
    numbers = []
    for token in tokens[value_index + 1 : value_index + 3]:
        if not NUMBER_PATTERN.match(token):
            break
        numbers.append(float(token))

    if len(numbers) != 2:
        return None
    low, high = sorted(numbers)
    return low, high


def _within_reference(value: float, reference: tuple[float, float]) -> bool:
    """
    Returns True if the value is close to the printed normal range.
    The tolerance allows slightly abnormal results, which are real.
    """
    low, high = reference
    return low / RANGE_TOLERANCE <= value <= high * RANGE_TOLERANCE


def _find_value(tokens: list[str], names: list[str], low: float, high: float) -> float | None:
    """Returns the first value that passes all checks for any of the test's names."""
    for index, token in enumerate(tokens):
        if not any(_is_name_match(token, name) for name in names):
            continue
        if index + 1 < len(tokens) and tokens[index + 1] in SKIP_IF_NEXT_WORD:
            continue

        value_index = _value_index_after(tokens, index)
        if value_index is None:
            continue

        value = float(tokens[value_index])
        if value == 0 or not low <= value <= high:
            continue

        reference = _reference_range_after(tokens, value_index)
        if reference is not None and not _within_reference(value, reference):
            continue

        return value
    return None


def extract_lab_values(ocr_text: str) -> list[dict]:
    """
    Returns one entry per known test found in the OCR text.
    Values are skipped when they are zero, outside the plausible range,
    or far outside the normal range printed next to them.
    """
    if not ocr_text:
        return []

    tokens = _tokenize(ocr_text)
    results = []
    for metric_name, names, unit, (low, high) in LAB_TESTS:
        value = _find_value(tokens, names, low, high)
        if value is not None:
            results.append({"metric_name": metric_name, "value": value, "unit": unit})
    return results