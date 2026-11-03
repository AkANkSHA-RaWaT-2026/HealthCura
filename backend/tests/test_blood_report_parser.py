from datetime import date

from app.services.blood_report_parser import (
    extract_lab_name,
    extract_panel_name,
    extract_report_date,
    parse_blood_report,
)
from app.services.reference_ranges import CBC, LIPID, BMP

# Real lines from the enlarged OCR output of the Aster Clinic report
REAL_SNIPPET = """Haemoglobin 13.80 Mcmatocrit M.50 MCV 80.30 L MCH 26.70 L MCHC 33.30
Red Coll DIstributlon Wldth 12.20 Total WBC Count 6.71
Platolet 265.00 150-410 10^3lul Mean Platelet Volune 10.10 7.6 10.8"""


def rows_by_name(result):
    return {row["metric_name"]: row for row in result["rows"]}


def test_real_snippet_reads_hemoglobin_wbc_and_platelets():
    rows = rows_by_name(parse_blood_report(REAL_SNIPPET))

    assert rows["Hemoglobin"]["value"] == 13.8
    assert rows["WBC"]["value"] == 6.71
    assert rows["Platelets"]["value"] == 265.0


def test_real_snippet_skips_garbled_hematocrit():
    rows = rows_by_name(parse_blood_report(REAL_SNIPPET))

    assert "Hematocrit" not in rows


def test_real_snippet_skips_mean_platelet_volume():
    result = parse_blood_report("Mean Platelet Volume 10.10 7.6 10.8")

    assert result["rows"] == []


def test_misspelled_hemoglobin_is_matched():
    rows = rows_by_name(parse_blood_report("Hatmoglobia 13.80"))

    assert rows["Hemoglobin"]["value"] == 13.8


def test_ldl_reads_printed_range_and_flags_high():
    row = rows_by_name(parse_blood_report("LDL Cholesterol 145 0 130 mg/dL"))["LDL Cholesterol"]

    assert row["value"] == 145.0
    assert row["printed_low"] == 0.0
    assert row["printed_high"] == 130.0
    assert row["status"] == "high"


def test_hdl_is_not_read_as_total_cholesterol():
    rows = rows_by_name(parse_blood_report("HDL Cholesterol 45 40 60 mg/dL"))

    assert "Total Cholesterol" not in rows
    assert rows["HDL Cholesterol"]["value"] == 45.0
    assert rows["HDL Cholesterol"]["status"] == "normal"


def test_total_cholesterol_is_read_on_its_own_line():
    row = rows_by_name(parse_blood_report("Total Cholesterol 185 0 200 mg/dL"))["Total Cholesterol"]

    assert row["value"] == 185.0
    assert row["status"] == "normal"


def test_glucose_below_printed_range_flags_low():
    row = rows_by_name(parse_blood_report("Glucose 65 70 99 mg/dL"))["Glucose"]

    assert row["value"] == 65.0
    assert row["status"] == "low"


def test_zero_value_is_skipped():
    rows = rows_by_name(parse_blood_report("Glucose 0 70 99 mg/dL"))

    assert "Glucose" not in rows


def test_value_far_outside_printed_range_is_skipped():
    # 300 is above the printed range of 0 to 130 by more than the tolerance
    rows = rows_by_name(parse_blood_report("LDL Cholesterol 300 0 130 mg/dL"))

    assert "LDL Cholesterol" not in rows


def test_misprinted_range_is_ignored_and_standard_range_used():
    # "4 13.17" does not match the standard Hemoglobin range of 13 to 17
    row = rows_by_name(parse_blood_report("Hemoglobin 13.8 4 13.17"))["Hemoglobin"]

    assert row["value"] == 13.8
    assert row["printed_low"] is None
    assert row["status"] == "normal"


def test_implausible_value_is_skipped():
    rows = rows_by_name(parse_blood_report("Platelets 2650"))

    assert "Platelets" not in rows


def test_unsupported_metrics_are_ignored():
    result = parse_blood_report("MCV 80.30 L MCH 26.70 L")

    assert result["rows"] == []
    assert result["document_type"] == "Other"


def test_date_with_missing_slash_is_read_correctly():
    assert extract_report_date("Collected 07/1122021 13:08") == date(2021, 11, 7)


def test_date_in_standard_format_is_read_correctly():
    assert extract_report_date("Reported 07/11/2021") == date(2021, 11, 7)


def test_invalid_date_returns_none():
    assert extract_report_date("Code 32/13/2021") is None


def test_blood_report_is_classified_as_blood_test_report():
    result = parse_blood_report("Haemoglobin 13.80")

    assert result["document_type"] == "Blood Test Report"


def test_other_document_has_no_rows():
    result = parse_blood_report("Electricity bill amount 500")

    assert result["document_type"] == "Other"
    assert result["rows"] == []


def test_panel_names_are_detected():
    assert extract_panel_name("CBC Complete Blood Count") == CBC
    assert extract_panel_name("Lipid Profile") == LIPID
    assert extract_panel_name("Renal function") == BMP
    assert extract_panel_name("Nothing here") is None


def test_lab_name_is_detected():
    assert extract_lab_name("Aster Clinic Fujairah") == "Aster Clinic"


def test_department_heading_is_not_used_as_lab_name():
    assert extract_lab_name("DEPARTMENT Of LABORATORY") is None


def test_empty_text_returns_other_with_no_rows():
    result = parse_blood_report("")

    assert result["document_type"] == "Other"
    assert result["rows"] == []

def test_word_containing_clinic_is_not_a_lab_name():
    assert extract_lab_name("Correlate Clinically as all results") is None