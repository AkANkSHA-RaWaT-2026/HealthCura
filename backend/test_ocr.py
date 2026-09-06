from app.services.ocr_service import extract_text_from_image_path

text = extract_text_from_image_path("test_sample.jpg")
print("Extracted text:")
print(text)