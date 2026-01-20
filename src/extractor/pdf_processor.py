"""PDF text extraction with OCR fallback support"""

import logging
from pathlib import Path
from typing import Optional, Union
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Union[str, Path], use_ocr: bool = True) -> str:
    """
    Extract text from a PDF file.
    
    First attempts direct text extraction. If that yields little or no text,
    falls back to OCR for scanned/image-based PDFs.
    
    Args:
        pdf_path: Path to the PDF file
        use_ocr: Whether to use OCR as fallback (default: True)
        
    Returns:
        Extracted text content as a string
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Try direct text extraction first
    text_content = _extract_text_direct(pdf_path)
    
    # Check if we got meaningful text (more than just whitespace/formatting)
    text_length = len(text_content.strip())
    
    # If text extraction yielded very little content, try OCR
    if use_ocr and text_length < 100:
        logger.info(f"Direct extraction yielded only {text_length} characters, trying OCR...")
        ocr_text = _extract_text_ocr(pdf_path)
        
        # Use OCR result if it's significantly longer
        if len(ocr_text.strip()) > text_length * 1.5:
            logger.info(f"OCR extraction yielded {len(ocr_text.strip())} characters, using OCR result")
            return ocr_text
    
    return text_content


def _extract_text_direct(pdf_path: Path) -> str:
    """Extract text directly from PDF using pdfplumber"""
    text_parts = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
        
        return "\n".join(text_parts)
    
    except Exception as e:
        logger.error(f"Error in direct text extraction: {e}")
        return ""


def _extract_text_ocr(pdf_path: Path) -> str:
    """Extract text using OCR (Tesseract) with support for Chinese and English"""
    text_parts = []
    
    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=300)
        
        # Try to detect if Chinese language support is available
        # Use 'chi_sim+eng' for Simplified Chinese + English, fallback to 'eng' only
        try:
            # Check if Chinese language data is available
            pytesseract.get_languages()
            lang = 'chi_sim+eng'  # Simplified Chinese + English
        except:
            lang = 'eng'  # Fallback to English only
        
        for page_num, image in enumerate(images, 1):
            try:
                # Perform OCR on the image with language support
                page_text = pytesseract.image_to_string(image, lang=lang)
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")
            except Exception as e:
                # If Chinese+English fails, try English only
                if lang != 'eng':
                    try:
                        page_text = pytesseract.image_to_string(image, lang='eng')
                        if page_text.strip():
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")
                    except:
                        logger.warning(f"Error performing OCR on page {page_num}: {e}")
                else:
                    logger.warning(f"Error performing OCR on page {page_num}: {e}")
                continue
        
        return "\n".join(text_parts)
    
    except Exception as e:
        logger.error(f"Error in OCR extraction: {e}")
        # If OCR fails, return empty string (will fall back to direct extraction result)
        return ""


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = ' '.join(line.split())
        if cleaned_line:  # Skip empty lines
            cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)
