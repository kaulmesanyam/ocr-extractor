"""FastAPI application for policy extraction"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from src.extractor.pdf_processor import extract_text_from_pdf
from src.extractor.ai_extractor import AIExtractor
from src.extractor.schema_validator import validate_and_format

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Car Insurance Policy Extraction API",
    description="Extract structured data from car insurance policy PDFs",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "policy-extraction"}


@app.post("/extract")
async def extract_policy(
    file: UploadFile = File(..., description="PDF file to extract data from")
) -> Dict[str, Any]:
    """
    Extract structured policy data from a PDF file.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        JSON object containing extracted policy data and validation results
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF (.pdf extension required)"
        )
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        try:
            # Write uploaded content to temp file
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
            
            logger.info(f"Processing PDF: {file.filename} ({len(content)} bytes)")
            
            # Step 1: Extract text from PDF
            try:
                pdf_text = extract_text_from_pdf(tmp_file_path)
                if not pdf_text or len(pdf_text.strip()) < 50:
                    raise HTTPException(
                        status_code=422,
                        detail="Could not extract meaningful text from PDF. The file may be corrupted or image-only."
                    )
                logger.info(f"Extracted {len(pdf_text)} characters from PDF")
            except Exception as e:
                logger.error(f"Error extracting text from PDF: {e}")
                raise HTTPException(
                    status_code=422,
                    detail=f"Failed to extract text from PDF: {str(e)}"
                )
            
            # Step 2: Extract structured data using AI
            try:
                extractor = AIExtractor()
                extracted_data = extractor.extract(pdf_text)
                logger.info("Successfully extracted data using AI")
            except Exception as e:
                logger.error(f"Error during AI extraction: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"AI extraction failed: {str(e)}"
                )
            
            # Step 3: Validate extracted data
            try:
                validated_data, validation_result = validate_and_format(extracted_data)
                
                response = {
                    "success": True,
                    "data": validated_data,
                    "validation": {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors,
                        "missing_fields": validation_result.missing_fields
                    }
                }
                
                if not validation_result.is_valid:
                    logger.warning(f"Validation found {len(validation_result.errors)} errors")
                    response["warnings"] = "Extracted data has validation errors. Please review."
                
                return JSONResponse(content=response)
            
            except Exception as e:
                logger.error(f"Error during validation: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Validation failed: {str(e)}"
                )
        
        finally:
            # Clean up temporary file
            try:
                Path(tmp_file_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if logger.level == logging.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
