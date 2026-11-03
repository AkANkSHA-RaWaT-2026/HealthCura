"""Reads text from lab report images and PDFs using EasyOCR.

Each image is read at two enlargement sizes. The reading that recovers the
most known test names and decimal numbers is kept.
"""

import os
import re

import cv2
import numpy as np
import easyocr
from dotenv import load_dotenv

load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH")
IMAGE_SCALES = (2, 3)  # enlargement factors tried for each image

KNOWN_TERMS = {
    "hemoglobin", "hb", "hematocrit", "hct", "rbc", "wbc", "platelet", "platelets",
    "mcv", "mch", "mchc", "neutrophils", "lymphocytes", "monocytes", "eosinophils",
    "basophils", "cholesterol", "triglycerides", "glucose", "creatinine", "sodium",
    "potassium", "urea", "tlc",
}

# EasyOCR loads its model into memory once, so the reader is created on first use
_reader = None


def get_reader() -> easyocr.Reader:
    """Creates the EasyOCR reader on first use, then reuses it."""
    global _reader
    if _reader is None:
        # English-only mode, because mixed languages reduced accuracy on English reports
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def enlarge_and_threshold(gray: np.ndarray, scale: int) -> np.ndarray:
    """
    Enlarges a grayscale image, then applies adaptive thresholding.
    Enlarging helps small table text. Thresholding removes uneven background shading.
    """
    enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return cv2.adaptiveThreshold(
        enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )


def score_text(text: str) -> tuple[int, int]:
    """Returns (known test names found, decimal numbers found). Used to pick the best reading."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    terms = len(KNOWN_TERMS & words)
    decimals = len(re.findall(r"\d+\.\d+", text))
    return terms, decimals


def read_best_text(gray: np.ndarray) -> str:
    """Runs OCR at each candidate scale and returns the reading with the best score."""
    reader = get_reader()
    best_text = ""
    best_score = (-1, -1)

    for scale in IMAGE_SCALES:
        processed = enlarge_and_threshold(gray, scale)
        # paragraph=True keeps words from the same table row together
        text = "\n".join(reader.readtext(processed, detail=0, paragraph=True))
        score = score_text(text)
        if score > best_score:
            best_score = score
            best_text = text

    return best_text


def extract_text_from_image_path(image_path: str) -> str:
    """Runs OCR on an image file and returns the best reading, one row per line."""
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError("Unable to read image file.")
    return read_best_text(gray)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Converts each PDF page to an image, then runs OCR on each page."""
    from pdf2image import convert_from_path

    pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    all_text = []

    for page_image in pages:
        gray = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2GRAY)
        all_text.append(read_best_text(gray))

    return "\n\n".join(all_text)