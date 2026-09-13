import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


def _sanitize_text(text: str) -> str:
    """
    Replaces 'smart' Unicode punctuation (often produced by LLMs) with
    plain ASCII equivalents. ReportLab's default fonts can render these
    incorrectly as garbled characters otherwise.
    """
    replacements = {
        "\u2013": "-",    # en dash
        "\u2014": "--",   # em dash
        "\u2011": "-",    # non-breaking hyphen
        "\u2012": "-",    # figure dash
        "\u2015": "--",   # horizontal bar
        "\u2018": "'",    # left single quote
        "\u2019": "'",    # right single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2044": "/",    # fraction slash
        "\u2212": "-",    # minus sign
        "\u2264": "<=",   # less-than-or-equal
        "\u2265": ">=",   # greater-than-or-equal
        "\u00a0": " ",    # non-breaking space
    }
    for bad_char, good_char in replacements.items():
        text = text.replace(bad_char, good_char)
    return text

def build_discharge_pdf(patient_name: str, patient_email: str, summary_text: str) -> str:
    """
    Builds a PDF from the AI-generated discharge summary text.
    Returns the path to the generated PDF (saved to a temp file).
    """
    summary_text = _sanitize_text(summary_text)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tmp_file.name
    tmp_file.close()

    doc = SimpleDocTemplate(
        tmp_path,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1B2B29")
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"], textColor=colors.HexColor("#2F6F5E"),
        spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle", parent=styles["Normal"], fontSize=10.5, leading=15,
    )
    disclaimer_style = ParagraphStyle(
        "DisclaimerStyle", parent=styles["Normal"], fontSize=8.5,
        textColor=colors.HexColor("#5B6E68"), leading=12,
    )

    story = []

    story.append(Paragraph("HealthCura Health Summary", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Patient: {patient_name}", body_style))
    story.append(Paragraph(f"Email: {patient_email}", body_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>This is an AI-generated reference summary based on your uploaded documents. "
        "It is NOT an official medical discharge summary and has not been reviewed by a "
        "physician. Always consult your doctor for medical decisions.</b>",
        disclaimer_style,
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#DDE5E1")))
    story.append(Spacer(1, 10))

    known_sections = ["Overview", "Key Findings", "Current Status", "Follow-up Notes", "Follow-up"]

    for line in summary_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        line = line.lstrip("#").strip()
        line = line.replace("**", "").replace("*", "")
        line = line.replace("|", " ")
        if set(line) <= {"-", " "}:
            continue

        stripped_line = line.strip("0123456789. ")
        is_section_header = any(stripped_line.startswith(s) for s in known_sections)

        if is_section_header:
            story.append(Paragraph(stripped_line, heading_style))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)
    return tmp_path