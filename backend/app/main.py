from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import shutil

# Import System Architecture Schemas (Person A's Contract)
from app.schemas.scan import ScanResponse

# Import Intelligence Services (Your Work as Person B)
from app.services.ocr_service import extract_text_from_image
from app.services.ai_service import analyze_text_with_ai

# Initialize the FastAPI Application
app = FastAPI(title="ScamShield API", version="1.0.0")

# Configure CORS for Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins during development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],
)

@app.post("/api/scan", response_model=ScanResponse)
async def process_scan(
    type: str = Form(..., description="Must be 'text', 'file', or 'url'"), 
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Unified endpoint to analyze text, URLs, or files for potential scams.
    Routes the input through the appropriate extraction pipeline before AI analysis.
    """
    extracted_content = ""

    # Pipeline Branch 1: Plain Text Input
    if type == "text":
        if not text:
            raise HTTPException(status_code=400, detail="Text input is required for type 'text'.")
        extracted_content = text

    # Pipeline Branch 2: File Upload (OCR Extraction)
    elif type == "file":
        if not file:
            raise HTTPException(status_code=400, detail="File is required for type 'file'.")
        
        # Save uploaded file temporarily to the local disk
        temp_file_path = f"temp_{file.filename}"
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # Execute the OCR Service
            extracted_content = extract_text_from_image(temp_file_path)
        finally:
            # Ensure the temporary file is securely deleted after processing
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
        if not extracted_content:
            raise HTTPException(status_code=500, detail="System failed to extract text from the uploaded image.")

    # Pipeline Branch 3: URL Analysis
    elif type == "url":
        if not url:
            raise HTTPException(status_code=400, detail="URL is required for type 'url'.")
        # Placeholder for future URL scraping logic
        extracted_content = f"Simulated content extracted from the provided URL: {url}"

    else:
        raise HTTPException(status_code=400, detail="Invalid scan type. Accepted values are 'text', 'file', or 'url'.")

    # Final Stage: Pass the unified extracted content to the AI Brain
    try:
        ai_analysis_result = analyze_text_with_ai(extracted_content)
        return ai_analysis_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing encountered an error: {str(e)}")