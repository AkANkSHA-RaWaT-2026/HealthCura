from sqlalchemy import inspect

from app.models.document import Document
from app.models.health_record import HealthRecord


def column_names(model):
    return {column.name for column in inspect(model).columns}


def test_document_has_blood_report_header_fields():
    columns = column_names(Document)

    assert {"report_date", "lab_name", "panel_name", "document_type", "ocr_status"} <= columns


def test_health_record_has_panel_and_printed_range_fields():
    columns = column_names(HealthRecord)

    assert {"panel", "printed_low", "printed_high", "status", "recorded_date"} <= columns