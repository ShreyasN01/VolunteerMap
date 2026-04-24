"""
OCR Processor for VolunteerMap.

Uses Google Cloud Vision API to extract text from images of paper surveys,
then parses the text to identify survey fields like category, severity,
district, and description.

Falls back to mock extracted data when Vision API key is not configured.
"""

import os
import re
import logging
from typing import Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Maharashtra districts for matching
MAHARASHTRA_DISTRICTS = [
    "Sangli", "Pune", "Kolhapur", "Solapur", "Nashik",
    "Mumbai", "Nagpur", "Aurangabad", "Thane", "Satara",
    "Ratnagiri", "Sindhudurg", "Ahmednagar", "Jalgaon", "Dhule",
    "Nandurbar", "Latur", "Osmanabad", "Beed", "Parbhani",
    "Hingoli", "Nanded", "Washim", "Yavatmal", "Amravati",
    "Akola", "Buldhana", "Wardha", "Chandrapur", "Gadchiroli",
    "Bhandara", "Gondia", "Raigad", "Palghar",
]

# Category keyword mapping
CATEGORY_KEYWORDS = {
    "healthcare": ["hospital", "medicine", "doctor", "health", "medical", "clinic",
                    "patient", "disease", "treatment", "nurse", "ambulance", "fever",
                    "injury", "healthcare", "vaccination", "pharma"],
    "food": ["food", "hunger", "meal", "nutrition", "ration", "grain", "rice",
             "wheat", "cooking", "starving", "malnutrition", "kitchen", "feeding"],
    "education": ["school", "education", "teacher", "student", "learn", "book",
                   "classroom", "tuition", "literacy", "exam", "study", "college"],
    "sanitation": ["sanitation", "toilet", "water", "drainage", "sewage", "waste",
                    "clean", "hygiene", "latrine", "garbage", "pollution", "drinking water"],
    "employment": ["job", "employment", "work", "skill", "training", "livelihood",
                    "income", "wages", "labor", "unemployed", "occupation", "workshop"],
}

# Severity keywords
SEVERITY_KEYWORDS = {
    5: ["critical", "emergency", "life-threatening", "death", "dying", "urgent"],
    4: ["severe", "serious", "acute", "dangerous", "alarming"],
    3: ["moderate", "concerning", "significant", "important"],
    2: ["mild", "minor", "low", "manageable"],
    1: ["minimal", "negligible", "slight"],
}

# Mock OCR response for demo mode
MOCK_OCR_RESULT = {
    "id": str(uuid.uuid4()),
    "submitted_at": datetime.now().isoformat(),
    "location": {"latitude": 16.85, "longitude": 74.59},
    "district": "Sangli",
    "state": "Maharashtra",
    "category": "healthcare",
    "description": "Rural health camp needed — multiple families reporting fever and waterborne diseases after recent flooding. Approximately 50 people affected in 3 villages.",
    "severity": 4,
    "affected_count": 50,
    "source": "paper_ocr",
    "urgency_score": 0.0,  # Will be computed by ML pipeline
}


def _is_demo_mode() -> bool:
    """Check if the app is running in demo mode (no Vision API key)."""
    api_key = os.getenv("CLOUD_VISION_API_KEY", "")
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    return (not api_key or api_key.startswith("your_")) and (
        not sa_json or sa_json.startswith("your_") or sa_json == '{"type":"service_account",...}'
    )


