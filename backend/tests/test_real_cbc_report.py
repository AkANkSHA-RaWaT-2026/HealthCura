from datetime import date

from app.services.blood_report_parser import extract_report_date, parse_blood_report

CBC_TEXT = """City Diagnostics Pathology Laboratory
Report Date : 25-May-2024 10:30 AM
Sample Collected : 24-May-2024 08:45 AM
Complete Blood Count (CBC)
Hemoglobin (Hb) 17.2 g/dL 13.0 - 17.0 HIGH
Total Leucocyte Count (TLC) 4,200 cells / µL 4,000 - 11,000 LOW
Red Blood Cell Count (RBC) 5.85 million / µL 4.50 - 5.50 Normal
Hematocrit (HCT) 51.6 % 40.0 - 50.0 HIGH
Mean Corpuscular Volume (MCV) 88.2 fL 80.0 - 100.0 Normal
Mean Corpuscular Hemoglobin (MCH) 29.4 pg 27.0 - 33.0 Normal
Mean Corpuscular Hemoglobin Conc. (MCHC) 33.3 g/dL 32.0 - 36.0 Normal
Red Cell Distribution Width (RDW-CV) 14.8 % 11.5 - 14.5 HIGH
Platelet Count 1,32,000 cells / µL 1,50,000 - 4,50,000 LOW
Mean Platelet Volume (MPV) 7.8 fL 8.5 - 12.0 LOW"""


def rows_by_name(result):
    return {row["metric_name"]: row for row in result["rows"]}


def test_hemoglobin_abbreviation_is_read_and_flagged_high():
    row = rows_by_name(parse_blood_report(CBC_TEXT))["Hemoglobin"]

    assert row["value"] == 17.2
    assert row["unit"] == "g/dL"
    assert row["printed_low"] == 13.0
    assert row["printed_high"] == 17.0
    assert row["status"] == "high"


def test_hematocrit_abbreviation_is_read_and_flagged_high():
    row = rows_by_name(parse_blood_report(CBC_TEXT))["Hematocrit"]

    assert row["value"] == 51.6
    assert row["status"] == "high"


def test_wbc_comma_thousands_is_converted_to_x10_3():
    row = rows_by_name(parse_blood_report(CBC_TEXT))["WBC"]

    assert row["value"] == 4.2
    assert row["unit"] == "x10^3/uL"
    assert row["printed_low"] == 4.0
    assert row["printed_high"] == 11.0


def test_wbc_status_follows_printed_range_not_report_flag():
    # The report prints LOW, but 4,200 is inside its own range of 4,000 to 11,000.
    # The app computes status from the range, and the report flag is not used.
    row = rows_by_name(parse_blood_report(CBC_TEXT))["WBC"]

    assert row["status"] == "normal"


def test_platelets_indian_thousands_is_converted():
    row = rows_by_name(parse_blood_report(CBC_TEXT))["Platelets"]

    assert row["value"] == 132.0
    assert row["printed_low"] == 150.0
    assert row["printed_high"] == 450.0
    assert row["status"] == "low"


def test_mean_platelet_volume_is_not_read_as_platelets():
    rows = rows_by_name(parse_blood_report(CBC_TEXT))

    assert rows["Platelets"]["value"] == 132.0


def test_only_supported_metrics_are_saved():
    names = set(rows_by_name(parse_blood_report(CBC_TEXT)))

    assert names == {"Hemoglobin", "Hematocrit", "RBC", "WBC", "Platelets"}


def test_rbc_value_and_unit_are_read():
    row = rows_by_name(parse_blood_report(CBC_TEXT))["RBC"]

    assert row["value"] == 5.85
    assert row["unit"] == "x10^6/uL"


def test_document_is_classified_as_blood_test_report():
    assert parse_blood_report(CBC_TEXT)["document_type"] == "Blood Test Report"


def test_report_date_prefers_the_report_date_label():
    assert extract_report_date(CBC_TEXT) == date(2024, 5, 25)


def test_month_name_date_is_read():
    assert extract_report_date("Date 07 Nov 2021") == date(2021, 11, 7)