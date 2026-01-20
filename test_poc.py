#!/usr/bin/env python3
"""Quick test script for the POC"""

import sys
from pathlib import Path
from src.extractor.pdf_processor import extract_text_from_pdf
from src.extractor.ai_extractor import AIExtractor
from src.extractor.schema_validator import validate_and_format
import json

def test_extraction(pdf_path: str):
    """Test the full extraction pipeline"""
    print(f"\n{'='*60}")
    print(f"Testing extraction for: {Path(pdf_path).name}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Extract text from PDF
        print("Step 1: Extracting text from PDF...")
        pdf_text = extract_text_from_pdf(pdf_path, use_ocr=True)
        print(f"✓ Extracted {len(pdf_text)} characters")
        print(f"  Preview: {pdf_text[:200]}...\n")
        
        # Step 2: Extract structured data using AI
        print("Step 2: Extracting structured data using AI...")
        extractor = AIExtractor()
        extracted_data = extractor.extract(pdf_text)
        print(f"✓ AI extraction completed")
        print(f"  Extracted keys: {list(extracted_data.keys())}\n")
        
        # Step 3: Validate extracted data
        print("Step 3: Validating extracted data...")
        validated_data, validation_result = validate_and_format(extracted_data)
        
        if validation_result.is_valid:
            print("✓ Validation PASSED")
        else:
            print("⚠ Validation FAILED")
            print(f"  Errors: {validation_result.errors}")
            print(f"  Missing fields: {validation_result.missing_fields}")
        
        # Print summary
        print(f"\n{'='*60}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(json.dumps(validated_data, indent=2, default=str))
        print(f"\n{'='*60}\n")
        
        return validated_data, validation_result
        
    except Exception as e:
        print(f"✗ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    # Get PDF file from command line or use first available
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Use first PDF from policy-docs
        policy_docs_dir = Path(__file__).parent / "policy-docs"
        pdf_files = list(policy_docs_dir.glob("*.pdf"))
        if not pdf_files:
            print("No PDF files found in policy-docs directory")
            sys.exit(1)
        pdf_path = pdf_files[0]
        print(f"Using first available PDF: {pdf_path.name}")
    
    if not Path(pdf_path).exists():
        print(f"PDF file not found: {pdf_path}")
        sys.exit(1)
    
    test_extraction(pdf_path)
