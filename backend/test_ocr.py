from app.services.ocr_service import extract_text_from_image_path

text = extract_text_from_image_path("1.png")
print("Extracted text:")
print(text)