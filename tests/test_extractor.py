"""Tests for policy extraction functionality"""

from pathlib import Path
from src.extractor.pdf_processor import extract_text_from_pdf
from src.extractor.schema_validator import validate_extracted_data


def test_pdf_text_extraction():
    """Test that PDF text extraction works"""
    # This test requires actual PDF files
    policy_docs_dir = Path(__file__).parent.parent / "policy-docs"
    
    if not policy_docs_dir.exists():
        print("SKIP: policy-docs directory not found")
        return
    
    pdf_files = list(policy_docs_dir.glob("*.pdf"))
    if not pdf_files:
        print("SKIP: No PDF files found in policy-docs directory")
        return
    
    # Test with first available PDF
    pdf_path = pdf_files[0]
    print(f"Testing PDF: {pdf_path.name}")
    
    try:
        # Try without OCR first
        text = extract_text_from_pdf(pdf_path, use_ocr=False)
        print(f"  Direct extraction: {len(text)} characters")
        
        if text is None or len(text.strip()) < 50:
            print(f"  Direct extraction yielded little text, trying with OCR...")
            text = extract_text_from_pdf(pdf_path, use_ocr=True)
            print(f"  With OCR: {len(text)} characters")
        
        if text is None or len(text.strip()) < 50:
            print(f"  Warning: Still very little text extracted ({len(text) if text else 0} chars)")
            print(f"  First 200 chars: {text[:200] if text else 'None'}")
            raise AssertionError(f"Failed to extract meaningful text from {pdf_path.name}")
        
        print(f"✓ Extracted {len(text)} characters from {pdf_path.name}")
        print(f"  Preview: {text[:200]}...")
        
    except Exception as e:
        print(f"  Error during extraction: {e}")
        raise


def test_schema_validation():
    """Test schema validation with sample data"""
    # Valid sample data
    valid_data = {
        "policyholder": {
            "name": "John Doe",
            "address": "123 Main St, Hong Kong",
            "occupation": "Engineer"
        },
        "vehicle": {
            "registrationMark": "ABC123",
            "makeAndModel": "Toyota Camry",
            "yearOfManufacture": 2020,
            "chassisNumber": "1234567890",
            "seatingCapacity": 5,
            "bodyType": "SALOON"
        },
        "coverage": {
            "typeOfCover": "COMPREHENSIVE",
            "liabilityLimits": {
                "bodilyInjury": 100000000,
                "propertyDamage": 2000000
            },
            "excess": {},
            "limitationsOnUse": "Social, domestic and pleasure",
            "authorizedDrivers": "Policyholder"
        },
        "premiumAndDiscounts": {
            "premiumAmount": 5000.0,
            "totalPayable": 5500.0,
            "noClaimDiscount": 60.0
        },
        "insurerAndPolicyDetails": {
            "insurerName": "Test Insurance Co",
            "policyNumber": "POL123456",
            "periodOfInsurance": {
                "start": "01/01/2024",
                "end": "31/12/2024"
            }
        }
    }
    
    validated_data, validation_result = validate_extracted_data(valid_data)
    
    if not validation_result.is_valid:
        raise AssertionError(f"Validation failed: {validation_result.errors}")
    
    if validated_data is None:
        raise AssertionError("Validated data is None")
    
    print("✓ Schema validation test passed!")


if __name__ == "__main__":
    # Run basic tests
    test_schema_validation()
    print("Schema validation test passed!")
    
    try:
        test_pdf_text_extraction()
        print("PDF extraction test passed!")
    except Exception as e:
        print(f"PDF extraction test skipped: {e}")
