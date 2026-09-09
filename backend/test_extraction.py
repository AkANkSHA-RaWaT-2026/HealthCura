from app.services.health_extraction_service import extract_health_metrics

sample_text = """
PATIENT: John Doe
Date: 15/03/2026
TEST: Complete Blood Count (CBC)
Glucose: 110 mg/dL
Hemoglobin: 10.2 g/dL
BP: 120/80 mmHg
"""

results = extract_health_metrics(sample_text)
for r in results:
    print(r)