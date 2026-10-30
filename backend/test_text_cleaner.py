from app.services.text_cleaner import clean_markdown


def test_removes_bold_markers():
    text = "**Plain-language summary** John Doe's blood test is normal."
    assert clean_markdown(text) == "Plain-language summary John Doe's blood test is normal."


def test_keeps_value_inside_bold():
    assert clean_markdown("Your glucose is **102 mg/dL**.") == "Your glucose is 102 mg/dL."


def test_removes_heading_hashes():
    assert clean_markdown("## Overview\nAll good.") == "Overview\nAll good."


def test_turns_star_bullets_into_dashes():
    assert clean_markdown("* Glucose is high\n* Cholesterol is fine") == (
        "- Glucose is high\n- Cholesterol is fine"
    )


def test_plain_text_is_unchanged():
    text = "The report shows normal values."
    assert clean_markdown(text) == text


def test_removes_stray_double_stars():
    assert clean_markdown("Result **: normal") == "Result : normal"


def test_empty_and_none_return_empty_string():
    assert clean_markdown("") == ""
    assert clean_markdown(None) == ""


def test_quotes_are_kept():
    text = "The doctor says: \u201cRepeat test in 3 months.\u201d"
    assert clean_markdown(text) == text