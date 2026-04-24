# 🗺️ VolunteerMap — Community Needs Intelligence Platform

> **Connecting communities to care through AI-powered insights**

VolunteerMap helps Indian NGOs turn scattered community survey data — including paper surveys — into an intelligent, real-time map of urgent local needs. It automatically matches available volunteers to the tasks where they are needed most, using Google's Gemini AI. The platform features OCR-powered paper survey digitisation via Cloud Vision API, K-Means geographic clustering to identify need hotspots, and a beautiful real-time dashboard for NGO coordinators.

Built as a production-ready solution for the **Google Solution Challenge 2026 — Build with AI** hackathon, VolunteerMap demonstrates how AI can bridge the gap between grassroots community data collection and effective volunteer deployment at scale.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                  Streamlit Dashboard (Python)                   │
│    ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────────┐   │
│    │Dashboard │ │Survey Form│ │OCR Upload│ │ AI Matching   │   │
│    │  + Map   │ │           │ │          │ │   Results     │   │
│    └────┬─────┘ └─────┬─────┘ └────┬─────┘ └───────┬───────┘   │
│         │             │            │               │            │
└─────────┼─────────────┼────────────┼───────────────┼────────────┘
          │   REST API  │            │               │
┌─────────┼─────────────┼────────────┼───────────────┼────────────┐
│         ▼             ▼            ▼               ▼            │
│                    FastAPI Backend (Python)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  /surveys/*  │  /volunteers/*  │  /dashboard/*  │ /health│   │
│  └──────┬───────┴────────┬────────┴───────┬────────┴────────┘   │
│         │                │                │                     │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐             │
│  │ ML Pipeline │  │   Gemini    │  │     OCR     │             │
│  │  (sklearn)  │  │  Matcher    │  │  Processor  │             │
│  │ - Urgency   │  │ (gemini-1.5 │  │ (Cloud      │             │
│  │ - K-Means   │  │  -flash)    │  │  Vision)    │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                  ┌───────▼───────┐                              │
│                  │   Firebase    │                              │
│                  │  Firestore DB │                              │
│                  └───────────────┘                              │
└─────────────────────────────────────────────────────────────────┘

Deployment:
  Backend  →  Google Cloud Run (Docker)
  Frontend →  Firebase Hosting
  Database →  Firebase Firestore (real-time)
```

---

## ✅ Prerequisites

Before setting up VolunteerMap, ensure you have:

| Requirement | Details |
|---|---|
| **Python** | 3.11 or higher |
| **Google Cloud Account** | With billing enabled |
| **Firebase Project** | Created in Firebase Console |
| **gcloud CLI** | Installed and authenticated |
| **API Keys** | Gemini, Cloud Vision, Google Maps |

---

## 🔑 How to Get API Keys

### Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key to your `.env` file

### Google Cloud Vision API
1. Go to [GCP Console → APIs & Services](https://console.cloud.google.com/apis/library)
2. Search for "Cloud Vision API" and enable it
3. Go to Credentials → Create Credentials → API Key

### Google Maps JavaScript API
1. Go to [GCP Console → APIs & Services](https://console.cloud.google.com/apis/library)
2. Search for "Maps JavaScript API" and enable it
3. Go to Credentials → Create Credentials → API Key

### Firebase Service Account
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project → Project Settings → Service Accounts
3. Click "Generate New Private Key"
4. Copy the JSON content to your `.env` file

---

## 🚀 Local Setup (Step-by-Step)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/volunteermap.git
cd volunteermap
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys (or leave defaults for demo mode)
```

### 3. Create virtual environment and install backend dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 4. Install frontend dependencies
```bash
pip install -r frontend/requirements.txt
```

### 5. Start the backend server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Verify the backend is running
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

### 7. Start the Streamlit frontend (in a new terminal)
```bash
cd frontend
streamlit run app.py
```

### 8. Open the dashboard
Navigate to `http://localhost:8501` in your browser.

> **💡 Demo Mode:** The app works without any API keys! It uses mock responses for Gemini AI matching and OCR processing, and stores data in-memory instead of Firestore.

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/surveys/submit` | Submit a new community need survey |
| `POST` | `/surveys/upload-csv` | Upload CSV file with multiple surveys |
| `POST` | `/surveys/ocr` | Extract survey from paper image (OCR) |
| `GET` | `/surveys/all` | Get all survey entries |
| `GET` | `/surveys/clusters` | Get K-Means clustered needs |
| `GET` | `/surveys/urgent` | Get top 10 most urgent needs |
| `POST` | `/volunteers/register` | Register a new volunteer |
| `GET` | `/volunteers/available` | Get all available volunteers |
| `POST` | `/volunteers/match` | Run AI matching for urgent needs |
| `GET` | `/dashboard/stats` | Get dashboard summary statistics |

**Interactive API docs:** `http://localhost:8000/docs` (Swagger UI)

---

## 🚢 Production Deployment

### One-command deploy:
```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
1. ✅ Check that `gcloud` CLI is installed and authenticated
2. 🐳 Build the backend Docker image
3. 📦 Push to Google Container Registry
4. ☁️ Deploy backend to Cloud Run (Mumbai region)
5. 🔧 Update frontend config with Cloud Run URL
6. 🌐 Deploy frontend to Firebase Hosting

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11 + FastAPI |
| ML Pipeline | scikit-learn, Pandas, NumPy |
| AI Matching | Google Gemini API (gemini-1.5-flash) |
| OCR | Google Cloud Vision API |
| Database | Firebase Firestore (real-time) |
| Authentication | Firebase Authentication |
| Frontend | Streamlit (Python) + Folium Maps |
| Deployment | Cloud Run (backend) + Firebase Hosting (frontend) |
| Environment | python-dotenv for secrets |

---

## 📸 Screenshots

> _Screenshots will be added after the first successful deployment._

| Dashboard | Survey Submission | OCR Upload | AI Matching |
|---|---|---|---|
| ![Dashboard](screenshots/dashboard.png) | ![Survey](screenshots/survey.png) | ![OCR](screenshots/ocr.png) | ![Matching](screenshots/matching.png) |

---

## 📂 Project Structure

```
volunteermap/
├── backend/
│   ├── main.py              # FastAPI app — all API endpoints
│   ├── ml_pipeline.py       # Urgency scoring + K-Means clustering
│   ├── gemini_matcher.py    # Gemini API volunteer matching
│   ├── ocr_processor.py     # Cloud Vision OCR for paper surveys
│   ├── firebase_client.py   # Firestore read/write helpers
│   ├── models.py            # Pydantic data models
│   ├── requirements.txt     # Backend dependencies
│   └── Dockerfile           # Cloud Run deployment
├── frontend/
│   ├── app.py               # Streamlit dashboard
│   ├── map_component.py     # Map embed helper (Folium)
│   └── requirements.txt     # Frontend dependencies
├── data/
│   └── sample_surveys.json  # 20 sample surveys + 8 volunteers
├── firebase/
│   └── firestore.rules      # Firestore security rules
├── .env.example             # Environment variable template
├── deploy.sh                # One-command deploy script
└── README.md                # This file
```

---

## 🏆 Built for

**Google Solution Challenge 2026 — Build with AI** 🚀

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
