from datetime import date

from app.services.blood_report_parser import extract_report_date


def test_city_report_misspelled_label_and_ocr_month_is_read():
    text = (
        "LABORATORY REPORT\n"
        "1b No Repor Date Anpla Collested Samplc Rcccrvad 0epor Slalui\n"
        "(C94/24/05/28759 25 Vsy 2024 10.30 AM"
    )
    assert extract_report_date(text) == date(2024, 5, 25)


def test_aster_report_misspelled_label_is_read():
    text = (
        "Ordercd Op Collocfed On Rccehrd On Cherakkarakuzhfyll Rcported On\n"
        "07/1122021 13:08 07/1102021 13;38 07n1/20zi 17.27"
    )
    assert extract_report_date(text) == date(2021, 11, 7)


def test_date_after_clean_report_label_is_used_over_earlier_date():
    text = "Collected 01-01-2024\nRepor Date 25-May-2024"
    assert extract_report_date(text) == date(2024, 5, 25)


def test_misspelled_rcported_label_is_used_over_earlier_date():
    # Without the label match, the earlier collection date would be returned
    text = "Collected 01-01-2020\nRcported On 07/11/2021"
    assert extract_report_date(text) == date(2021, 11, 7)