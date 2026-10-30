"""Removes Markdown symbols from AI-generated text so the app shows plain text."""

import re

HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
BULLET_PATTERN = re.compile(r"^\s*\*\s+", re.MULTILINE)


def clean_markdown(text: str | None) -> str:
    """
    Returns the text with Markdown headings, bold markers, and backticks removed.
    Bullet stars become dashes. Returns an empty string for None or empty input.
    """
    if not text:
        return ""

    cleaned = HEADING_PATTERN.sub("", text)
    cleaned = BOLD_PATTERN.sub(r"\1", cleaned)
    # Removes any leftover ** that the bold pattern did not match
    cleaned = cleaned.replace("**", "")
    cleaned = BULLET_PATTERN.sub("- ", cleaned)
    cleaned = cleaned.replace("`", "")

    return cleaned.strip()