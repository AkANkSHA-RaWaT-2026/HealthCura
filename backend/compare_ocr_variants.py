"""Runs OCR on three versions of a lab report image and saves each result.

Manual check only. Run it, then open the saved text files and compare them.
"""

import cv2

from app.services.ocr_service import get_reader

IMAGE_PATH = "1.png"


def load_grayscale(path: str):
    """Loads the image in grayscale. Raises ValueError if the file can't be read."""
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def make_variants(gray):
    """Returns a dict of image versions to test, keyed by a short name."""
    enlarged = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    cleaned = cv2.adaptiveThreshold(
        enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    return {
        "original": gray,
        "enlarged": enlarged,
        "enlarged_cleaned": cleaned,
    }


def run_ocr_variants() -> None:
    """Runs OCR on each variant and writes the text to ocr_<name>.txt."""
    reader = get_reader()
    gray = load_grayscale(IMAGE_PATH)

    for name, image in make_variants(gray).items():
        # paragraph=True keeps words from the same row together
        lines = reader.readtext(image, detail=0, paragraph=True)
        output_file = f"ocr_{name}.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))
        print(f"Saved {output_file} ({len(lines)} lines)")


if __name__ == "__main__":
    run_ocr_variants()