"""
VolunteerMap — Streamlit Dashboard.

Interactive frontend for the Community Needs Intelligence Platform.
Connects to the FastAPI backend for data operations.

Built for Google Solution Challenge 2026 — Build with AI.
"""

import os
import sys
import json
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Ensure frontend directory is in path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="VolunteerMap — Community Needs Intelligence",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 700;
    margin-bottom: 0;
}

.tagline {
    color: #a0aec0;
    font-size: 1.1rem;
    margin-top: -10px;
    margin-bottom: 20px;
}

.metric-card {
    background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    color: #a0aec0;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.match-card {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    border-left: 4px solid #667eea;
    border: 1px solid rgba(255,255,255,0.06);
}

.priority-high { border-left-color: #E53E3E; }
.priority-medium { border-left-color: #ED8936; }
.priority-low { border-left-color: #38A169; }

.category-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29, #302b63, #24243e);
}
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def api_get(endpoint):
    """Make a GET request to the backend API."""
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to backend. Make sure the FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_post(endpoint, data=None, files=None):
    """Make a POST request to the backend API."""
    try:
        if files:
            resp = requests.post(f"{BACKEND_URL}{endpoint}", files=files, timeout=30)
        else:
            resp = requests.post(f"{BACKEND_URL}{endpoint}", json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to backend. Make sure the FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<h1 class="main-header">🗺️ VolunteerMap</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">Connecting communities to care</p>', unsafe_allow_html=True)
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "📝 Submit Survey", "📸 OCR Upload", "🤖 Volunteer Matching"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Built for Google Solution Challenge 2026")
    st.caption("Build with AI 🚀")


# ─── Dashboard Page ──────────────────────────────────────────────────────────

if page == "📊 Dashboard":
    st.markdown("## 📊 Community Needs Dashboard")
    st.markdown("Real-time intelligence on community needs across Maharashtra")
    st.markdown("")

    # Metrics Row
    with st.spinner("Loading dashboard stats..."):
        stats = api_get("/dashboard/stats")

    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 Total Surveys", stats.get("total_surveys", 0))
        with col2:
            st.metric("👥 Active Volunteers", stats.get("total_volunteers", 0))
        with col3:
            st.metric("🚨 Urgent Needs", stats.get("urgent_needs", 0))
        with col4:
            st.metric("📈 Avg Urgency", f"{stats.get('avg_urgency', 0):.1f}")

    st.markdown("")
    st.markdown("### 🗺️ Needs Hotspot Map")

    # Map
    with st.spinner("Clustering needs and generating map..."):
        cluster_data = api_get("/surveys/clusters")

    if cluster_data and cluster_data.get("clusters"):
        clusters = cluster_data["clusters"]

        try:
            import folium
            from streamlit_folium import st_folium
            from map_component import generate_folium_map

            survey_data = api_get("/surveys/all")
            all_surveys = survey_data.get("surveys", []) if survey_data else []
            m = generate_folium_map(clusters, all_surveys)
            st_folium(m, height=500, use_container_width=True)
        except ImportError:
            st.warning("Folium not installed. Showing cluster data as table.")
            for c in clusters:
                st.json(c)

        # Cluster summary
        st.markdown("### 📍 Cluster Summary")
        cluster_df = pd.DataFrame([
            {
                "Cluster": f"#{c['cluster_id'] + 1}",
                "Category": c["top_category"].title(),
                "Needs Count": c["count"],
                "Total Urgency": f"{c['total_urgency']:.1f}",
                "Lat": c["centroid"]["lat"],
                "Lng": c["centroid"]["lng"],
            }
            for c in clusters
        ])
        st.dataframe(cluster_df, width='stretch', hide_index=True)
    else:
        st.info("No cluster data available. Submit some surveys first!")

    # Urgent needs table
    st.markdown("### 🚨 Top 10 Urgent Needs")
    with st.spinner("Loading urgent needs..."):
        urgent_data = api_get("/surveys/urgent")

    if urgent_data and urgent_data.get("urgent_needs"):
        needs = urgent_data["urgent_needs"]
        df = pd.DataFrame([
            {
                "District": n.get("district", ""),
                "Category": n.get("category", "").title(),
                "Severity": "⭐" * n.get("severity", 0),
                "Affected": n.get("affected_count", 0),
                "Urgency Score": f"{n.get('urgency_score', 0):.1f}",
                "Description": n.get("description", "")[:80] + "...",
            }
            for n in needs
        ])
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No urgent needs found.")


# ─── Submit Survey Page ──────────────────────────────────────────────────────

elif page == "📝 Submit Survey":
    st.markdown("## 📝 Submit New Survey")
    st.markdown("Report a community need from the field")
    st.markdown("")

    with st.form("survey_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            district = st.selectbox(
                "District",
                ["Sangli", "Pune", "Kolhapur", "Solapur", "Nashik",
                 "Mumbai", "Nagpur", "Aurangabad", "Thane", "Satara"]
            )
            category = st.selectbox(
                "Category",
                ["healthcare", "food", "education", "sanitation", "employment"]
            )
            severity = st.slider("Severity Level", 1, 5, 3)

        with col2:
            latitude = st.number_input("Latitude", value=16.85, format="%.4f")
            longitude = st.number_input("Longitude", value=74.59, format="%.4f")
            affected_count = st.number_input("Affected People", min_value=1, value=50)

        description = st.text_area(
            "Description of Need",
            placeholder="Describe the community need in detail...",
            height=120,
        )

        submitted = st.form_submit_button("🚀 Submit Survey")

        if submitted:
            if not description:
                st.error("Please provide a description.")
            else:
                with st.spinner("Submitting survey and computing urgency..."):
                    payload = {
                        "location": {"latitude": latitude, "longitude": longitude},
                        "district": district,
                        "state": "Maharashtra",
                        "category": category,
                        "description": description,
                        "severity": severity,
                        "affected_count": affected_count,
                        "source": "digital_form",
                    }
                    result = api_post("/surveys/submit", data=payload)

                if result:
                    st.success(f"✅ Survey submitted! Urgency Score: **{result.get('urgency_score', 'N/A')}**")
                    st.balloons()


# ─── OCR Upload Page ─────────────────────────────────────────────────────────

elif page == "📸 OCR Upload":
    st.markdown("## 📸 OCR Paper Survey Upload")
    st.markdown("Upload a photo of a paper survey form for automatic extraction")
    st.markdown("")

    uploaded_file = st.file_uploader(
        "Upload survey image (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        help="Take a clear photo of the paper survey form",
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(uploaded_file, caption="Uploaded Survey", width="stretch")

        with col2:
            with st.spinner("🔍 Running OCR extraction..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                result = api_post("/surveys/ocr", files=files)

            if result and result.get("extracted_survey"):
                extracted = result["extracted_survey"]
                st.markdown("### Extracted Fields")

                st.markdown(f"**District:** {extracted.get('district', 'Unknown')}")
                st.markdown(f"**Category:** {extracted.get('category', 'Unknown').title()}")
                st.markdown(f"**Severity:** {'⭐' * extracted.get('severity', 3)}")
                st.markdown(f"**Affected Count:** {extracted.get('affected_count', 0)}")
                st.markdown(f"**Urgency Score:** {extracted.get('urgency_score', 0):.1f}")

                st.markdown("**Description:**")
                st.text(extracted.get("description", "")[:300])

                st.success("✅ Survey extracted and saved automatically!")


# ─── Volunteer Matching Page ─────────────────────────────────────────────────

elif page == "🤖 Volunteer Matching":
    st.markdown("## 🤖 AI-Powered Volunteer Matching")
    st.markdown("Let Gemini AI find the best volunteer for each urgent need")
    st.markdown("")

    # Show available volunteers
    with st.spinner("Loading volunteers..."):
        vol_data = api_get("/volunteers/available")

    if vol_data and vol_data.get("volunteers"):
        st.markdown(f"### 👥 Available Volunteers ({vol_data['count']})")
        vol_df = pd.DataFrame([
            {
                "Name": v.get("name", ""),
                "District": v.get("district", ""),
                "Skills": ", ".join(v.get("skills", [])),
                "Languages": ", ".join(v.get("languages", [])),
            }
            for v in vol_data["volunteers"]
        ])
        st.dataframe(vol_df, width='stretch', hide_index=True)
    else:
        st.warning("No volunteers available.")

    st.markdown("")

    if st.button("🚀 Run AI Matching", type="primary"):
        with st.spinner("🧠 Gemini AI is analyzing needs and matching volunteers..."):
            match_result = api_post("/volunteers/match")

        if match_result and match_result.get("matches"):
            st.success(f"✅ {match_result['count']} matches found!")
            st.markdown("### 📋 Match Assignments")

            for match in match_result["matches"]:
                priority = match.get("priority", "medium")
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                priority_class = f"priority-{priority}"

                st.markdown(f"""
                <div class="match-card {priority_class}">
                    <h4>{priority_emoji} {match.get('volunteer_name', 'Volunteer')}</h4>
                    <p><strong>Task:</strong> {match.get('task_summary', 'N/A')}</p>
                    <p><strong>Reason:</strong> {match.get('match_reason', 'N/A')}</p>
                    <p><strong>Travel:</strong> ~{match.get('estimated_travel_km', '?')} km | <strong>Priority:</strong> {priority.upper()}</p>
                </div>
                """, unsafe_allow_html=True)

                # Mock SMS preview
                with st.expander(f"📱 SMS Preview for {match.get('volunteer_name', 'Volunteer')}"):
                    st.code(
                        f"Hi {match.get('volunteer_name', 'Volunteer')}! "
                        f"You've been matched to a {priority} priority task: "
                        f"{match.get('task_summary', 'N/A')}. "
                        f"Estimated travel: {match.get('estimated_travel_km', '?')} km. "
                        f"Reply YES to accept. — VolunteerMap",
                        language=None,
                    )
        elif match_result:
            st.info(match_result.get("message", "No matches found."))
