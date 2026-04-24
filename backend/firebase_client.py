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
