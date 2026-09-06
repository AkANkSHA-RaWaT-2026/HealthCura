# backend/app/services/ocr_service.py
import os
import cv2
import numpy as np
import easyocr
from dotenv import load_dotenv

load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH")

# EasyOCR loads its model into memory once, on first use - keep a single
# global instance so we don't reload it on every request (slow + wasteful)
_reader = None


def get_reader() -> easyocr.Reader:
    """Lazily loads the EasyOCR reader once, then reuses it."""
    global _reader
    if _reader is None:
        # English-only mode - per project findings, multilingual mode
        # caused accuracy issues on English medical documents
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Grayscale + denoise + threshold - improves accuracy on phone photos."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresholded = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresholded


def extract_text_from_image_path(image_path: str) -> str:
    """Runs OCR on an image file and returns extracted text."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to read image file.")

    processed = preprocess_image(image)
    reader = get_reader()
    results = reader.readtext(processed, detail=0)  # detail=0 returns just text strings
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
        results = reader.readtext(processed, detail=0)
        all_text.append("\n".join(results))

    return "\n\n".join(all_text)