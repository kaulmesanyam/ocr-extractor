"""OpenAI-based extraction of structured policy data from PDF text"""

import json
import logging
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIExtractor:
    """Extracts structured policy data from PDF text using OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the AI extractor.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
    
    def extract(self, pdf_text: str) -> Dict[str, Any]:
        """
        Extract structured policy data from PDF text.
        
        Args:
            pdf_text: Extracted text content from PDF
            
        Returns:
            Dictionary containing extracted policy data
        """
        prompt = self._build_extraction_prompt(pdf_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            response_text = response.choices[0].message.content
            if not response_text:
                raise ValueError("Empty response from OpenAI API")
            
            # Parse key-value pairs from the response and construct JSON
            extracted_data = self._parse_key_value_pairs(response_text)
            
            logger.info("Successfully extracted policy data from PDF")
            return extracted_data
        
        except Exception as e:
            logger.error(f"Error during AI extraction: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for extraction"""
        return """You are an expert at extracting structured information from car insurance policy documents.
Your task is to extract all relevant information from the provided policy document text and return it as KEY-VALUE PAIRS.

Return the extracted data in the following format, one key-value pair per line:
KEY: value

For nested objects, use dot notation (e.g., "policyholder.name: John Doe", "coverage.liabilityLimits.bodilyInjury: 100000000")

For arrays, use comma-separated values (e.g., "policyholder.namedDrivers: Driver1, Driver2")

CRITICAL - Required fields that MUST be extracted (use "UNKNOWN" if truly not found):
- policyholder.name, policyholder.address, policyholder.occupation, policyholder.namedDrivers (optional)
- vehicle.registrationMark, vehicle.makeAndModel, vehicle.yearOfManufacture, vehicle.chassisNumber, vehicle.engineNumber (optional), vehicle.cubicCapacity (optional), vehicle.seatingCapacity, vehicle.bodyType, vehicle.estimatedValue (optional)
- coverage.typeOfCover, coverage.liabilityLimits.bodilyInjury, coverage.liabilityLimits.propertyDamage, coverage.excess.thirdPartyProperty (optional), coverage.excess.youngDriver (optional), coverage.excess.inexperiencedDriver (optional), coverage.excess.unnamedDriver (optional), coverage.limitationsOnUse, coverage.authorizedDrivers
- premiumAndDiscounts.premiumAmount, premiumAndDiscounts.totalPayable, premiumAndDiscounts.noClaimDiscount (as number, e.g., 60 for 60%), premiumAndDiscounts.levies.mib (optional), premiumAndDiscounts.levies.ia (optional)
- insurerAndPolicyDetails.insurerName, insurerAndPolicyDetails.policyNumber, insurerAndPolicyDetails.periodOfInsurance.start, insurerAndPolicyDetails.periodOfInsurance.end, insurerAndPolicyDetails.dateOfIssue (optional)
- additionalEndorsements.endorsements (optional, comma-separated), additionalEndorsements.hirePurchaseMortgagee (optional)

SPECIAL INSTRUCTIONS FOR CRITICAL FIELDS:

1. coverage.limitationsOnUse: This is ALWAYS present in insurance documents, even if it's standard boilerplate text. Look for phrases like:
   - "social, domestic and pleasure"
   - "business or profession"
   - "use only for..."
   - "restrictions on use"
   Extract the FULL sentence or paragraph describing usage restrictions. If you find ANY text about usage, extract it. If truly not found, use "UNKNOWN - standard usage restrictions apply"

2. coverage.authorizedDrivers: This is ALWAYS present. Look for phrases like:
   - "the policyholder"
   - "any person driving with permission"
   - "authorized drivers"
   - "who may drive"
   Extract the FULL description. If you find ANY text about who can drive, extract it. If truly not found, use "UNKNOWN - standard driver authorization applies"

3. insurerAndPolicyDetails.insurerName: Search the ENTIRE document including headers, footers, and first page. Look for company names, insurer names, or insurance company logos/text. Common patterns: "Insurance Company", "Insurance Ltd", company names in headers.

4. vehicle and policyholder details: These are often in tables, schedules, or structured sections. Search the entire document, not just the first page.

5. premiumAndDiscounts: Look for premium tables, payment schedules, or summary sections. Search for "premium", "total payable", "NCD", "no claim discount".

HANDLING REDACTED DOCUMENTS:
- If a field is REDACTED, BLACKED OUT, or shows as "***", "[REDACTED]", or similar masking, use "REDACTED" as the value
- If a field label exists but the value is completely obscured/blacked out, extract it as "REDACTED"
- Do NOT try to guess redacted values - use "REDACTED" explicitly

HANDLING MULTILINGUAL DOCUMENTS:
- Documents may contain Chinese text (繁體中文 or 简体中文) - extract information from both English and Chinese sections
- Look for bilingual labels (e.g., "Policyholder / 受保人", "Vehicle / 車輛")
- Extract values from whichever language they appear in
- If information appears in Chinese only, extract it as-is (the system will handle it)

Important guidelines:
1. Extract all available information accurately - search the ENTIRE document thoroughly
2. For required string fields (limitationsOnUse, authorizedDrivers, insurerName, etc.), if not found, use "UNKNOWN" (not null, not empty). If REDACTED, use "REDACTED"
3. For optional fields that are missing, omit that line (don't include it). If REDACTED, include it with value "REDACTED"
4. Dates should be in DD/MM/YYYY format
5. Monetary values should be numbers only (not strings with currency symbols)
6. Percentages should be numbers (e.g., 60 for 60%, not "60%")
7. Return ONLY the key-value pairs, one per line, no additional text or explanation
8. Use the exact key names as specified above
9. Be thorough - read through ALL pages and sections of the document
10. If you see blacked-out sections, masked text, or "[REDACTED]" markers, explicitly use "REDACTED" as the value"""

    def _build_extraction_prompt(self, pdf_text: str) -> str:
        """Build the extraction prompt with PDF text"""
        # Truncate very long text to avoid token limits (keep first 20000 chars for better coverage)
        max_chars = 20000
        if len(pdf_text) > max_chars:
            pdf_text = pdf_text[:max_chars] + "\n\n[Text truncated due to length...]"
        
        # Detect if document contains Chinese characters or redaction markers
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in pdf_text)
        has_redaction = any(marker in pdf_text.upper() for marker in ['REDACTED', '***', 'BLACKED', 'MASKED', '████'])
        
        detection_note = ""
        if has_chinese:
            detection_note += "\nNOTE: This document contains Chinese text. Extract information from both English and Chinese sections.\n"
        if has_redaction:
            detection_note += "\nNOTE: This document appears to contain REDACTED information. Use 'REDACTED' as the value for any fields that are blacked out, masked, or show redaction markers.\n"
        
        return f"""Extract all relevant information from the following car insurance policy document text.
{detection_note}
Policy Document Text:
---
{pdf_text}
---

CRITICAL INSTRUCTIONS:
1. Read through the ENTIRE document text carefully - information may be on any page
2. Search for ALL required fields listed in the system prompt
3. For coverage.limitationsOnUse and coverage.authorizedDrivers: These are ALWAYS present in insurance documents, even if they look like standard boilerplate. Extract the full text describing usage restrictions and authorized drivers.
4. For insurerAndPolicyDetails.insurerName: Search headers, footers, company logos, and all pages. The insurer name is always present somewhere in the document.
5. For vehicle and policyholder details: Check tables, schedules, and structured sections throughout the document.
6. For premium information: Look for premium tables, payment summaries, or financial sections.
7. If you encounter REDACTED, BLACKED OUT, or MASKED fields (showing as ***, [REDACTED], black boxes, etc.), use "REDACTED" as the value - do NOT try to guess or infer the value.
8. If the document contains Chinese text, extract information from both English and Chinese sections. Look for bilingual labels.

Return all extracted information as KEY-VALUE PAIRS (one per line) as described in the system prompt.
For required fields that cannot be found, use "UNKNOWN" (not null, not empty) to ensure the data structure is complete.
For fields that are REDACTED, use "REDACTED" as the value."""

    def _parse_key_value_pairs(self, response_text: str) -> Dict[str, Any]:
        """
        Parse key-value pairs from AI response and construct JSON structure.
        
        Args:
            response_text: Raw response text with key-value pairs
            
        Returns:
            Dictionary with structured policy data
        """
        # Initialize the structure
        data = {
            "policyholder": {},
            "vehicle": {},
            "coverage": {
                "liabilityLimits": {},
                "excess": {}
            },
            "premiumAndDiscounts": {
                "levies": {}
            },
            "insurerAndPolicyDetails": {
                "periodOfInsurance": {}
            },
            "additionalEndorsements": {}
        }
        
        # Parse each line
        lines = response_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            # Split key and value
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            key = parts[0].strip()
            value = parts[1].strip()
            
            # Skip empty values (but allow "N/A", "UNKNOWN", and "REDACTED" for required fields)
            if not value or (value.lower() == 'null' and 'N/A' not in value and 'UNKNOWN' not in value.upper() and 'REDACTED' not in value.upper()):
                continue
            
            # Parse nested keys (e.g., "policyholder.name" -> data["policyholder"]["name"])
            self._set_nested_value(data, key, value)
        
        # Fill in missing required fields with defaults
        self._fill_missing_required_fields(data)
        
        return data
    
    def _clean_empty_objects(self, data: Dict[str, Any]):
        """Remove empty nested objects and arrays"""
        if isinstance(data, dict):
            keys_to_remove = []
            for key, value in data.items():
                if isinstance(value, dict):
                    self._clean_empty_objects(value)
                    if not value:
                        keys_to_remove.append(key)
                elif isinstance(value, list):
                    if not value:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del data[key]
    
    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """
        Set a nested value in the data structure using dot notation.
        
        Args:
            data: The data dictionary to modify
            key_path: Dot-separated key path (e.g., "policyholder.name")
            value: Value to set
        """
        keys = key_path.split('.')
        current = data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        
        # Handle special cases
        if final_key == "namedDrivers" or final_key == "endorsements":
            # Parse comma-separated array values
            if value and value != "N/A":
                current[final_key] = [v.strip() for v in value.split(',') if v.strip()]
            else:
                current[final_key] = []
        elif final_key in ["yearOfManufacture", "seatingCapacity"]:
            # Parse integers
            try:
                current[final_key] = int(value) if value != "N/A" else None
            except (ValueError, TypeError):
                current[final_key] = None
        elif final_key in ["premiumAmount", "totalPayable", "noClaimDiscount", "bodilyInjury", 
                          "propertyDamage", "cubicCapacity", "estimatedValue", "mib",
                          "thirdPartyProperty", "youngDriver", "inexperiencedDriver", "unnamedDriver"]:
            # Parse numbers
            try:
                # Remove currency symbols and commas
                cleaned = value.replace('$', '').replace(',', '').replace('HKD', '').strip()
                if cleaned and cleaned != "N/A":
                    current[final_key] = float(cleaned) if '.' in cleaned else int(cleaned)
                else:
                    current[final_key] = None
            except (ValueError, TypeError):
                current[final_key] = None
        elif final_key == "ia":
            # Can be number or string
            try:
                cleaned = value.replace('$', '').replace(',', '').replace('HKD', '').strip()
                if cleaned and cleaned.upper() != "INCLUDED" and cleaned != "N/A":
                    current[final_key] = float(cleaned) if '.' in cleaned else int(cleaned)
                else:
                    current[final_key] = value if value.upper() == "INCLUDED" else None
            except (ValueError, TypeError):
                current[final_key] = value if value.upper() == "INCLUDED" else None
        else:
            # String values - for required fields, keep "N/A" or "UNKNOWN" as strings
            # Required string fields that should never be None:
            required_string_fields = [
                "name", "address", "occupation", "registrationMark", "makeAndModel",
                "chassisNumber", "bodyType", "typeOfCover", "limitationsOnUse",
                "authorizedDrivers", "insurerName", "policyNumber"
            ]
            
            if final_key in required_string_fields:
                # Keep "N/A", "UNKNOWN", or "REDACTED" as strings for required fields
                if value.upper() in ["N/A", "UNKNOWN", "REDACTED"]:
                    current[final_key] = value.upper()
                elif value.upper().startswith("UNKNOWN") or value.upper().startswith("REDACTED"):
                    current[final_key] = value  # Keep full "UNKNOWN - ..." or "REDACTED" message
                else:
                    current[final_key] = value
            else:
                # Optional string fields can be None
                current[final_key] = value if value != "N/A" else None
    
    def _fill_missing_required_fields(self, data: Dict[str, Any]):
        """
        Fill in missing required fields with default values to ensure schema validation passes.
        
        Args:
            data: The data dictionary to fill
        """
        # Required string fields with defaults
        defaults = {
            "policyholder": {
                "name": "UNKNOWN",
                "address": "UNKNOWN",
                "occupation": "UNKNOWN"
            },
            "vehicle": {
                "registrationMark": "UNKNOWN",
                "makeAndModel": "UNKNOWN",
                "yearOfManufacture": 0,  # Default integer for required field
                "chassisNumber": "UNKNOWN",
                "seatingCapacity": 0,  # Default integer for required field
                "bodyType": "UNKNOWN"
            },
            "coverage": {
                "typeOfCover": "UNKNOWN",
                "limitationsOnUse": "UNKNOWN - standard usage restrictions apply",
                "authorizedDrivers": "UNKNOWN - standard driver authorization applies",
                "liabilityLimits": {
                    "bodilyInjury": 0,
                    "propertyDamage": 0
                },
                "excess": {}
            },
            "premiumAndDiscounts": {
                "premiumAmount": 0.0,
                "totalPayable": 0.0,
                "noClaimDiscount": 0.0
            },
            "insurerAndPolicyDetails": {
                "insurerName": "UNKNOWN",
                "policyNumber": "UNKNOWN",
                "periodOfInsurance": {
                    "start": "UNKNOWN",
                    "end": "UNKNOWN"
                }
            }
        }
        
        # Fill policyholder
        for key, default in defaults["policyholder"].items():
            if key not in data.get("policyholder", {}) or data["policyholder"].get(key) is None:
                if "policyholder" not in data:
                    data["policyholder"] = {}
                data["policyholder"][key] = default
        
        # Fill vehicle
        if "vehicle" not in data:
            data["vehicle"] = {}
        for key, default in defaults["vehicle"].items():
            # For integer fields, check if None or missing
            if key in ["yearOfManufacture", "seatingCapacity"]:
                if key not in data["vehicle"] or data["vehicle"].get(key) is None:
                    data["vehicle"][key] = default
            else:
                # For string fields, check if None or missing
                if key not in data["vehicle"] or data["vehicle"].get(key) is None:
                    data["vehicle"][key] = default
        
        # Fill coverage
        if "coverage" not in data:
            data["coverage"] = {}
        
        for key, default in defaults["coverage"].items():
            if key == "liabilityLimits":
                if "liabilityLimits" not in data["coverage"]:
                    data["coverage"]["liabilityLimits"] = {}
                for sub_key, sub_default in default.items():
                    if sub_key not in data["coverage"]["liabilityLimits"] or data["coverage"]["liabilityLimits"].get(sub_key) is None:
                        data["coverage"]["liabilityLimits"][sub_key] = sub_default
            elif key == "excess":
                if "excess" not in data["coverage"]:
                    data["coverage"]["excess"] = {}
            else:
                if key not in data["coverage"] or data["coverage"].get(key) is None:
                    data["coverage"][key] = default
        
        # Fill premiumAndDiscounts
        if "premiumAndDiscounts" not in data:
            data["premiumAndDiscounts"] = {}
        for key, default in defaults["premiumAndDiscounts"].items():
            if key not in data["premiumAndDiscounts"] or data["premiumAndDiscounts"].get(key) is None:
                data["premiumAndDiscounts"][key] = default
        
        # Handle levies - remove null values or set defaults
        if "levies" in data["premiumAndDiscounts"]:
            levies = data["premiumAndDiscounts"]["levies"]
            # Set default 0 for mib if null
            if "mib" in levies and levies["mib"] is None:
                levies["mib"] = 0.0
            # Set default 0 for ia if null
            if "ia" in levies and levies["ia"] is None:
                levies["ia"] = 0.0
            # Remove levies object if both are missing/null (shouldn't happen after above, but just in case)
            if not levies or (levies.get("mib") is None and levies.get("ia") is None):
                data["premiumAndDiscounts"].pop("levies", None)
        
        # Fill insurerAndPolicyDetails
        if "insurerAndPolicyDetails" not in data:
            data["insurerAndPolicyDetails"] = {}
        if "periodOfInsurance" not in data["insurerAndPolicyDetails"]:
            data["insurerAndPolicyDetails"]["periodOfInsurance"] = {}
        
        for key, default in defaults["insurerAndPolicyDetails"].items():
            if key == "periodOfInsurance":
                for sub_key, sub_default in default.items():
                    if sub_key not in data["insurerAndPolicyDetails"]["periodOfInsurance"] or data["insurerAndPolicyDetails"]["periodOfInsurance"].get(sub_key) is None:
                        data["insurerAndPolicyDetails"]["periodOfInsurance"][sub_key] = sub_default
            else:
                if key not in data["insurerAndPolicyDetails"] or data["insurerAndPolicyDetails"].get(key) is None:
                    data["insurerAndPolicyDetails"][key] = default


def extract_policy_data(pdf_text: str, api_key: Optional[str] = None, model: str = "gpt-4o") -> Dict[str, Any]:
    """
    Convenience function to extract policy data from PDF text.
    
    Args:
        pdf_text: Extracted text content from PDF
        api_key: OpenAI API key (optional, uses env var if not provided)
        model: OpenAI model to use (default: gpt-4o)
        
    Returns:
        Dictionary containing extracted policy data
    """
    extractor = AIExtractor(api_key=api_key, model=model)
    return extractor.extract(pdf_text)
