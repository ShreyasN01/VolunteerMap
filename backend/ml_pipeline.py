"""
ML Pipeline for VolunteerMap.

Provides urgency scoring for community needs and K-Means geographic clustering
to identify hotspots of urgent needs across districts.
"""

import math
import logging
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter

from dateutil.parser import parse as parse_date

logger = logging.getLogger(__name__)

# Category weights reflect the relative urgency of different need types
CATEGORY_WEIGHTS = {
    "healthcare": 10,
    "food": 8,
    "sanitation": 7,
    "education": 6,
    "employment": 4,
}


def compute_urgency_score(survey: dict) -> float:
    """
    Compute an urgency score for a given survey entry.

    The score is based on:
    - Category weight (healthcare is most urgent)
    - Severity level (1-5)
    - Number of affected people (logarithmic scale)
    - Recency boost (surveys from last 7 days get 1.3x multiplier)

    Args:
        survey: Dictionary containing survey fields including category,
                severity, affected_count, and submitted_at.

    Returns:
        Computed urgency score as a float, rounded to 2 decimal places.
    """
    try:
        category = survey.get("category", "healthcare")
        base = CATEGORY_WEIGHTS.get(category, 5)

        severity = int(survey.get("severity", 3))
        affected_count = int(survey.get("affected_count", 1))

        score = base * severity * math.log1p(affected_count)

        # Recency boost: surveys from last 7 days get 1.3x multiplier
        submitted_at = survey.get("submitted_at", datetime.now().isoformat())
        try:
            submitted_date = parse_date(submitted_at)
            # Make both timezone-naive for comparison
            if submitted_date.tzinfo is not None:
                submitted_date = submitted_date.replace(tzinfo=None)
            days_old = (datetime.now() - submitted_date).days
        except (ValueError, TypeError):
            days_old = 0

        recency = 1.3 if days_old <= 7 else 1.0

        return round(score * recency, 2)

    except Exception as e:
        logger.error(f"Error computing urgency score: {e}")
        return 0.0


def cluster_needs(surveys: List[dict]) -> List[Dict[str, Any]]:
    """
    Cluster survey entries geographically using K-Means.

    Groups nearby community needs into geographic clusters to identify
    hotspots. Each cluster includes summary statistics.

    Args:
        surveys: List of survey dictionaries with location data.

    Returns:
        List of cluster dictionaries sorted by total_urgency descending.
        Each cluster contains: cluster_id, centroid, surveys, top_category,
        total_urgency, and count.
        Returns empty list if input is empty or has no valid coordinates.
    """
    if not surveys:
        logger.warning("No surveys provided for clustering.")
        return []

    # Filter out surveys with missing or invalid coordinates
    valid_surveys = []
    for s in surveys:
        loc = s.get("location", {})
        if isinstance(loc, dict):
            lat = loc.get("latitude")
            lng = loc.get("longitude")
        else:
            continue

        if lat is not None and lng is not None:
            try:
                lat = float(lat)
                lng = float(lng)
                valid_surveys.append(s)
            except (ValueError, TypeError):
                logger.warning(f"Skipping survey {s.get('id', 'unknown')}: invalid coordinates")
                continue

    if not valid_surveys:
        logger.warning("No surveys with valid coordinates for clustering.")
        return []

    try:
        import numpy as np
        from sklearn.cluster import KMeans

        # Extract coordinates
        coords = np.array([
            [
                float(s["location"]["latitude"]),
                float(s["location"]["longitude"])
            ]
            for s in valid_surveys
        ])

        # Determine number of clusters (max 5, min 1, at most len(valid_surveys))
        n_clusters = min(5, len(valid_surveys))
        if n_clusters < 1:
            return []

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)

        # Build cluster results
        clusters = []
        for cluster_id in range(n_clusters):
            cluster_surveys = [
                valid_surveys[i] for i in range(len(valid_surveys)) if labels[i] == cluster_id
            ]

            if not cluster_surveys:
                continue

            centroid = kmeans.cluster_centers_[cluster_id]

            # Determine top category in this cluster
            categories = [s.get("category", "unknown") for s in cluster_surveys]
            category_counts = Counter(categories)
            top_category = category_counts.most_common(1)[0][0]

            # Sum urgency scores
            total_urgency = sum(
                float(s.get("urgency_score", 0)) for s in cluster_surveys
            )

            clusters.append({
                "cluster_id": cluster_id,
                "centroid": {
                    "lat": round(float(centroid[0]), 6),
                    "lng": round(float(centroid[1]), 6),
                },
                "surveys": cluster_surveys,
                "top_category": top_category,
                "total_urgency": round(total_urgency, 2),
                "count": len(cluster_surveys),
            })

        # Sort by total_urgency descending
        clusters.sort(key=lambda c: c["total_urgency"], reverse=True)

        logger.info(f"Clustered {len(valid_surveys)} surveys into {len(clusters)} clusters.")
        return clusters

    except ImportError as e:
        logger.error(f"scikit-learn not installed: {e}")
        return []
    except Exception as e:
        logger.error(f"Error during clustering: {e}")
        return []
