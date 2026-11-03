from app.services.summary_service import check_ai_summary

ROWS = [
    {"metric_name": "WBC", "value": 6.71, "unit": "x10^3/uL", "status": "normal",
     "printed_low": None, "printed_high": None},
    {"metric_name": "Hemoglobin", "value": 13.8, "unit": "g/dL", "status": "normal",
     "printed_low": None, "printed_high": None},
]


def test_unit_exponent_is_not_treated_as_a_number():
    text = (
        "This blood test report includes 2 supported results. "
        "WBC was 6.71 x10^3/uL, within the reference range of 4 to 10.5. "
        "Hemoglobin was 13.8 g/dL, within the reference range of 13 to 17."
    )
    assert check_ai_summary(text, ROWS) is None


def test_made_up_value_is_still_rejected():
    text = (
        "This blood test report includes 2 supported results. "
        "WBC was 9.9 x10^3/uL, within the reference range of 4 to 10.5. "
        "Hemoglobin was 13.8 g/dL, within the reference range of 13 to 17."
    )
    assert "not in the data" in check_ai_summary(text, ROWS)