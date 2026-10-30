from app.services.fuzzy_lab_parser import extract_lab_values
from app.services.health_extraction_service import extract_health_metrics

REPORT_SNIPPET = """Haemoglobin 13.80 Mcmatocrit M.50 MCV 80.30 L MCH 26.70 L Total WBC Count 6.71
Neutrophils 53.10 40 80 Lymphocytes 35.00 20 40 Eosinophils 1.90 Monocytes 9.10 Basophils 0.60
Platolet 265.00 150-410 Mean Platelet Volume 10.10 7.6 10.8"""


def values_by_name(results):
    return {item["metric_name"]: item["value"] for item in results}


def test_extracts_values_from_report_text():
    values = values_by_name(extract_lab_values(REPORT_SNIPPET))

    assert values["Hemoglobin"] == 13.8
    assert values["WBC"] == 6.71
    assert values["Neutrophils"] == 53.1
    assert values["Lymphocytes"] == 35.0
    assert values["Eosinophils"] == 1.9
    assert values["Monocytes"] == 9.1
    assert values["Basophils"] == 0.6
    assert values["Platelets"] == 265.0


def test_misspelled_names_are_matched():
    values = values_by_name(extract_lab_values("Hatmoglobia 13.80\nPlatolet 265.00"))

    assert values["Hemoglobin"] == 13.8
    assert values["Platelets"] == 265.0


def test_comma_decimal_is_read():
    values = values_by_name(extract_lab_values("Platelets 265,00"))

    assert values["Platelets"] == 265.0


def test_mean_platelet_volume_is_not_platelets():
    results = extract_lab_values("Mean Platelet Volume 10.10 7.6 10.8")

    assert "Platelets" not in values_by_name(results)


def test_implausible_value_is_skipped():
    # OCR misread 1.90 as 190. Percentages cannot be above 100.
    results = extract_lab_values("Eosinophils 190")

    assert "Eosinophils" not in values_by_name(results)


def test_empty_text_returns_empty_list():
    assert extract_lab_values("") == []
    assert extract_lab_values(None) == []


def test_regex_and_fuzzy_results_are_merged_without_duplicates():
    results = extract_health_metrics(REPORT_SNIPPET)
    names = [item["metric_name"] for item in results]

    assert "Hemoglobin" in names
    assert "Platelets" in names
    assert names.count("Hemoglobin") == 1

def test_mcv_mch_mchc_and_hematocrit_are_found():
    text = "Hematocrit 39.50 MCV 80.30 L MCH 26.70 L MCHC 33.30"
    values = values_by_name(extract_lab_values(text))

    assert values["Hematocrit"] == 39.5
    assert values["MCV"] == 80.3
    assert values["MCH"] == 26.7
    assert values["MCHC"] == 33.3

def test_lymphocytes_far_outside_printed_range_is_skipped():
    # OCR read 35.00 as 85.00. The printed range is 20 to 40.
    results = extract_lab_values("Lymphocytes 85.00 20 40")

    assert "Lymphocytes" not in values_by_name(results)


def test_hematocrit_with_garbled_value_is_skipped():
    # "M.50" is not a clean number, so the 50 must not be used.
    results = extract_lab_values("Mcmatocrit M.50 MCV 80.30 L")

    assert "Hematocrit" not in values_by_name(results)


def test_zero_value_is_skipped():
    results = extract_lab_values("Basophils 0 2")

    assert "Basophils" not in values_by_name(results)


def test_large_monocyte_misread_is_skipped():
    # OCR read 9.10 as 940.
    results = extract_lab_values("Monocytes 940 10")

    assert "Monocytes" not in values_by_name(results)


def test_result_inside_printed_range_is_kept():
    values = values_by_name(extract_lab_values("Neutrophils 53.10 10 80"))

    assert values["Neutrophils"] == 53.1