def extract_survey_from_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extract survey fields from a paper survey image using OCR.

    Processes the image through Google Cloud Vision API to extract text,
    then uses keyword matching to identify category, severity, district,
    and description fields.

    Args:
        image_bytes: Raw bytes of the uploaded image (JPG or PNG).

    Returns:
        Dictionary containing extracted survey fields with source="paper_ocr".
        Falls back to defaults for fields that cannot be extracted.
    """
    if _is_demo_mode():
        logger.info("Running in demo mode. Returning mock OCR result.")
        mock = dict(MOCK_OCR_RESULT)
        mock["id"] = str(uuid.uuid4())
        mock["submitted_at"] = datetime.now().isoformat()
        return mock

    try:
        raw_text = _call_vision_api(image_bytes)
        return _parse_survey_text(raw_text)
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}. Returning mock result.")
        mock = dict(MOCK_OCR_RESULT)
        mock["id"] = str(uuid.uuid4())
        mock["submitted_at"] = datetime.now().isoformat()
        return mock


def _call_vision_api(image_bytes: bytes) -> str:
    """
    Call Google Cloud Vision API for text detection.

    Args:
        image_bytes: Raw image bytes.

    Returns:
        Extracted text string from the image.

    Raises:
        Exception: If API call fails.
    """
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)

    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(f"Vision API error: {response.error.message}")

    texts = response.text_annotations
    if not texts:
        logger.warning("No text detected in image.")
        return ""

    raw_text = texts[0].description
    logger.info(f"OCR extracted {len(raw_text)} characters from image.")
    return raw_text


def _parse_survey_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw OCR text to extract survey fields using keyword matching.

    Args:
        raw_text: Text extracted from the image by Vision API.

    Returns:
        Dictionary containing parsed survey fields.
    """
    text_lower = raw_text.lower()

    # Extract category
    category = _detect_category(text_lower)

    # Extract severity
    severity = _detect_severity(text_lower)

    # Extract district
    district = _detect_district(raw_text)

    # Extract affected count
    affected_count = _detect_affected_count(text_lower)

    # Use the full text as description (truncated)
    description = raw_text.strip()[:500] if raw_text.strip() else "Paper survey — details pending manual review"

    return {
        "id": str(uuid.uuid4()),
        "submitted_at": datetime.now().isoformat(),
        "location": {"latitude": 16.85, "longitude": 74.59},  # Default: Sangli area
        "district": district,
        "state": "Maharashtra",
        "category": category,
        "description": description,
        "severity": severity,
        "affected_count": affected_count,
        "source": "paper_ocr",
        "urgency_score": 0.0,  # Will be computed by ML pipeline
    }


def _detect_category(text_lower: str) -> str:
    """
    Detect the survey category based on keyword frequency in text.

    Args:
        text_lower: Lowercase text to search.

    Returns:
        Detected category string, defaults to "healthcare".
    """
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score

    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "healthcare"  # Default


def _detect_severity(text_lower: str) -> int:
    """
    Detect severity level from keywords or explicit numbers.

    Args:
        text_lower: Lowercase text to search.

    Returns:
        Severity integer 1-5, defaults to 3.
    """
    # Look for explicit numbers (e.g., "severity: 4", "level 5")
    number_match = re.search(r'(?:severity|level|urgency)\s*[:\-]?\s*(\d)', text_lower)
    if number_match:
        num = int(number_match.group(1))
        if 1 <= num <= 5:
            return num

    # Keyword-based detection
    for level in [5, 4, 3, 2, 1]:
        for keyword in SEVERITY_KEYWORDS[level]:
            if keyword in text_lower:
                return level

    return 3  # Default


def _detect_district(raw_text: str) -> str:
    """
    Detect district name by matching against known Maharashtra districts.

    Args:
        raw_text: Original (case-preserved) text.

    Returns:
        Matched district name, defaults to "Sangli".
    """
    for district in MAHARASHTRA_DISTRICTS:
        if district.lower() in raw_text.lower():
            return district
    return "Sangli"  # Default


def _detect_affected_count(text_lower: str) -> int:
    """
    Extract the number of affected people from text.

    Args:
        text_lower: Lowercase text to search.

    Returns:
        Extracted count integer, defaults to 25.
    """
    # Look for patterns like "50 people", "affected 100", "200 families"
    patterns = [
        r'(\d+)\s*(?:people|persons|individuals|families|villagers|residents)',
        r'(?:affect|impact|reach)\w*\s*(\d+)',
        r'(?:approximately|approx|about|around|nearly)\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            count = int(match.group(1))
            if 1 <= count <= 10000:
                return count

    return 25  # Default
