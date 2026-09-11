# (low, high, normal)reference range for each metric we extract.
# Ranges are general adult reference values - not patient-specific
# (age/sex-adjusted ranges are a known simplification for this MVP).
REFERENCE_RANGES = {
    "Glucose": (70, 99),
    "Hemoglobin": (13.0, 17.0),
    "Total Cholesterol": (0, 200),
    "HDL Cholesterol": (40, 999),   # higher is better - only a lower bound matters
    "LDL Cholesterol": (0, 130),
    "Triglycerides": (0, 130),
    "WBC": (4.0, 10.5),
    "RBC": (4.5, 5.9),
    "Hematocrit": (38, 50),
    "Platelets": (150, 450),
    "BUN": (7, 20),
    "Creatinine": (0.6, 1.3),
    "Sodium": (135, 145),
    "Potassium": (3.5, 5.1),
    "Blood Pressure Systolic": (90, 120),
    "Blood Pressure Diastolic": (60, 80),
    "Heart Rate": (60, 100),
}


def get_status(metric_name: str, value: float) -> str:
    """
    Returns 'low', 'high', or 'normal' based on the metric's reference range.
    Returns 'unknown' if we don't have a defined range for this metric.
    """
    range_pair = REFERENCE_RANGES.get(metric_name)
    if not range_pair:
        return "unknown"

    low, high = range_pair
    if value < low:
        return "low"
    elif value > high:
        return "high"
    return "normal"