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
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler: load sample data on startup."""
    # Try multiple paths (works on both local dev and Vercel)
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sample_surveys.json"),
        os.path.join(os.path.dirname(__file__), "..", "data", "sample_surveys.json"),
        os.path.join(os.getcwd(), "data", "sample_surveys.json"),
        "/var/task/data/sample_surveys.json",  # Vercel serverless path
    ]
    loaded = False
    for sample_path in possible_paths:
        if os.path.exists(sample_path):
            load_sample_data(sample_path)
            logger.info(f"Sample data loaded from: {sample_path}")
            loaded = True
            break
    if not loaded:
        # Load embedded sample data as fallback
        from firebase_client import load_embedded_sample_data
        load_embedded_sample_data()
        logger.info("Loaded embedded sample data (Vercel fallback).")
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


# ─── Root & Health Check ─────────────────────────────────────────────────────


# ─── Auth & Session Management ───────────────────────────────────────────────

DEMO_ACCOUNTS = {
    "admin@volunteermap.org": {"pass": "admin123", "role": "admin", "name": "System Admin"},
    "sangli_lead@volunteermap.org": {"pass": "sangli123", "role": "lead", "name": "Sangli Coordinator"},
    "pune_lead@volunteermap.org": {"pass": "pune123", "role": "lead", "name": "Pune Coordinator"},
    "+919999999999": {"pass": "123456", "role": "field", "name": "Field Officer"},
    "google_demo": {"pass": "google", "role": "admin", "name": "Google User (Demo)"}
}

@app.post("/auth/login", tags=["Auth"])
async def login(credentials: dict):
    """
    Validate credentials and return user profile.
    Supports email, phone (+91...), or google_demo.
    """
    identity = credentials.get("identity")
    password = credentials.get("password")
    
    if identity in DEMO_ACCOUNTS and DEMO_ACCOUNTS[identity]["pass"] == password:
        user = DEMO_ACCOUNTS[identity].copy()
        user.pop("pass")
        user["token"] = f"demo_token_{identity}"
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials. Try admin@volunteermap.org / admin123"
    )

@app.delete("/volunteers/{volunteer_id}", tags=["Volunteers"])
async def remove_volunteer(volunteer_id: str):
    """Remove a volunteer profile."""
    success = firebase_client.delete_volunteer(volunteer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return {"status": "success", "message": "Volunteer deleted"}

@app.get("/", tags=["System"], response_class=HTMLResponse)
async def root():
    """Interactive Web Dashboard (Desktop Prototype) for VolunteerMap."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VolunteerMap | AI Community Intelligence</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #f9fafb; 
        min-height: 100vh;
    }
    .sidebar-gradient { background: rgba(15, 12, 41, 0.95); backdrop-filter: blur(10px); border-right: 1px solid rgba(255,255,255,0.05); }
    .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
    .nav-item { transition: all 0.2s ease; cursor: pointer; border-radius: 12px; color: rgba(255,255,255,0.6); }
    .nav-item:hover { background: rgba(255, 255, 255, 0.1); color: white; }
    .nav-item.active { background: rgba(255, 255, 255, 0.15); color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .tab-content { display: none; animation: fadeIn 0.4s ease; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    #map { height: 400px; border-radius: 24px; z-index: 10; border: 1px solid rgba(255,255,255,0.1); }
    .leaflet-tile { filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }
    .leaflet-container { background: #020617 !important; }
    #login-overlay { 
        position: fixed; inset: 0; z-index: 9999; 
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        display: flex; align-items: center; justify-content: center; 
    }
    .btn-cosmic { background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); transition: all 0.3s ease; }
    .btn-cosmic:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -5px rgba(0, 210, 255, 0.4); }
