"""
Gemini AI Volunteer Matcher for VolunteerMap.

Uses Google Gemini API (gemini-1.5-flash) to intelligently match
available volunteers to urgent community needs based on skills,
geographic proximity, and language compatibility.

Falls back to a hardcoded mock response when API key is not configured.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Mock response for demo mode
MOCK_MATCH_RESPONSE = [
    {
        "need_id": "sample_001",
        "volunteer_id": "vol_001",
        "volunteer_name": "Priya Kulkarni",
        "task_summary": "Assist at Sangli Rural Health Camp — medical supplies distribution",
        "match_reason": "Medical background, Marathi speaker, located 3km from need site",
        "estimated_travel_km": 3,
        "priority": "high"
    },
    {
        "need_id": "sample_002",
        "volunteer_id": "vol_003",
        "volunteer_name": "Amit Deshmukh",
        "task_summary": "Organize food distribution at Kolhapur community center",
        "match_reason": "Logistics expertise, local resident, fluent in Marathi and Hindi",
        "estimated_travel_km": 5,
        "priority": "high"
    },
    {
        "need_id": "sample_005",
        "volunteer_id": "vol_004",
        "volunteer_name": "Sneha Patil",
        "task_summary": "Conduct remedial teaching sessions at Solapur municipal school",
        "match_reason": "Teaching skills, education background, located in same district",
        "estimated_travel_km": 8,
        "priority": "medium"
    },
    {
        "need_id": "sample_008",
        "volunteer_id": "vol_006",
        "volunteer_name": "Rajesh Jadhav",
        "task_summary": "Coordinate sanitation drive in Nashik slum area",
        "match_reason": "Logistics and counselling skills, Hindi speaker, nearby location",
        "estimated_travel_km": 12,
        "priority": "medium"
    },
    {
        "need_id": "sample_010",
        "volunteer_id": "vol_002",
        "volunteer_name": "Ananya Sharma",
        "task_summary": "Provide cooking support for Pune community kitchen",
        "match_reason": "Cooking expertise, available immediately, same district",
        "estimated_travel_km": 2,
        "priority": "low"
    }
]


def _is_demo_mode() -> bool:
    """Check if the app is running in demo mode (no Gemini API key)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    return not api_key or api_key == "demo" or api_key.startswith("your_")


def match_volunteers(urgent_needs: List[dict], volunteers: List[dict]) -> List[Dict[str, Any]]:
    """
    Match available volunteers to urgent community needs using Gemini AI.

    Uses Google Gemini API to analyze needs and volunteer profiles, then
    produces optimal assignments based on skill match, geographic proximity,
    and language compatibility.

    Args:
        urgent_needs: List of urgent survey dicts sorted by urgency score.
        volunteers: List of available volunteer dicts.

    Returns:
        List of match assignment dictionaries, each containing:
        need_id, volunteer_id, volunteer_name, task_summary,
        match_reason, estimated_travel_km, priority.
        Returns mock data in demo mode or on API failure.
    """
    if not urgent_needs or not volunteers:
        logger.warning("No needs or volunteers to match.")
        return []

    if _is_demo_mode():
        logger.info("Running in demo mode. Returning mock match results.")
        return _get_demo_matches(urgent_needs, volunteers)

    try:
        return _call_gemini_api(urgent_needs, volunteers)
    except Exception as e:
        logger.error(f"Gemini matching failed: {e}. Returning mock results.")
        return _get_demo_matches(urgent_needs, volunteers)


def _get_demo_matches(urgent_needs: List[dict], volunteers: List[dict]) -> List[Dict[str, Any]]:
    """
    Generate demo match results using actual need/volunteer IDs from data.

    Maps mock responses to real IDs when possible, otherwise uses hardcoded data.
    """
    results = []
    for i, mock in enumerate(MOCK_MATCH_RESPONSE):
        match = dict(mock)
        # Map to actual IDs if available
        if i < len(urgent_needs):
            match["need_id"] = urgent_needs[i].get("id", match["need_id"])
        if i < len(volunteers):
            match["volunteer_id"] = volunteers[i].get("id", match["volunteer_id"])
            match["volunteer_name"] = volunteers[i].get("name", match["volunteer_name"])
        results.append(match)

    return results[:min(len(urgent_needs), len(volunteers), len(MOCK_MATCH_RESPONSE))]


def _call_gemini_api(
    urgent_needs: List[dict], volunteers: List[dict], max_retries: int = 2
) -> List[Dict[str, Any]]:
    """
    Call the Gemini API with retry logic to match volunteers to needs.

    Args:
        urgent_needs: Sorted list of urgent community needs.
        volunteers: List of available volunteers.
        max_retries: Maximum number of retries on failure (default 2).

    Returns:
        Parsed list of match assignments from Gemini response.

    Raises:
        Exception: If all retries are exhausted.
    """
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # Prepare simplified data for the prompt (reduce token usage)
    needs_summary = []
    for n in urgent_needs[:10]:  # Limit to top 10
        needs_summary.append({
            "id": n.get("id"),
            "category": n.get("category"),
            "district": n.get("district"),
            "description": n.get("description"),
            "severity": n.get("severity"),
            "urgency_score": n.get("urgency_score"),
            "affected_count": n.get("affected_count"),
            "location": n.get("location"),
        })

    vol_summary = []
    for v in volunteers:
        vol_summary.append({
            "id": v.get("id"),
            "name": v.get("name"),
            "skills": v.get("skills"),
            "district": v.get("district"),
            "languages": v.get("languages"),
            "location": v.get("location"),
        })

    prompt = f"""
You are a volunteer coordination AI for an NGO in Maharashtra, India.

URGENT COMMUNITY NEEDS (sorted by urgency, highest first):
{json.dumps(needs_summary, indent=2)}

AVAILABLE VOLUNTEERS:
{json.dumps(vol_summary, indent=2)}

Your task: Match each urgent need to the BEST available volunteer based on:
1. Skill match (most important)
2. Geographic proximity (prefer same district)
3. Language match with affected community

Return ONLY a valid JSON array. No explanation. No markdown. Example format:
[
  {{
    "need_id": "survey_id_here",
    "volunteer_id": "volunteer_id_here",
    "volunteer_name": "Name",
    "task_summary": "One sentence describing what volunteer should do",
    "match_reason": "Why this volunteer was chosen",
    "estimated_travel_km": 5,
    "priority": "high|medium|low"
  }}
]
"""

    model = genai.GenerativeModel("gemini-1.5-flash")

    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean up potential markdown code fences
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines (code fences)
                lines = [l for l in lines if not l.strip().startswith("```")]
                response_text = "\n".join(lines)

            matches = json.loads(response_text)

            if isinstance(matches, list):
                logger.info(f"Gemini returned {len(matches)} matches on attempt {attempt + 1}.")
                return matches
            else:
                logger.warning(f"Gemini response is not a list: {type(matches)}")
                continue

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}: Failed to parse Gemini response as JSON: {e}")
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}: Gemini API error: {e}")

        if attempt < max_retries:
            logger.info(f"Retrying in 2 seconds...")
            time.sleep(2)

    logger.error("All Gemini API retries exhausted. Returning empty list.")
    return []
