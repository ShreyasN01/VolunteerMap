"""
Pydantic data models for VolunteerMap.

Defines the core data structures used throughout the application:
- Survey entries (community needs)
- Volunteer profiles
- Match assignments
- API response models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class Location(BaseModel):
    """Geographic coordinates for a location."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class SurveySubmit(BaseModel):
    """Schema for submitting a new survey entry."""
    location: Location
    district: str = Field(..., min_length=1, description="District name")
    state: str = Field(default="Maharashtra", description="State name")
    category: str = Field(
        ...,
        pattern="^(healthcare|food|education|sanitation|employment)$",
        description="Need category"
    )
    description: str = Field(..., min_length=5, description="Free text description of need")
    severity: int = Field(..., ge=1, le=5, description="Severity level 1-5")
    affected_count: int = Field(..., ge=1, description="Number of people affected")
    source: str = Field(
        default="digital_form",
        pattern="^(digital_form|paper_ocr|csv_upload|mobile_app)$",
        description="Data source type"
    )


class Survey(BaseModel):
    """Complete survey entry with computed fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    submitted_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of submission"
    )
    location: Location
    district: str
    state: str = "Maharashtra"
    category: str
    description: str
    severity: int = Field(ge=1, le=5)
    affected_count: int = Field(ge=1)
    source: str = "digital_form"  # Accepts: digital_form, paper_ocr, csv_upload, mobile_app
    urgency_score: float = Field(default=0.0, description="Computed urgency score")


class VolunteerRegister(BaseModel):
    """Schema for registering a new volunteer."""
    name: str = Field(..., min_length=2, description="Full name")
    phone: str = Field(..., min_length=10, description="Phone number")
    skills: List[str] = Field(
        ...,
        min_length=1,
        description="Skills list: medical, teaching, logistics, cooking, counselling"
    )
    available: bool = Field(default=True, description="Availability status")
    location: Location
    district: str = Field(..., min_length=1, description="District name")
    languages: List[str] = Field(
        default=["Hindi", "English"],
        description="Languages spoken"
    )


class Volunteer(BaseModel):
    """Complete volunteer profile."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    skills: List[str]
    available: bool = True
    location: Location
    district: str
    languages: List[str] = ["Hindi", "English"]


class MatchResult(BaseModel):
    """Result of AI-powered volunteer-need matching."""
    need_id: str
    volunteer_id: str
    volunteer_name: str
    task_summary: str
    match_reason: str
    estimated_travel_km: float
    priority: str = Field(pattern="^(high|medium|low)$")


class ClusterResult(BaseModel):
    """Result of K-Means geographic clustering."""
    cluster_id: int
    centroid: dict  # {"lat": float, "lng": float}
    surveys: List[dict]
    top_category: str
    total_urgency: float
    count: int


class DashboardStats(BaseModel):
    """Summary statistics for the dashboard."""
    total_surveys: int
    total_volunteers: int
    urgent_needs: int
    top_category: str
    avg_urgency: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
