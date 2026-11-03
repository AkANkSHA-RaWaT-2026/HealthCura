from app.services.summary_service import (
    build_facts,
    build_flagged,
    build_template_summary,
    check_ai_summary,
    count_sentences,
    create_summary,
)

ROWS = [
    {"metric_name": "Hemoglobin", "value": 13.8, "unit": "g/dL", "status": "normal",
     "printed_low": None, "printed_high": None},
    {"metric_name": "Platelets", "value": 265.0, "unit": "x10^3/uL", "status": "normal",
     "printed_low": 150.0, "printed_high": 410.0},
    {"metric_name": "RBC", "value": 6.17, "unit": "x10^6/uL", "status": "high",
     "printed_low": None, "printed_high": None},
    {"metric_name": "LDL Cholesterol", "value": 145.0, "unit": "mg/dL", "status": "high",
     "printed_low": 0.0, "printed_high": 130.0},
]

VALID_AI_TEXT = (
    "This blood test report includes 4 results. Hemoglobin was 13.8 g/dL, within the "
    "reference range of 13 to 17. LDL Cholesterol was 145 mg/dL, above the reference "
    "range of 0 to 130."
)


def test_flagged_list_is_built_from_rows():
    flagged = build_flagged(ROWS)

    assert any("LDL Cholesterol was 145 mg/dL, above the reference range of 0 to 130" in f for f in flagged)
    assert any("RBC was 6.17 x10^6/uL, above the reference range of 4.5 to 5.9 (standard range)" in f for f in flagged)
    assert not any("Hemoglobin" in f for f in flagged)


def test_facts_include_every_stored_value():
    facts = build_facts(ROWS)

    assert len(facts) == 4
    assert "Hemoglobin: 13.8 g/dL" in facts[0]


def test_valid_ai_text_is_accepted():
    assert check_ai_summary(VALID_AI_TEXT, ROWS) is None


def test_number_not_in_data_is_rejected():
    text = "This blood test report includes 4 results. Hemoglobin was 14.2 g/dL, within the reference range of 13 to 17."

    assert "not in the data" in check_ai_summary(text, ROWS)


def test_advice_wording_is_rejected():
    text = "You should consult your doctor about the LDL result. Hemoglobin was 13.8 g/dL."

    assert check_ai_summary(text, ROWS) == "contains interpretation or advice"


def test_too_many_sentences_are_rejected():
    text = " ".join(["Hemoglobin was 13.8 g/dL."] * 6)

    assert "sentences" in check_ai_summary(text, ROWS)


def test_decimal_point_does_not_count_as_sentence_end():
    assert count_sentences("Hemoglobin was 13.8 g/dL. RBC was 6.17.") == 2


def test_valid_ai_text_is_used_and_marked_ai():
    result = create_summary(ROWS, "Blood Test Report", writer=lambda facts: VALID_AI_TEXT)

    assert result["summary_source"] == "ai"
    assert result["summary"] == VALID_AI_TEXT


def test_rejected_ai_text_falls_back_to_template():
    bad_text = "You should consult your doctor. Hemoglobin was 99 g/dL."
    result = create_summary(ROWS, "Blood Test Report", writer=lambda facts: bad_text)

    assert result["summary_source"] == "template"
    assert "includes 4 supported results" in result["summary"]


def test_writer_failure_falls_back_to_template():
    def broken_writer(facts):
        raise RuntimeError("Groq is unavailable")

    result = create_summary(ROWS, "Blood Test Report", writer=broken_writer)

    assert result["summary_source"] == "template"
    assert "includes 4 supported results" in result["summary"]


def test_flagged_list_is_same_regardless_of_writer():
    with_ai = create_summary(ROWS, "Blood Test Report", writer=lambda facts: VALID_AI_TEXT)
    without_ai = create_summary(ROWS, "Blood Test Report", writer=lambda facts: "Bad. Text 999.")

    assert with_ai["flagged"] == without_ai["flagged"]


def test_other_document_gets_no_flags_and_no_model_call():
    calls = []

    def writer(facts):
        calls.append(facts)
        return VALID_AI_TEXT

    result = create_summary([], "Other", writer=writer)

    assert result["document_type"] == "Other"
    assert result["flagged"] == []
    assert calls == []


def test_blood_type_without_rows_is_treated_as_other():
    result = create_summary([], "Blood Test Report")

    assert result["document_type"] == "Other"


def test_disclaimer_is_always_present():
    result = create_summary(ROWS, "Blood Test Report", writer=lambda facts: VALID_AI_TEXT)

    assert "not a diagnosis" in result["disclaimer"]


def test_template_summary_states_flag_count():
    text = build_template_summary(ROWS)

    assert "2 results are outside the reference range" in text