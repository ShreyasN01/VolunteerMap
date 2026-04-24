"""
VolunteerMap — FastAPI Backend Application.

Main API server providing endpoints for survey management, volunteer
registration, AI-powered matching, OCR processing, and dashboard analytics.

Built for Google Solution Challenge 2026 — Build with AI.
"""

import os
import io
import csv
import json
import logging
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from models import (
    SurveySubmit, Survey, VolunteerRegister, Volunteer,
    MatchResult, ClusterResult, DashboardStats, HealthResponse,
)
from firebase_client import (
    save_survey, get_all_surveys, save_volunteer,
    get_available_volunteers, save_match_result, load_sample_data,
)
from ml_pipeline import compute_urgency_score, cluster_needs
from gemini_matcher import match_volunteers
from ocr_processor import extract_survey_from_image

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler: load sample data on startup."""
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "sample_surveys.json"
    )
    if os.path.exists(sample_path):
        load_sample_data(sample_path)
        logger.info("Sample data loaded on startup.")
    else:
        logger.warning(f"Sample data file not found at {sample_path}")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title="VolunteerMap API",
    description="Community Needs Intelligence Platform — Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint. Returns status ok if the server is running."""
    return {"status": "ok"}


# ─── Survey Endpoints ────────────────────────────────────────────────────────


@app.post("/surveys/submit", status_code=status.HTTP_201_CREATED, tags=["Surveys"])
async def submit_survey(survey_input: SurveySubmit):
    """
    Submit a new community need survey.

    Accepts survey data, computes urgency score via ML pipeline,
    and stores the entry in Firestore (or in-memory store in demo mode).
    """
    try:
        survey = Survey(
            location=survey_input.location,
            district=survey_input.district,
            state=survey_input.state,
            category=survey_input.category,
            description=survey_input.description,
            severity=survey_input.severity,
            affected_count=survey_input.affected_count,
            source=survey_input.source,
        )
        survey_dict = survey.model_dump()
        survey_dict["urgency_score"] = compute_urgency_score(survey_dict)

        survey_id = save_survey(survey_dict)
        logger.info(f"Survey submitted: {survey_id} | Urgency: {survey_dict['urgency_score']}")

        return {
            "message": "Survey submitted successfully",
            "survey_id": survey_id,
            "urgency_score": survey_dict["urgency_score"],
        }
    except Exception as e:
        logger.error(f"Error submitting survey: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit survey: {str(e)}",
        )


@app.post("/surveys/upload-csv", status_code=status.HTTP_201_CREATED, tags=["Surveys"])
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file containing multiple survey entries.

    Parses each row, computes urgency scores, and stores all entries.
    Expected CSV columns: district, state, category, description,
    severity, affected_count, latitude, longitude.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted.",
        )

    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        saved_count = 0
        errors = []

        for i, row in enumerate(reader):
            try:
                survey = Survey(
                    location={
                        "latitude": float(row.get("latitude", 0)),
                        "longitude": float(row.get("longitude", 0)),
                    },
                    district=row.get("district", "Unknown"),
                    state=row.get("state", "Maharashtra"),
                    category=row.get("category", "healthcare"),
                    description=row.get("description", ""),
                    severity=int(row.get("severity", 3)),
                    affected_count=int(row.get("affected_count", 1)),
                    source="csv_upload",
                )
                survey_dict = survey.model_dump()
                survey_dict["urgency_score"] = compute_urgency_score(survey_dict)
                save_survey(survey_dict)
                saved_count += 1
            except Exception as e:
                errors.append(f"Row {i + 1}: {str(e)}")

        return {
            "message": f"CSV processed: {saved_count} surveys saved",
            "saved_count": saved_count,
            "errors": errors,
        }
    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV: {str(e)}",
        )


@app.post("/surveys/ocr", status_code=status.HTTP_201_CREATED, tags=["Surveys"])
async def ocr_survey(file: UploadFile = File(...)):
    """
    Extract survey data from a paper survey image using OCR.

    Accepts JPG/PNG images, runs Google Cloud Vision OCR (or mock in demo mode),
    extracts survey fields, computes urgency score, and returns extracted data
    for user confirmation before saving.
    """
    if not file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG/PNG images are accepted.",
        )

    try:
        image_bytes = await file.read()
        extracted = extract_survey_from_image(image_bytes)
        extracted["urgency_score"] = compute_urgency_score(extracted)

        # Save to store
        save_survey(extracted)

        return {
            "message": "OCR extraction complete",
            "extracted_survey": extracted,
        }
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}",
        )


@app.get("/surveys/all", tags=["Surveys"])
async def get_surveys():
    """Return all survey entries from the data store."""
    try:
        surveys = get_all_surveys()
        return {"surveys": surveys, "count": len(surveys)}
    except Exception as e:
        logger.error(f"Error fetching surveys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch surveys: {str(e)}",
        )


