from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HealthCura API",
    description="Medical Document Intelligence System - Backend API",
    version="0.1.0"
)

# Allows the React dev server (different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "HealthCura API is running", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}