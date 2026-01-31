FROM python:3.9-slim

# Install system dependencies
# tesseract-ocr: for text extraction
# tesseract-ocr-chi-sim: for Chinese language support
# poppler-utils: required by pdf2image
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and resources
COPY src/ src/
COPY validator.json .
COPY schema.pdf .
# Create directories that might be needed
RUN mkdir -p output

# Expose the API port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
