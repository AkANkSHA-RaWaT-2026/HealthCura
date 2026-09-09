from app.services.health_extraction_service import extract_health_metrics

# Exact OCR text from your real document upload
sample_text = """Made with Al
MEDICAL LABORATORY REPORT
Medical Center;
Patient Name: John Doe
1234 Health
Suite 200
Date of Birth: 05/15/1975
Anytown; USA 12345
Patient ID: 567890
Phone: (555) 123-4567
Date: 01/10/2022
LAB RESULTS
TEST
RESULT
REFERENCE RANGE
Glucose
95 mg/dl
70-99 mg/dL
Hemoglobin
13.5 g/dl
13.0-17.0 gdL
Cholesterol
185 mg/dL
200 mg/dL
Blood Urea Nitrogen
14 mg/dl
7-20 mg/dL
White Blood Cell Count
6.8 x10?/uL
4.0-10.5 x1O /uL
TSH (Thyroid Stimulating Hormone)
2.1 ulU/mL
0.4-4.0 ulU/mL
Doctor: Dr: Emily Carter
Notes:
Normal lab findings, No abnormalities detected."""

results = extract_health_metrics(sample_text)
for r in results:
    print(r)

print("\n--- Debugging individual patterns ---")
import re
print("Glucose search:", re.search(r"glucose\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dl|mg%)?", sample_text, re.IGNORECASE))
print("Hemoglobin search:", re.search(r"h(?:a)?emoglobin\s*[:\-]?\s*(\d+\.?\d*)\s*(g/dl)?", sample_text, re.IGNORECASE))