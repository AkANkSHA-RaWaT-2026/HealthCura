"""Supported blood test metrics, their reference ranges, and status logic.

This is the single source of truth for which tests HealthCura reads.
Standard ranges are used only when the report does not print its own range.
"""

from dataclasses import dataclass

CBC = "Complete Blood Count (CBC)"
LIPID = "Lipid Profile"
BMP = "Kidney and Electrolytes (BMP)"


@dataclass(frozen=True)
class MetricDefinition:
    """One supported test and the rules used to read it from OCR text."""

    name: str
    panel: str
    unit: str
    aliases: tuple[str, ...]  # lowercase spellings OCR may produce, including abbreviations
    standard_range: tuple[float | None, float | None]  # None means open-ended
    plausible_range: tuple[float, float]  # values outside this are OCR errors
    excluded_previous: tuple[str, ...] = ()  # words that must not come right before


METRICS = (
    MetricDefinition(
        "Hemoglobin", CBC, "g/dL",
        ("hemoglobin", "haemoglobin", "hb", "hgb"),
        (13.0, 17.0), (3.0, 25.0),
    ),
    MetricDefinition(
        "Hematocrit", CBC, "%",
        ("hematocrit", "haematocrit", "hct", "pcv"),
        (38.0, 50.0), (15.0, 65.0),
    ),
    MetricDefinition("RBC", CBC, "x10^6/uL", ("rbc",), (4.5, 5.9), (1.0, 10.0)),
    MetricDefinition(
        "WBC", CBC, "x10^3/uL",
        ("wbc", "tlc", "leucocyte", "leukocyte"),
        (4.0, 10.5), (0.5, 100.0),
    ),
    MetricDefinition(
        "Platelets", CBC, "x10^3/uL",
        ("platelet", "platelets"),
        (150.0, 450.0), (10.0, 1500.0),
    ),
    MetricDefinition(
        "Total Cholesterol", LIPID, "mg/dL", ("cholesterol",), (None, 200.0), (50.0, 600.0),
        excluded_previous=("hdl", "ldl"),
    ),
    MetricDefinition("HDL Cholesterol", LIPID, "mg/dL", ("hdl",), (40.0, None), (5.0, 150.0)),
    MetricDefinition("LDL Cholesterol", LIPID, "mg/dL", ("ldl",), (None, 130.0), (5.0, 400.0)),
    MetricDefinition(
        "Triglycerides", LIPID, "mg/dL", ("triglycerides", "triglyceride"), (None, 130.0), (10.0, 2000.0)
    ),
    MetricDefinition("Glucose", BMP, "mg/dL", ("glucose",), (70.0, 99.0), (20.0, 600.0)),
    MetricDefinition("BUN", BMP, "mg/dL", ("bun", "urea"), (7.0, 20.0), (1.0, 200.0)),
    MetricDefinition("Creatinine", BMP, "mg/dL", ("creatinine",), (0.6, 1.3), (0.1, 20.0)),
    MetricDefinition("Sodium", BMP, "mmol/L", ("sodium",), (135.0, 145.0), (100.0, 180.0)),
    MetricDefinition("Potassium", BMP, "mmol/L", ("potassium",), (3.5, 5.1), (1.0, 10.0)),
)

METRICS_BY_NAME = {metric.name: metric for metric in METRICS}


def printed_range_matches_standard(metric: MetricDefinition, printed_range) -> bool:
    """
    Returns True if the printed range is close to the standard range.
    OCR often garbles ranges, so a range far from the standard one is ignored.
    """
    if printed_range is None:
        return False

    for printed_side, standard_side in zip(printed_range, metric.standard_range):
        if printed_side is None or standard_side is None:
            continue
        allowed_difference = 0.5 * max(abs(standard_side), 1.0)
        if abs(printed_side - standard_side) > allowed_difference:
            return False
    return True


def get_status(metric_name: str, value: float, printed_range=None) -> str:
    """
    Returns "low", "high", "normal", or "unknown".
    The range printed on the report is used when present, otherwise the standard range.
    """
    metric = METRICS_BY_NAME.get(metric_name)
    if metric is None:
        return "unknown"

    low, high = printed_range if printed_range else metric.standard_range
    if low is not None and value < low:
        return "low"
    if high is not None and value > high:
        return "high"
    return "normal"