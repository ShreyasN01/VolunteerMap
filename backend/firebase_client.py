"""
Firebase Firestore client helpers for VolunteerMap.

Provides read/write operations for surveys, volunteers, and match results.
Falls back to an in-memory store when Firebase credentials are not configured,
enabling demo mode without any cloud dependencies.
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory fallback store for demo mode
_memory_store: Dict[str, List[dict]] = {
    "surveys": [],
    "volunteers": [],
    "matches": [],
}

_firestore_db = None
_using_firestore = False


def _init_firebase():
    """
    Initialize Firebase Admin SDK using service account credentials.
    
    Reads credentials from the FIREBASE_SERVICE_ACCOUNT_JSON environment variable.
    If not set or invalid, falls back to in-memory storage for demo mode.
    """
    global _firestore_db, _using_firestore

    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json or sa_json.startswith("your_") or sa_json == '{"type":"service_account",...}':
        logger.warning("Firebase credentials not configured. Using in-memory store (demo mode).")
        _using_firestore = False
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Check if already initialized
        try:
            app = firebase_admin.get_app()
        except ValueError:
            cred_dict = json.loads(sa_json)
            cred = credentials.Certificate(cred_dict)
            app = firebase_admin.initialize_app(cred)

        _firestore_db = firestore.client()
        _using_firestore = True
        logger.info("Firebase Firestore initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}. Falling back to in-memory store.")
        _using_firestore = False


# Initialize on module load
_init_firebase()


def save_survey(survey: dict) -> str:
    """
    Save a survey entry to Firestore or in-memory store.

    Args:
        survey: Dictionary containing all survey fields.

    Returns:
        The survey ID.

    Raises:
        Exception: If Firestore write fails (logged, not re-raised in demo mode).
    """
    survey_id = survey.get("id", str(id(survey)))

    if _using_firestore:
        try:
            _firestore_db.collection("surveys").document(survey_id).set(survey)
            logger.info(f"Survey {survey_id} saved to Firestore.")
        except Exception as e:
            logger.error(f"Firestore write error for survey {survey_id}: {e}")
            # Fallback: save to memory
            _memory_store["surveys"].append(survey)
    else:
        _memory_store["surveys"].append(survey)
        logger.info(f"Survey {survey_id} saved to in-memory store. Total: {len(_memory_store['surveys'])}")

    return survey_id


def get_all_surveys() -> List[dict]:
    """
    Retrieve all survey entries from Firestore or in-memory store.

    Returns:
        List of survey dictionaries.
    """
    if _using_firestore:
        try:
            docs = _firestore_db.collection("surveys").stream()
            surveys = [doc.to_dict() for doc in docs]
            logger.info(f"Retrieved {len(surveys)} surveys from Firestore.")
            return surveys
        except Exception as e:
            logger.error(f"Firestore read error for surveys: {e}")
            return _memory_store.get("surveys", [])
    else:
        return list(_memory_store.get("surveys", []))


def save_volunteer(volunteer: dict) -> str:
    """
    Save a volunteer profile to Firestore or in-memory store.

    Args:
        volunteer: Dictionary containing all volunteer fields.

    Returns:
        The volunteer ID.
    """
    vol_id = volunteer.get("id", str(id(volunteer)))

    if _using_firestore:
        try:
            _firestore_db.collection("volunteers").document(vol_id).set(volunteer)
            logger.info(f"Volunteer {vol_id} saved to Firestore.")
        except Exception as e:
            logger.error(f"Firestore write error for volunteer {vol_id}: {e}")
            _memory_store["volunteers"].append(volunteer)
    else:
        _memory_store["volunteers"].append(volunteer)
        logger.info(f"Volunteer {vol_id} saved to in-memory store. Total: {len(_memory_store['volunteers'])}")

    return vol_id


def get_available_volunteers() -> List[dict]:
    """
    Retrieve all available volunteers from Firestore or in-memory store.

    Returns:
        List of volunteer dictionaries where available == True.
    """
    if _using_firestore:
        try:
            docs = _firestore_db.collection("volunteers").where("available", "==", True).stream()
            volunteers = [doc.to_dict() for doc in docs]
            logger.info(f"Retrieved {len(volunteers)} available volunteers from Firestore.")
            return volunteers
        except Exception as e:
            logger.error(f"Firestore read error for volunteers: {e}")
            vols = _memory_store.get("volunteers", [])
            return [v for v in vols if v.get("available", True)]
    else:
        vols = _memory_store.get("volunteers", [])
        return [v for v in vols if v.get("available", True)]


def save_match_result(match: dict) -> str:
    """
    Save a volunteer-need match result to Firestore or in-memory store.

    Args:
        match: Dictionary containing match assignment details.

    Returns:
        A match identifier string.
    """
    match_id = f"{match.get('need_id', 'unknown')}_{match.get('volunteer_id', 'unknown')}"

    if _using_firestore:
        try:
            _firestore_db.collection("matches").document(match_id).set(match)
            logger.info(f"Match {match_id} saved to Firestore.")
        except Exception as e:
            logger.error(f"Firestore write error for match {match_id}: {e}")
            _memory_store["matches"].append(match)
    else:
        _memory_store["matches"].append(match)
        logger.info(f"Match {match_id} saved to in-memory store.")

    return match_id


def get_all_matches() -> List[dict]:
    """
    Retrieve all match results from Firestore or in-memory store.

    Returns:
        List of match result dictionaries.
    """
    if _using_firestore:
        try:
            docs = _firestore_db.collection("matches").stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Firestore read error for matches: {e}")
            return _memory_store.get("matches", [])
    else:
        return list(_memory_store.get("matches", []))


def load_sample_data(sample_path: str) -> None:
    """
    Load sample survey and volunteer data from a JSON file into the store.

    Args:
        sample_path: Path to the sample_surveys.json file.
    """
    try:
        with open(sample_path, "r") as f:
            data = json.load(f)

        surveys = data.get("surveys", [])
        volunteers = data.get("volunteers", [])

        for s in surveys:
            save_survey(s)
        for v in volunteers:
            save_volunteer(v)

        logger.info(f"Loaded {len(surveys)} sample surveys and {len(volunteers)} sample volunteers.")
    except FileNotFoundError:
        logger.warning(f"Sample data file not found: {sample_path}")
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")


def clear_memory_store() -> None:
    """Clear the in-memory store. Useful for testing."""
    for key in _memory_store:
        _memory_store[key] = []
    logger.info("In-memory store cleared.")


# ─── Embedded Sample Data (Vercel Fallback) ──────────────────────────────────

EMBEDDED_SURVEYS = [
    {"id":"sample_001","submitted_at":"2026-04-20T09:15:00","location":{"latitude":16.8524,"longitude":74.5815},"district":"Sangli","state":"Maharashtra","category":"healthcare","description":"Multiple families reporting fever and waterborne diseases after recent flooding in Miraj taluka.","severity":5,"affected_count":200,"source":"digital_form","urgency_score":344.85},
    {"id":"sample_002","submitted_at":"2026-04-19T14:30:00","location":{"latitude":16.7050,"longitude":74.2433},"district":"Kolhapur","state":"Maharashtra","category":"food","description":"Severe food shortage in tribal hamlet after crop failure. 150 families have no ration card access.","severity":5,"affected_count":450,"source":"digital_form","urgency_score":318.24},
    {"id":"sample_003","submitted_at":"2026-04-21T11:00:00","location":{"latitude":18.5204,"longitude":73.8567},"district":"Pune","state":"Maharashtra","category":"education","description":"Government school in Hadapsar has no teachers for Std 8-10. 120 students preparing for board exams.","severity":4,"affected_count":120,"source":"digital_form","urgency_score":149.78},
    {"id":"sample_004","submitted_at":"2026-04-18T08:45:00","location":{"latitude":17.6599,"longitude":75.9064},"district":"Solapur","state":"Maharashtra","category":"sanitation","description":"Open drainage flowing through residential area. Mosquito breeding causing dengue cases.","severity":4,"affected_count":320,"source":"csv_upload","urgency_score":209.51},
    {"id":"sample_005","submitted_at":"2026-04-22T16:20:00","location":{"latitude":19.9975,"longitude":73.7898},"district":"Nashik","state":"Maharashtra","category":"employment","description":"200+ daily wage workers from grape vineyards left unemployed due to unseasonal rain damage.","severity":3,"affected_count":200,"source":"digital_form","urgency_score":82.66},
    {"id":"sample_008","submitted_at":"2026-04-20T07:30:00","location":{"latitude":20.0112,"longitude":73.7700},"district":"Nashik","state":"Maharashtra","category":"sanitation","description":"Village handpump contaminated with fluoride. 300 residents drinking unsafe water.","severity":5,"affected_count":300,"source":"csv_upload","urgency_score":291.22},
    {"id":"sample_010","submitted_at":"2026-04-22T12:00:00","location":{"latitude":18.5500,"longitude":73.9000},"district":"Pune","state":"Maharashtra","category":"healthcare","description":"Mental health crisis among youth. Rising anxiety and depression cases post-exam season.","severity":3,"affected_count":100,"source":"digital_form","urgency_score":180.02},
    {"id":"sample_012","submitted_at":"2026-04-21T08:00:00","location":{"latitude":16.8300,"longitude":74.5500},"district":"Sangli","state":"Maharashtra","category":"food","description":"Sugar factory closure left 100 worker families without income. Children malnourished.","severity":4,"affected_count":400,"source":"paper_ocr","urgency_score":249.42},
    {"id":"sample_020","submitted_at":"2026-04-23T10:00:00","location":{"latitude":17.6900,"longitude":75.9100},"district":"Solapur","state":"Maharashtra","category":"sanitation","description":"Solid waste dumping ground near primary school. Students falling sick from toxic fumes.","severity":5,"affected_count":180,"source":"digital_form","urgency_score":236.68},
]

EMBEDDED_VOLUNTEERS = [
    {"id":"vol_001","name":"Priya Kulkarni","phone":"+919876543210","skills":["medical","counselling"],"available":True,"location":{"latitude":16.86,"longitude":74.57},"district":"Sangli","languages":["Marathi","Hindi","English"]},
    {"id":"vol_002","name":"Ananya Sharma","phone":"+919876543211","skills":["cooking","logistics"],"available":True,"location":{"latitude":18.53,"longitude":73.86},"district":"Pune","languages":["Hindi","English","Marathi"]},
    {"id":"vol_003","name":"Amit Deshmukh","phone":"+919876543212","skills":["logistics","teaching"],"available":True,"location":{"latitude":16.70,"longitude":74.24},"district":"Kolhapur","languages":["Marathi","Hindi"]},
    {"id":"vol_004","name":"Sneha Patil","phone":"+919876543213","skills":["teaching","counselling"],"available":True,"location":{"latitude":17.67,"longitude":75.90},"district":"Solapur","languages":["Marathi","Hindi","English"]},
    {"id":"vol_005","name":"Rohan Joshi","phone":"+919876543214","skills":["medical","logistics"],"available":True,"location":{"latitude":19.99,"longitude":73.79},"district":"Nashik","languages":["Marathi","Hindi"]},
    {"id":"vol_006","name":"Rajesh Jadhav","phone":"+919876543215","skills":["logistics","counselling"],"available":True,"location":{"latitude":20.00,"longitude":73.78},"district":"Nashik","languages":["Hindi","Marathi"]},
    {"id":"vol_007","name":"Meera Bhosale","phone":"+919876543216","skills":["cooking","teaching"],"available":True,"location":{"latitude":16.84,"longitude":74.56},"district":"Sangli","languages":["Marathi","Kannada","Hindi"]},
    {"id":"vol_008","name":"Vikram Chavan","phone":"+919876543217","skills":["medical","cooking","logistics"],"available":True,"location":{"latitude":16.71,"longitude":74.25},"district":"Kolhapur","languages":["Marathi","Hindi","English"]},
]


def load_embedded_sample_data() -> None:
    """Load hardcoded sample data into the store. Used as fallback on Vercel."""
    if _memory_store["surveys"]:
        return  # Already loaded
    for s in EMBEDDED_SURVEYS:
        save_survey(s)
    for v in EMBEDDED_VOLUNTEERS:
        save_volunteer(v)
    logger.info(f"Loaded {len(EMBEDDED_SURVEYS)} embedded surveys and {len(EMBEDDED_VOLUNTEERS)} embedded volunteers.")
