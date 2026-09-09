from app.services.llm_service import generate_medical_summary

sample_text = """
PATIENT: John Doe
TEST: Complete Blood Count (CBC)
Hemoglobin: 10.2 g/dL (Low - Normal range 13.5-17.5)
WBC: 11,200 /uL (High - Normal range 4,500-11,000)
Platelets: 250,000 /uL (Normal)
"""

summary = generate_medical_summary(sample_text)
print("Summary:")
print(summary)