</style>
</head>
<body class="antialiased">
    <!-- Login Overlay -->
    <div id="login-overlay">
        <div class="glass p-12 rounded-[48px] w-full max-w-md space-y-10 border-white/10 text-center">
            <div class="space-y-4">
                <div class="w-20 h-20 bg-white/10 rounded-3xl flex items-center justify-center mx-auto border border-white/20 shadow-2xl">
                    <i class="fa-solid fa-map-location-dot text-4xl text-white"></i>
                </div>
                <div class="space-y-1">
                    <h2 class="text-3xl font-black text-white tracking-tight">VolunteerMap</h2>
                    <p class="text-[10px] text-indigo-400 font-black uppercase tracking-[0.2em]">AI Community Intelligence</p>
                </div>
            </div>
            
            <div class="space-y-4">
                <button onclick="mockGoogleLogin()" class="w-full flex items-center justify-center gap-3 bg-white text-black py-4 rounded-2xl font-bold hover:bg-gray-100 transition-all shadow-lg">
                    <img src="https://www.google.com/favicon.ico" class="w-5 h-5"> Sign in with Google
                </button>
                <button onclick="showPhoneLogin()" class="w-full flex items-center justify-center gap-3 bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 py-4 rounded-2xl font-bold hover:bg-indigo-600/30 transition-all">
                    <i class="fa-solid fa-phone"></i> Mobile Number Login
                </button>
                <div class="relative py-2">
                    <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-white/5"></div></div>
                    <div class="relative flex justify-center text-[10px] uppercase font-black text-gray-500 px-4">OR EMAIL ACCOUNT</div>
                </div>
                <div class="space-y-3">
                    <input id="login-email" type="text" placeholder="Email or Phone Number" class="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm focus:border-indigo-500 focus:bg-white/10 outline-none transition-all placeholder:text-gray-600">
                    <input id="login-pass" type="password" placeholder="Password" class="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm focus:border-indigo-500 focus:bg-white/10 outline-none transition-all placeholder:text-gray-600">
                    <button onclick="handleEmailLogin()" class="w-full py-5 btn-cosmic text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-2xl shadow-blue-500/20 mt-4">Access Intelligence Portal</button>
                </div>
            </div>
            
            <div class="p-6 bg-white/5 rounded-3xl border border-white/10">
                <p class="text-[9px] text-gray-500 font-black uppercase tracking-widest mb-3">System Access Codes</p>
                <div class="grid grid-cols-1 gap-2 text-[10px] text-gray-400 font-bold">
                    <div class="flex justify-between px-2"><span>Admin Email:</span> <span class="text-white">admin@volunteermap.org / admin123</span></div>
                    <div class="flex justify-between px-2 border-t border-white/5 pt-2"><span>Mobile Demo:</span> <span class="text-white">+919999999999 / 123456</span></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Dashboard Container -->
    <div id="main-dashboard" class="flex h-screen overflow-hidden hidden">
        <!-- Sidebar -->
        <aside class="w-72 sidebar-gradient flex flex-col p-6 space-y-8">
            <div class="flex items-center gap-3 px-2">
                <div class="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center border border-white/20">
                    <i class="fa-solid fa-map-location-dot text-xl text-white"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight text-white">VolunteerMap</h1>
                    <p class="text-[10px] text-white/50 font-bold tracking-widest uppercase">Community AI</p>
                </div>
            </div>

            <nav class="flex-1 space-y-1">
                <div onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-item active flex items-center gap-3 px-4 py-3 text-sm font-medium">
                    <i class="fa-solid fa-chart-pie w-5 text-red-500"></i> Dashboard
                </div>
                <div onclick="switchTab('surveys')" id="nav-surveys" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium">
                    <i class="fa-solid fa-clipboard-list w-5 text-amber-500"></i> Community Surveys
                </div>
                <div onclick="switchTab('volunteers')" id="nav-volunteers" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium">
                    <i class="fa-solid fa-users w-5 text-blue-500"></i> Volunteers
                </div>
                <div onclick="switchTab('matching')" id="nav-matching" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium">
                    <i class="fa-solid fa-wand-magic-sparkles w-5 text-indigo-500"></i> AI Matching
                </div>
                <div onclick="switchTab('register')" id="nav-register" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium">
                    <i class="fa-solid fa-user-plus w-5 text-teal-500"></i> Registration
                </div>
            </nav>

            <div class="pt-6 border-t border-white/10">
                <div onclick="logout()" class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-400 hover:text-white cursor-pointer transition-colors">
                    <i class="fa-solid fa-power-off w-5 text-rose-500"></i> Sign Out
                </div>
            </div>
        </aside>

        <!-- Main Content (Rest of dashboard same as before...) -->
        <main class="flex-1 overflow-y-auto bg-[#020617] p-8">
            <header class="flex justify-between items-center mb-8">
                <div>
                    <h2 id="page-title" class="text-3xl font-extrabold flex items-center gap-3">
                        <span id="page-icon">📊</span> <span id="page-text">Dashboard</span>
                    </h2>
                    <p id="page-subtitle" class="text-gray-500 text-sm mt-1">Real-time intelligence on community needs across Maharashtra</p>
                </div>
                <div id="user-profile" class="flex items-center gap-4 bg-white/5 border border-white/10 px-5 py-2.5 rounded-2xl">
                    <div class="text-right">
                        <p id="user-name" class="text-xs font-bold text-white">--</p>
                        <p id="user-role" class="text-[9px] font-black text-teal-500 uppercase">--</p>
                    </div>
                    <div class="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center font-black text-white shadow-xl shadow-indigo-500/20" id="user-initial">A</div>
                </div>
            </header>
            
            <!-- Dashboard Tab (rest of HTML injected same as before...) -->
            <div id="tab-dashboard" class="tab-content active space-y-8">
                <div class="flex gap-12 border-b border-gray-900 pb-8">
                    <div><p class="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">📋 Total Surveys</p><p class="text-5xl font-black text-white" id="stat-total-surveys">--</p></div>
                    <div><p class="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">👥 Active Volunteers</p><p class="text-5xl font-black text-white" id="stat-active-volunteers">--</p></div>
                    <div><p class="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">🚨 Urgent Needs</p><p class="text-5xl font-black text-rose-500" id="stat-urgent-needs">--</p></div>
                    <div><p class="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">📈 Avg Urgency</p><p class="text-5xl font-black text-white" id="stat-avg-urgency">--</p></div>
                </div>
                <div class="space-y-4">
                    <h3 class="text-xl font-bold flex items-center gap-2">🗺️ Needs Hotspot Map</h3>
                    <div id="map"></div>
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="glass p-8 rounded-[32px]"><h3 class="text-lg font-bold mb-6">Needs by Category</h3><div class="h-64"><canvas id="categoryChart"></canvas></div></div>
                    <div class="glass p-8 rounded-[32px]"><h3 class="text-lg font-bold mb-6">Critical Hotspots</h3><div id="urgent-list" class="space-y-3"></div></div>
                </div>
            </div>

            <div id="tab-surveys" class="tab-content glass rounded-3xl overflow-hidden"><table class="w-full text-left"><thead class="bg-white/5 border-b border-white/10 text-[10px] font-bold uppercase tracking-widest text-gray-500"><tr><th class="px-8 py-4">District</th><th class="px-4 py-4">Category</th><th class="px-4 py-4">Score</th><th class="px-4 py-4">Affected</th></tr></thead><tbody id="surveys-table-body" class="text-sm"></tbody></table></div>
            <div id="tab-volunteers" class="tab-content">
                <div id="volunteers-grid" class="grid grid-cols-1 md:grid-cols-3 gap-6"></div>
            </div>
            <div id="tab-matching" class="tab-content space-y-8"><div class="glass p-12 rounded-[40px] text-center space-y-6 border-indigo-500/20"><div class="w-20 h-20 bg-indigo-500 text-white rounded-[28px] flex items-center justify-center mx-auto text-3xl shadow-2xl shadow-indigo-500/30"><i class="fa-solid fa-bolt-lightning"></i></div><h3 class="text-2xl font-bold">AI Matching Engine</h3><button id="btn-run-match" onclick="runAIMatch()" class="bg-indigo-500 text-white px-12 py-4 rounded-2xl font-bold hover:scale-105 transition-all">🚀 Run AI Matching</button><div id="matching-loader" class="hidden animate-pulse text-indigo-400 font-bold">AI is analyzing community needs...</div></div><div id="matches-results" class="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20"></div></div>
            <div id="tab-register" class="tab-content max-w-xl mx-auto glass p-10 rounded-[32px]"><h3 class="text-xl font-bold mb-8">📝 Submit New Survey</h3><form id="survey-form" onsubmit="event.preventDefault(); submitNewSurvey();" class="space-y-6"><select name="district" required class="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm"><option value="Sangli">Sangli</option><option value="Pune">Pune</option><option value="Kolhapur">Kolhapur</option><option value="Solapur">Solapur</option><option value="Nashik">Nashik</option></select><select name="category" required class="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm"><option value="healthcare">Healthcare</option><option value="food">Food</option><option value="education">Education</option><option value="sanitation">Sanitation</option></select><textarea name="description" required class="w-full h-32 bg-white/5 border border-white/10 rounded-xl p-4 text-sm" placeholder="Detailed description..."></textarea><button type="submit" class="w-full py-4 bg-teal-500 text-white rounded-2xl font-bold shadow-xl shadow-teal-500/20">Submit to Cloud</button></form></div>
        </main>
    </div>

    <script>
        let map, chartInstance;
        let currentUser = null;

        async function handleEmailLogin() {
            const identity = document.getElementById('login-email').value;
            const password = document.getElementById('login-pass').value;
            performLogin(identity, password);
        }

        async function mockGoogleLogin() {
            const btn = document.querySelector('button[onclick="mockGoogleLogin()"]');
            const original = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-circle-notch animate-spin"></i> Connecting...';
            btn.disabled = true;
            
            setTimeout(() => {
                btn.innerHTML = original;
                btn.disabled = false;
                performLogin('google_demo', 'google');
            }, 1000);
        }

        async function showPhoneLogin() {
            const phone = prompt('📞 Enter demo mobile number:', '+919999999999');
            if (!phone) return;
            const code = prompt('🔑 Enter 6-digit OTP:', '123456');
            if (phone && code) performLogin(phone, code);
        }

        async function performLogin(identity, password) {
            console.log('Attempting login for:', identity);
            try {
                const res = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ identity, password })
                });
                
                if (!res.ok) {
                    const errData = await res.json();
                    throw new Error(errData.detail || 'Authentication failed');
                }
                
                const user = await res.json();
                console.log('Login successful:', user.name);
                currentUser = user;
                localStorage.setItem('vm_user', JSON.stringify(user));
                document.getElementById('login-overlay').style.display = 'none';
                document.getElementById('main-dashboard').style.display = 'flex';
                initDashboard();
            } catch (e) { 
                console.error('Auth Error:', e);
                alert('❌ Login Failed: ' + e.message); 
            }
        }

        function initDashboard() {
            document.getElementById('user-name').innerText = currentUser.name;
            document.getElementById('user-role').innerText = currentUser.role;
            document.getElementById('user-initial').innerText = currentUser.name[0];
            initMap();
            fetchData();
        }

        function logout() {
            localStorage.removeItem('vm_user');
            window.location.reload();
        }

        // ... initMap, updateMap, switchTab, fetchData, updateChart, fetchUrgent, etc. same as before ...
        function initMap() {
            if (map) return;
            map = L.map('map', { zoomControl: false }).setView([18.5204, 73.8567], 7);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
            L.control.zoom({ position: 'bottomright' }).addTo(map);
        }

        async function updateMap() {
            const res = await fetch('/surveys/clusters');
            const data = await res.json();
            data.clusters.forEach(c => {
                L.circleMarker([c.centroid.lat, c.centroid.lng], { radius: 10 + (c.count * 2), fillColor: '#22c55e', color: '#fff', weight: 2, fillOpacity: 0.8 }).addTo(map);
            });
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            document.getElementById('nav-' + tabId).classList.add('active');
            
            const titles = {
                'dashboard': ['📊', 'Dashboard', 'Real-time intelligence on community needs'],
                'surveys': ['📋', 'Community Surveys', 'Detailed record of submitted field reports'],
                'volunteers': ['👥', 'Volunteers', 'Manage and track available community responders'],
                'matching': ['🪄', 'AI Matching', 'Intelligent task assignment via Gemini'],
                'register': ['📝', 'Registration', 'Directly enter new field data into the cloud']
            };
            
            if (titles[tabId]) {
                document.getElementById('page-icon').innerText = titles[tabId][0];
                document.getElementById('page-text').innerText = titles[tabId][1];
                document.getElementById('page-subtitle').innerText = titles[tabId][2];
            }

            if (tabId === 'dashboard') { setTimeout(() => map.invalidateSize(), 100); fetchData(); }
            if (tabId === 'surveys') fetchSurveys();
            if (tabId === 'volunteers') fetchVolunteers();
        }

        async function fetchData() {
            const res = await fetch('/dashboard/stats');
            const data = await res.json();
            document.getElementById('stat-total-surveys').innerText = data.total_surveys;
            document.getElementById('stat-active-volunteers').innerText = data.active_volunteers || data.total_volunteers;
            document.getElementById('stat-urgent-needs').innerText = data.urgent_needs || data.urgent_count;
            document.getElementById('stat-avg-urgency').innerText = (data.avg_urgency || 0).toFixed(1);
            updateChart(data.category_breakdown);
            updateMap();
            fetchUrgent();
        }

        function updateChart(data) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            if (chartInstance) chartInstance.destroy();
            chartInstance = new Chart(ctx, { type: 'bar', data: { labels: Object.keys(data).map(k => k.toUpperCase()), datasets: [{ data: Object.values(data), backgroundColor: ['#f43f5e', '#f59e0b', '#3b82f6', '#10b981'], borderRadius: 12 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { display: false }, x: { grid: { display: false }, ticks: { color: '#4b5563', font: { weight: 'bold' } } } } } });
        }

        async function fetchUrgent() {
            const res = await fetch('/surveys/urgent');
            const data = await res.json();
            const list = document.getElementById('urgent-list'); list.innerHTML = '';
            (data.urgent_needs || []).slice(0, 4).forEach(n => { list.innerHTML += `<div class="flex justify-between items-center bg-white/5 p-4 rounded-2xl border border-white/5"><div class="flex gap-3 items-center"><div class="w-2 h-2 bg-rose-500 rounded-full animate-pulse"></div><div><p class="text-sm font-bold">${n.district}</p><p class="text-[10px] text-gray-500 font-bold uppercase">${n.category}</p></div></div><p class="text-lg font-black">${n.urgency_score.toFixed(0)}</p></div>`; });
        }

        async function fetchSurveys() {
            const res = await fetch('/surveys/all');
            const data = await res.json();
            const body = document.getElementById('surveys-table-body'); body.innerHTML = '';
            (data.surveys || []).forEach(s => { body.innerHTML += `<tr class="border-b border-white/5"><td class="px-8 py-4 font-bold">${s.district}</td><td class="px-4 py-4 uppercase text-xs font-bold text-gray-500">${s.category}</td><td class="px-4 py-4 font-mono font-black">${s.urgency_score.toFixed(1)}</td><td class="px-4 py-4">${s.affected_count}</td></tr>`; });
        }

        async function fetchVolunteers() {
            const res = await fetch('/volunteers/available');
            const data = await res.json();
            const grid = document.getElementById('volunteers-grid'); grid.innerHTML = '';
            (data.volunteers || []).forEach(v => { 
                grid.innerHTML += `<div class="glass p-6 rounded-3xl space-y-4 border-white/5 relative">
                    <button onclick="deleteVolunteer('${v.id}')" class="absolute top-4 right-4 transition-all w-8 h-8 bg-rose-500/10 text-rose-500 rounded-lg hover:bg-rose-500 hover:text-white flex items-center justify-center">
                        <i class="fa-solid fa-trash-can text-xs"></i>
                    </button>
                    <div class="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center font-bold">${v.name[0]}</div>
                    <div><p class="font-bold">${v.name}</p><p class="text-xs text-gray-500">${v.district}</p></div>
                    <div class="flex flex-wrap gap-2">${v.skills.map(s => `<span class="text-[9px] px-2 py-1 bg-white/5 rounded-lg border border-white/10 text-gray-400 font-bold uppercase tracking-wider">${s}</span>`).join('')}</div>
                </div>`; 
            });
        }

        async function deleteVolunteer(id) {
            if (!confirm('Are you sure you want to remove this volunteer?')) return;
            const res = await fetch(`/volunteers/${id}`, { method: 'DELETE' });
            if (res.ok) { fetchData(); fetchVolunteers(); }
            else { alert('Failed to delete'); }
        }

        async function runAIMatch() {
            const loader = document.getElementById('matching-loader'); const btn = document.getElementById('btn-run-match'); const results = document.getElementById('matches-results');
            loader.classList.remove('hidden'); btn.classList.add('hidden'); results.innerHTML = '';
            try {
                const res = await fetch('/volunteers/match', { method: 'POST' }); const data = await res.json();
                setTimeout(() => { loader.classList.add('hidden'); btn.classList.remove('hidden'); (data.matches || []).forEach(m => { results.innerHTML += `<div class="glass p-8 rounded-[32px] border-l-4 border-indigo-500 space-y-4"><div class="flex justify-between items-start"><div><h4 class="text-lg font-bold">${m.volunteer_name}</h4><p class="text-xs text-indigo-400 font-bold uppercase">${m.need_category}</p></div><span class="text-[10px] px-3 py-1 bg-white/10 rounded-lg font-black uppercase">${m.priority}</span></div><p class="text-sm text-gray-400 italic">"${m.task_summary}"</p><div class="bg-indigo-500/10 p-4 rounded-xl text-xs text-gray-400"><i class="fa-solid fa-sparkles mr-2 text-indigo-400"></i>${m.match_reason}</div><div class="flex justify-between text-[10px] font-bold text-gray-600"><span>DISTANCE: ${m.distance || m.estimated_travel_km}KM</span><span>MATCH: ${(m.match_score * 100).toFixed(0)}%</span></div></div>`; }); }, 1000);
            } catch (e) { loader.classList.add('hidden'); btn.classList.remove('hidden'); }
        }

        async function submitNewSurvey() {
            const form = document.getElementById('survey-form'); const formData = new FormData(form);
            const data = { location: { latitude: 18.5, longitude: 73.8 }, district: formData.get('district'), state: "Maharashtra", category: formData.get('category'), description: formData.get('description'), severity: 3, affected_count: 10, source: "digital_form" };
            await fetch('/surveys/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            alert('Success!'); form.reset(); switchTab('dashboard');
        }

        window.onload = () => {
            const savedUser = localStorage.getItem('vm_user');
            if (savedUser) {
                currentUser = JSON.parse(savedUser);
                document.getElementById('login-overlay').style.display = 'none';
                document.getElementById('main-dashboard').style.display = 'flex';
                initDashboard();
            }
        };
    </script>
</body>
</html>"""



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
        category_counts = dict(Counter(categories))

        return {
            "total_surveys": len(surveys),
            "total_volunteers": len(volunteers),
            "active_volunteers": len(volunteers),
            "urgent_needs": urgent_count,
            "urgent_count": urgent_count,
            "top_category": top_category,
            "avg_urgency": avg_urgency,
            "category_breakdown": {
                "healthcare": category_counts.get("healthcare", 0),
                "food": category_counts.get("food", 0),
                "education": category_counts.get("education", 0),
                "sanitation": category_counts.get("sanitation", 0),
                "employment": category_counts.get("employment", 0),
            },
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