@app.get("/surveys/clusters", tags=["Surveys"])
async def get_clusters():
    """
    Return K-Means clustered community needs.

    Runs the ML pipeline to cluster all surveys geographically,
    identifying hotspots of urgent needs.
    """
    try:
        surveys = get_all_surveys()
        if not surveys:
            return {"clusters": [], "message": "No surveys available for clustering."}

        clusters = cluster_needs(surveys)
        return {
            "clusters": clusters,
            "total_clusters": len(clusters),
            "total_surveys": len(surveys),
        }
    except Exception as e:
        logger.error(f"Clustering error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(e)}",
        )


@app.get("/surveys/urgent", tags=["Surveys"])
async def get_urgent_needs():
    """Return the top 10 most urgent community needs sorted by urgency score."""
    try:
        surveys = get_all_surveys()
        # Sort by urgency_score descending
        sorted_surveys = sorted(
            surveys,
            key=lambda s: float(s.get("urgency_score", 0)),
            reverse=True,
        )
        top_urgent = sorted_surveys[:10]
        return {"urgent_needs": top_urgent, "count": len(top_urgent)}
    except Exception as e:
        logger.error(f"Error fetching urgent needs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch urgent needs: {str(e)}",
        )


# ─── Volunteer Endpoints ─────────────────────────────────────────────────────


@app.post("/volunteers/register", status_code=status.HTTP_201_CREATED, tags=["Volunteers"])
async def register_volunteer(volunteer_input: VolunteerRegister):
    """Register a new volunteer with their skills, location, and availability."""
    try:
        volunteer = Volunteer(
            name=volunteer_input.name,
            phone=volunteer_input.phone,
            skills=volunteer_input.skills,
            available=volunteer_input.available,
            location=volunteer_input.location,
            district=volunteer_input.district,
            languages=volunteer_input.languages,
        )
        vol_dict = volunteer.model_dump()
        vol_id = save_volunteer(vol_dict)

        return {
            "message": "Volunteer registered successfully",
            "volunteer_id": vol_id,
        }
    except Exception as e:
        logger.error(f"Error registering volunteer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register volunteer: {str(e)}",
        )


@app.get("/volunteers/available", tags=["Volunteers"])
async def get_volunteers():
    """Get all currently available volunteers."""
    try:
        volunteers = get_available_volunteers()
        return {"volunteers": volunteers, "count": len(volunteers)}
    except Exception as e:
        logger.error(f"Error fetching volunteers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch volunteers: {str(e)}",
        )


@app.post("/volunteers/match", tags=["Volunteers"])
async def run_matching():
    """
    Run AI-powered volunteer-need matching.

    Fetches the most urgent community needs and available volunteers,
    then uses Gemini AI to produce optimal assignments.
    """
    try:
        surveys = get_all_surveys()
        volunteers = get_available_volunteers()

        if not surveys:
            return {"matches": [], "message": "No surveys available for matching."}
        if not volunteers:
            return {"matches": [], "message": "No volunteers available for matching."}

        # Get top urgent needs
        sorted_surveys = sorted(
            surveys,
            key=lambda s: float(s.get("urgency_score", 0)),
            reverse=True,
        )
        urgent_needs = sorted_surveys[:10]

        # Run Gemini matching
        matches = match_volunteers(urgent_needs, volunteers)

        # Save match results
        for match in matches:
            save_match_result(match)

        return {
            "matches": matches,
            "count": len(matches),
            "message": f"Matched {len(matches)} volunteers to urgent needs.",
        }
    except Exception as e:
        logger.error(f"Matching error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Volunteer matching failed: {str(e)}",
        )


# ─── Dashboard Endpoints ─────────────────────────────────────────────────────


@app.get("/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """
    Return summary statistics for the dashboard.

    Includes total surveys, active volunteers, count of urgent needs
    (urgency_score > 50), top category, and average urgency score.
    """
    try:
        surveys = get_all_surveys()
        volunteers = get_available_volunteers()

        if not surveys:
            return {
                "total_surveys": 0,
                "total_volunteers": len(volunteers),
                "urgent_needs": 0,
                "top_category": "N/A",
                "avg_urgency": 0.0,
            }

        urgency_scores = [float(s.get("urgency_score", 0)) for s in surveys]
        urgent_count = sum(1 for score in urgency_scores if score > 50)
        avg_urgency = round(sum(urgency_scores) / len(urgency_scores), 2) if urgency_scores else 0.0

        # Find top category
        from collections import Counter
        categories = [s.get("category", "unknown") for s in surveys]
        top_category = Counter(categories).most_common(1)[0][0] if categories else "N/A"

        return {
            "total_surveys": len(surveys),
            "total_volunteers": len(volunteers),
            "urgent_needs": urgent_count,
            "top_category": top_category,
            "avg_urgency": avg_urgency,
        }
    except Exception as e:
        logger.error(f"Error computing dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute stats: {str(e)}",
        )


# ─── Run with Uvicorn ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
