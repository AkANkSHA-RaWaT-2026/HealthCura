import os

import cv2
import numpy as np
import easyocr
from dotenv import load_dotenv

load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH")
ENLARGE_FACTOR = 2

# EasyOCR loads its model into memory once, so the reader is created on first use
_reader = None


def get_reader() -> easyocr.Reader:
    """Creates the EasyOCR reader on first use, then reuses it."""
    global _reader
    if _reader is None:
        # English-only mode, because mixed languages reduced accuracy on English reports
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Prepares a photo or scanned page for OCR.
    Enlarging the image makes small table text easier to read.
    Adaptive thresholding removes uneven background shading.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    enlarged = cv2.resize(
        gray, None, fx=ENLARGE_FACTOR, fy=ENLARGE_FACTOR, interpolation=cv2.INTER_CUBIC
    )
    return cv2.adaptiveThreshold(
        enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )


def extract_text_from_image_path(image_path: str) -> str:
    """Runs OCR on an image file and returns the text, one row per line."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to read image file.")

    processed = preprocess_image(image)
    reader = get_reader()
    # paragraph=True keeps words from the same table row together
    results = reader.readtext(processed, detail=0, paragraph=True)
    return "\n".join(results)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Converts each PDF page to an image, then runs OCR on each page."""
    from pdf2image import convert_from_path

    pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    reader = get_reader()
    all_text = []

    for page_image in pages:
        page_array = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2BGR)
        processed = preprocess_image(page_array)
        results = reader.readtext(processed, detail=0, paragraph=True)
        all_text.append("\n".join(results))

    return "\n\n".join(all_text)