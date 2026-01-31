# Car Insurance Policy Extraction POC

A Python-based proof-of-concept system that extracts structured data from car insurance policy PDFs using OCR and AI (OpenAI GPT), outputting JSON conforming to a defined schema.

## Features

- **PDF Text Extraction**: Direct text extraction with OCR fallback for scanned documents
- **AI-Powered Extraction**: Uses OpenAI GPT models to intelligently parse and extract structured data
- **Schema Validation**: Validates extracted data against a comprehensive JSON schema
- **REST API**: FastAPI-based API for easy integration and testing

## Architecture

The system consists of four main components:

1. **PDF Processing Layer**: Extracts text from PDFs using `pdfplumber` and falls back to OCR (`pytesseract`) for scanned documents
2. **AI Extraction Layer**: Uses OpenAI GPT models to parse extracted text and structure it according to the schema
3. **Schema Validation**: Validates extracted JSON against Pydantic models
4. **API Interface**: FastAPI REST API for file upload and extraction

## Prerequisites

- Python 3.9 or higher
- Tesseract OCR (for OCR functionality)
  - macOS: `brew install tesseract` and `brew install tesseract-lang` (for Chinese support)
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim` (for Chinese support)
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) and install Chinese language data
- OpenAI API key

## Installation

1. Clone or navigate to the project directory:
```bash
cd project-3
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Running the API Server

Start the FastAPI server:
```bash
python -m src.api.main
```

Or using uvicorn directly:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Health Check
```bash
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "service": "policy-extraction"
}
```

#### Extract Policy Data
```bash
POST /extract
Content-Type: multipart/form-data
```

Upload a PDF file:
```bash
curl -X POST "http://localhost:8000/extract" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@policy-docs/test12.pdf" -o out_test12.json
```

Response format:
```json
{
  "success": true,
  "data": {
    "policyholder": { ... },
    "vehicle": { ... },
    "coverage": { ... },
    "premiumAndDiscounts": { ... },
    "insurerAndPolicyDetails": { ... },
    "additionalEndorsements": { ... }
  },
  "validation": {
    "is_valid": true,
    "errors": [],
    "missing_fields": []
  }
}
```

### Using the API with Python

```python
import requests

url = "http://localhost:8000/extract"
with open("policy.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    data = response.json()
    print(data)
```

### Using the Extraction Modules Directly

```python
from src.extractor.pdf_processor import extract_text_from_pdf
from src.extractor.ai_extractor import extract_policy_data
from src.extractor.schema_validator import validate_and_format

# Extract text from PDF
pdf_text = extract_text_from_pdf("policy.pdf")

# Extract structured data using AI
extracted_data = extract_policy_data(pdf_text)

# Validate the data
validated_data, validation_result = validate_and_format(extracted_data)

if validation_result.is_valid:
    print("Extraction successful!")
    print(validated_data)
else:
    print("Validation errors:", validation_result.errors)
```

## Project Structure

```
project-3/
├── policy-docs/              # Sample PDFs (existing)
├── schema.pdf                # Schema definition (existing)
├── validator.json            # JSON schema for validation
├── .env                      # Environment variables (create this)
├── src/
│   ├── __init__.py
│   ├── extractor/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py      # PDF text extraction & OCR
│   │   ├── ai_extractor.py       # OpenAI-based extraction (key-value pairs)
│   │   └── schema_validator.py  # JSON schema validation
│   ├── models/
│   │   ├── __init__.py
│   │   └── policy_schema.py     # Pydantic models (for reference)
│   └── api/
│       ├── __init__.py
│       └── main.py               # FastAPI application
├── tests/
│   └── test_extractor.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Schema

The extracted data conforms to the JSON schema defined in `validator.json`. This schema file can be updated directly if the upper layer APIs require changes to the JSON structure.

The schema includes the following main sections:

- **policyholder**: Name, address, occupation, named drivers
- **vehicle**: Registration mark, make/model, year, VIN, engine details, seating capacity, body type, estimated value
- **coverage**: Type of cover, liability limits, excess/deductibles, limitations on use, authorized drivers
- **premiumAndDiscounts**: Premium amount, total payable, no-claim discount, levies
- **insurerAndPolicyDetails**: Insurer name, policy number, period of insurance, date of issue
- **additionalEndorsements**: Endorsements/clauses, hire purchase/mortgagee

See `schema.pdf` for the detailed field descriptions and `validator.json` for the JSON schema definition used for validation.

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run individual tests:
```bash
python tests/test_extractor.py
```

## Known Limitations

1. **OCR Dependency**: OCR functionality requires Tesseract to be installed on the system
2. **API Costs**: Uses OpenAI API which incurs costs per request
3. **PDF Quality**: Extraction accuracy depends on PDF quality and format
4. **Token Limits**: Very long PDFs may be truncated to fit within API token limits
5. **Redacted Documents**: Documents with redacted/blacked-out fields will show "REDACTED" for those fields
6. **Multilingual Support**: Supports English and Chinese (Simplified) documents. For Chinese documents, ensure Tesseract Chinese language data is installed

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Successful extraction
- `400`: Invalid file type or request
- `422`: Unable to extract text from PDF
- `500`: Server error (AI extraction failure, validation error, etc.)

Validation errors and missing fields are included in the response for debugging.

## Future Enhancements

- Batch processing multiple PDFs
- Web UI for file upload
- Caching extracted results
- Integration with quote generation APIs
- Support for additional document formats
- Multi-language support

## License

This is a proof-of-concept project.
