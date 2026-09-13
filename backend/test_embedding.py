from app.services.embedding_service import chunk_text, embed_texts

sample_text = """
Patient: John Doe
Glucose: 95 mg/dL (Normal)
Hemoglobin: 13.5 g/dL (Normal)
The patient shows no signs of anemia or diabetes based on these results.
Doctor recommends a follow-up in 6 months.
""" * 5  # repeated to make it long enough to actually split into multiple chunks

chunks = chunk_text(sample_text)
print(f"Split into {len(chunks)} chunks")

embeddings = embed_texts(chunks)
print(f"Generated {len(embeddings)} embeddings, each with {len(embeddings[0])} dimensions")