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
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #030712; color: #f9fafb; }
    .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
    .nav-item { transition: all 0.2s ease; cursor: pointer; border-radius: 12px; }
    .nav-item:hover { background: rgba(20, 184, 166, 0.1); color: #14b8a6; }
    .nav-item.active { background: #14b8a6; color: white; box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3); }
    .tab-content { display: none; animation: fadeIn 0.4s ease; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .card-hover:hover { transform: translateY(-4px); border-color: rgba(20, 184, 166, 0.4); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #030712; }
    ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #374151; }
</style>
</head>
<body class="antialiased">
    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
        <aside class="w-72 glass border-r border-gray-800 flex flex-col p-6 space-y-8">
            <div class="flex items-center gap-3 px-2">
                <div class="w-10 h-10 bg-teal-500 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/20">
                    <i class="fa-solid fa-map-location-dot text-xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight">VolunteerMap</h1>
                    <p class="text-[10px] text-teal-500 font-bold tracking-widest uppercase">Community AI</p>
                </div>
            </div>

            <nav class="flex-1 space-y-1">
                <div onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-item active flex items-center gap-3 px-4 py-3 text-sm font-medium">
                    <i class="fa-solid fa-chart-pie w-5"></i> Dashboard
                </div>
                <div onclick="switchTab('surveys')" id="nav-surveys" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-400">
                    <i class="fa-solid fa-clipboard-list w-5"></i> Community Surveys
                </div>
                <div onclick="switchTab('volunteers')" id="nav-volunteers" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-400">
                    <i class="fa-solid fa-users w-5"></i> Volunteers
                </div>
                <div onclick="switchTab('matching')" id="nav-matching" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-400">
                    <i class="fa-solid fa-wand-magic-sparkles w-5"></i> AI Matching
                </div>
                <div onclick="switchTab('register')" id="nav-register" class="nav-item flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-400">
                    <i class="fa-solid fa-user-plus w-5"></i> Registration
                </div>
            </nav>

            <div class="pt-6 border-t border-gray-800">
                <div class="bg-gray-900/50 rounded-2xl p-4 border border-gray-800">
                    <p class="text-xs text-gray-500 mb-1">System Status</p>
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span class="text-xs font-bold text-gray-300">API Live v1.0.0</span>
                    </div>
                </div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 overflow-y-auto bg-[#020617] p-8">
            <!-- Header -->
            <header class="flex justify-between items-center mb-8">
                <div>
                    <h2 id="page-title" class="text-2xl font-bold">Dashboard Overview</h2>
                    <p id="page-subtitle" class="text-gray-500 text-sm">Real-time community intelligence and analytics</p>
                </div>
                <div class="flex items-center gap-4">
                    <button onclick="fetchData()" class="p-2 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors">
                        <i class="fa-solid fa-rotate text-gray-400"></i>
                    </button>
                    <div class="h-8 w-[1px] bg-gray-800"></div>
                    <div class="flex items-center gap-3 bg-gray-900 px-4 py-2 rounded-xl border border-gray-800">
                        <div class="w-8 h-8 bg-indigo-500/20 text-indigo-500 rounded-lg flex items-center justify-center font-bold">A</div>
                        <span class="text-sm font-semibold">Admin Panel</span>
                    </div>
                </div>
            </header>

            <!-- Dashboard Tab -->
            <div id="tab-dashboard" class="tab-content active space-y-8">
                <!-- Stats Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div class="glass p-6 rounded-3xl space-y-4">
                        <div class="flex justify-between items-start">
                            <div class="p-3 bg-blue-500/10 text-blue-500 rounded-2xl"><i class="fa-solid fa-clipboard-check text-xl"></i></div>
                            <span class="text-xs font-bold text-blue-500 bg-blue-500/10 px-2 py-1 rounded-lg">+12%</span>
                        </div>
                        <div>
                            <p class="text-3xl font-black" id="stat-total-surveys">--</p>
                            <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">Total Surveys</p>
                        </div>
                    </div>
                    <div class="glass p-6 rounded-3xl space-y-4">
                        <div class="flex justify-between items-start">
                            <div class="p-3 bg-teal-500/10 text-teal-500 rounded-2xl"><i class="fa-solid fa-user-group text-xl"></i></div>
                            <span class="text-xs font-bold text-teal-500 bg-teal-500/10 px-2 py-1 rounded-lg">Active</span>
                        </div>
                        <div>
                            <p class="text-3xl font-black" id="stat-active-volunteers">--</p>
                            <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">Volunteers</p>
                        </div>
                    </div>
                    <div class="glass p-6 rounded-3xl space-y-4">
                        <div class="flex justify-between items-start">
                            <div class="p-3 bg-rose-500/10 text-rose-500 rounded-2xl"><i class="fa-solid fa-triangle-exclamation text-xl"></i></div>
                            <span class="text-xs font-bold text-rose-500 bg-rose-500/10 px-2 py-1 rounded-lg">Urgent</span>
                        </div>
                        <div>
                            <p class="text-3xl font-black" id="stat-urgent-needs">--</p>
                            <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">Urgent Needs</p>
                        </div>
                    </div>
                    <div class="glass p-6 rounded-3xl space-y-4">
                        <div class="flex justify-between items-start">
                            <div class="p-3 bg-amber-500/10 text-amber-500 rounded-2xl"><i class="fa-solid fa-fire text-xl"></i></div>
                            <span class="text-xs font-bold text-amber-500 bg-amber-500/10 px-2 py-1 rounded-lg">Avg</span>
                        </div>
                        <div>
                            <p class="text-3xl font-black" id="stat-avg-urgency">--</p>
                            <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">Avg Urgency</p>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Chart -->
                    <div class="lg:col-span-2 glass p-8 rounded-3xl">
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-lg font-bold">Needs Category Breakdown</h3>
                            <div class="flex gap-2">
                                <span class="w-3 h-3 bg-teal-500 rounded-full"></span>
                                <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Live Distribution</span>
                            </div>
                        </div>
                        <div class="h-80 w-full">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                    <!-- Urgent Needs List -->
                    <div class="glass p-8 rounded-3xl flex flex-col">
                        <h3 class="text-lg font-bold mb-6">Critical Hotspots</h3>
                        <div id="urgent-list" class="space-y-4 flex-1 overflow-y-auto max-h-[320px] pr-2">
                            <!-- Items injected via JS -->
                        </div>
                        <button onclick="switchTab('surveys')" class="mt-6 w-full py-3 bg-gray-800 hover:bg-gray-700 rounded-2xl text-xs font-bold transition-all">View All Surveys</button>
                    </div>
                </div>
            </div>

            <!-- Surveys Tab -->
            <div id="tab-surveys" class="tab-content space-y-6">
                <div class="flex justify-between items-center bg-gray-900/50 p-6 rounded-3xl border border-gray-800">
                    <div class="flex gap-4">
                        <select id="filter-category" onchange="filterSurveys()" class="bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-sm">
                            <option value="all">All Categories</option>
                            <option value="healthcare">Healthcare</option>
                            <option value="food">Food</option>
                            <option value="education">Education</option>
                            <option value="sanitation">Sanitation</option>
                        </select>
                        <select id="filter-district" onchange="filterSurveys()" class="bg-gray-800 border border-gray-700 rounded-xl px-4 py-2 text-sm">
                            <option value="all">All Districts</option>
                        </select>
                    </div>
                    <button onclick="switchTab('register')" class="bg-teal-500 text-white px-6 py-2 rounded-xl text-sm font-bold shadow-lg shadow-teal-500/20">New Submission</button>
                </div>
                <div class="glass rounded-3xl overflow-hidden">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="bg-gray-900/50 text-gray-500 text-[10px] font-bold uppercase tracking-widest border-b border-gray-800">
                                <th class="px-8 py-4">District</th>
                                <th class="px-4 py-4">Category</th>
                                <th class="px-4 py-4">Description</th>
                                <th class="px-4 py-4">Severity</th>
                                <th class="px-4 py-4">Affected</th>
                                <th class="px-8 py-4 text-right">Score</th>
                            </tr>
                        </thead>
                        <tbody id="surveys-table-body" class="text-sm">
                            <!-- Rows injected via JS -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Volunteers Tab -->
            <div id="tab-volunteers" class="tab-content space-y-6">
                <div id="volunteers-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Cards injected via JS -->
                </div>
            </div>

            <!-- Matching Tab -->
            <div id="tab-matching" class="tab-content space-y-8">
                <div class="glass p-12 rounded-[40px] text-center space-y-6">
                    <div class="w-24 h-24 bg-indigo-500/10 text-indigo-500 rounded-[32px] flex items-center justify-center mx-auto text-4xl shadow-xl shadow-indigo-500/10">
                        <i class="fa-solid fa-brain"></i>
                    </div>
                    <div class="max-w-md mx-auto space-y-4">
                        <h3 class="text-2xl font-bold">Gemini AI Engine</h3>
                        <p class="text-gray-500 text-sm leading-relaxed">Match available volunteers to the most critical community needs using Google's advanced large language model.</p>
                    </div>
                    <button id="btn-run-match" onclick="runAIMatch()" class="bg-indigo-500 text-white px-10 py-4 rounded-2xl font-bold shadow-xl shadow-indigo-500/20 transition-all hover:scale-105 active:scale-95">
                        <i class="fa-solid fa-bolt-lightning mr-2"></i> Run AI Matching Logic
                    </button>
                    <div id="matching-loader" class="hidden">
                        <div class="flex flex-col items-center gap-4">
                            <div class="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
                            <p class="text-xs text-indigo-400 font-bold animate-pulse">Analyzing profiles and needs...</p>
                        </div>
                    </div>
                </div>

                <div id="matches-results" class="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
                    <!-- Match results injected via JS -->
                </div>
            </div>

            <!-- Registration Tab -->
            <div id="tab-register" class="tab-content max-w-2xl mx-auto space-y-8">
                <div class="glass p-10 rounded-[32px]">
                    <h3 class="text-xl font-bold mb-8 flex items-center gap-3">
                        <i class="fa-solid fa-pen-to-square text-teal-500"></i> New Field Registration
                    </h3>
                    <form id="survey-form" onsubmit="event.preventDefault(); submitNewSurvey();" class="space-y-6">
                        <div class="grid grid-cols-2 gap-6">
                            <div class="space-y-2">
                                <label class="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">District</label>
                                <select name="district" required class="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none">
                                    <option value="Sangli">Sangli</option>
                                    <option value="Pune">Pune</option>
                                    <option value="Kolhapur">Kolhapur</option>
                                    <option value="Solapur">Solapur</option>
                                    <option value="Nashik">Nashik</option>
                                </select>
                            </div>
                            <div class="space-y-2">
                                <label class="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Category</label>
                                <select name="category" required class="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none">
                                    <option value="healthcare">Healthcare</option>
                                    <option value="food">Food</option>
                                    <option value="education">Education</option>
                                    <option value="sanitation">Sanitation</option>
                                    <option value="employment">Employment</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-6">
                            <div class="space-y-2">
                                <label class="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Severity (1-5)</label>
                                <input type="number" name="severity" min="1" max="5" value="3" required class="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none">
                            </div>
                            <div class="space-y-2">
                                <label class="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Affected Count</label>
                                <input type="number" name="affected_count" min="1" value="10" required class="w-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none">
                            </div>
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Location (Lat, Lng)</label>
                            <div class="grid grid-cols-2 gap-4">
                                <input type="number" name="lat" step="0.0001" value="19.0760" required class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none">
                                <input type="number" name="lng" step="0.0001" value="72.8777" required class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none">
                            </div>
                        </div>
                        <div class="space-y-2">
                            <label class="text-xs font-bold text-gray-500 uppercase tracking-wider ml-1">Description</label>
                            <textarea name="description" required class="w-full h-32 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-sm focus:border-teal-500 outline-none resize-none" placeholder="Provide detailed information about the need..."></textarea>
                        </div>
                        <button type="submit" class="w-full py-4 bg-teal-500 text-white rounded-2xl font-bold shadow-xl shadow-teal-500/20 hover:bg-teal-600 transition-colors">Submit Survey to Intelligence Cloud</button>
                    </form>
                </div>
            </div>

            <!-- Footer -->
            <footer class="mt-16 pt-8 border-t border-gray-900 flex justify-between items-center text-gray-600 text-xs font-bold">
                <p>&copy; 2026 VolunteerMap — Google Solution Challenge</p>
                <div class="flex gap-6">
                    <a href="/docs" class="hover:text-teal-500 transition-colors">API DOCS</a>
                    <a href="/redoc" class="hover:text-teal-500 transition-colors">REDOC</a>
                    <a href="https://github.com/ShreyasN01/VolunteerMap" target="_blank" class="hover:text-teal-500 transition-colors">GITHUB SOURCE</a>
                </div>
            </footer>
        </main>
    </div>

    <script>
        let chartInstance = null;
        let allSurveys = [];

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => {
                n.classList.remove('active');
                n.classList.add('text-gray-400');
            });

            document.getElementById('tab-' + tabId).classList.add('active');
            const navItem = document.getElementById('nav-' + tabId);
            navItem.classList.add('active');
            navItem.classList.remove('text-gray-400');

            const titles = {
                dashboard: ['Dashboard Overview', 'Real-time community intelligence and analytics'],
                surveys: ['Community Surveys', 'Detailed list of all reported community needs'],
                volunteers: ['Available Volunteers', 'Registered support personnel and skill profiles'],
                matching: ['AI Volunteer Matching', 'Gemini-powered intelligent deployment system'],
                register: ['Field Registration', 'Report new community needs from the ground']
            };

            document.getElementById('page-title').innerText = titles[tabId][0];
            document.getElementById('page-subtitle').innerText = titles[tabId][1];

            if (tabId === 'dashboard') fetchData();
            if (tabId === 'surveys') fetchSurveys();
            if (tabId === 'volunteers') fetchVolunteers();
        }

        async function fetchData() {
            try {
                const response = await fetch('/dashboard/stats');
                const data = await response.json();

                document.getElementById('stat-total-surveys').innerText = data.total_surveys || '0';
                document.getElementById('stat-active-volunteers').innerText = data.active_volunteers || data.total_volunteers || '0';
                document.getElementById('stat-urgent-needs').innerText = data.urgent_needs || data.urgent_count || '0';
                document.getElementById('stat-avg-urgency').innerText = (data.avg_urgency || 0).toFixed(1);

                updateChart(data.category_breakdown);
                fetchUrgent();
            } catch (e) { console.error('Error fetching stats:', e); }
        }

        async function fetchUrgent() {
            try {
                const response = await fetch('/surveys/urgent');
                const data = await response.json();
                const list = document.getElementById('urgent-list');
                list.innerHTML = '';

                (data.urgent_needs || []).slice(0, 5).forEach(n => {
                    const div = document.createElement('div');
                    div.className = 'bg-gray-900/30 border border-gray-800 p-4 rounded-2xl flex justify-between items-center';
                    div.innerHTML = `
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-xl bg-${getCategoryColor(n.category)}-500/10 text-${getCategoryColor(n.category)}-500 flex items-center justify-center">
                                <i class="fa-solid ${getCategoryIcon(n.category)}"></i>
                            </div>
                            <div>
                                <p class="text-sm font-bold">${n.district}</p>
                                <p class="text-[10px] text-gray-500 font-bold uppercase">${n.category}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-sm font-black text-rose-500">${n.urgency_score.toFixed(0)}</p>
                            <p class="text-[9px] text-gray-600 font-bold uppercase">Urgency</p>
                        </div>
                    `;
                    list.appendChild(div);
                });
            } catch (e) { console.error(e); }
        }

        async function fetchSurveys() {
            try {
                const response = await fetch('/surveys/all');
                const data = await response.json();
                allSurveys = data.surveys || [];

                const districtSelect = document.getElementById('filter-district');
                const districts = [...new Set(allSurveys.map(s => s.district))];
                districtSelect.innerHTML = '<option value="all">All Districts</option>';
                districts.forEach(d => {
                    districtSelect.innerHTML += `<option value="${d}">${d}</option>`;
                });

                renderSurveysTable(allSurveys);
            } catch (e) { console.error(e); }
        }

        function renderSurveysTable(data) {
            const tbody = document.getElementById('surveys-table-body');
            tbody.innerHTML = '';
            data.forEach(s => {
                const row = document.createElement('tr');
                row.className = 'border-b border-gray-800/50 hover:bg-gray-900/20 transition-colors';
                row.innerHTML = `
                    <td class="px-8 py-4 font-bold text-teal-500">${s.district}</td>
                    <td class="px-4 py-4 uppercase text-[11px] font-bold tracking-wider">${s.category}</td>
                    <td class="px-4 py-4 text-gray-400 max-w-xs truncate">${s.description}</td>
                    <td class="px-4 py-4"><div class="flex text-[8px] gap-0.5">${'★'.repeat(s.severity)}${'☆'.repeat(5-s.severity)}</div></td>
                    <td class="px-4 py-4 font-mono">${s.affected_count}</td>
                    <td class="px-8 py-4 text-right font-black">${(s.urgency_score || 0).toFixed(1)}</td>
                `;
                tbody.appendChild(row);
            });
        }

        function filterSurveys() {
            const cat = document.getElementById('filter-category').value;
            const dist = document.getElementById('filter-district').value;
            let filtered = allSurveys;
            if (cat !== 'all') filtered = filtered.filter(s => s.category === cat);
            if (dist !== 'all') filtered = filtered.filter(s => s.district === dist);
            renderSurveysTable(filtered);
        }

        async function fetchVolunteers() {
            try {
                const response = await fetch('/volunteers/available');
                const data = await response.json();
                const grid = document.getElementById('volunteers-grid');
                grid.innerHTML = '';

                (data.volunteers || []).forEach(v => {
                    const card = document.createElement('div');
                    card.className = 'glass p-6 rounded-[32px] space-y-4 card-hover transition-all border-gray-800';
                    card.innerHTML = `
                        <div class="flex justify-between items-start">
                            <div class="w-12 h-12 bg-gray-800 rounded-2xl flex items-center justify-center text-xl font-black text-teal-500">${v.name[0]}</div>
                            <span class="text-[10px] font-bold px-3 py-1 bg-green-500/10 text-green-500 rounded-lg">Available</span>
                        </div>
                        <div>
                            <h4 class="font-bold text-lg">${v.name}</h4>
                            <p class="text-xs text-gray-500 flex items-center gap-1"><i class="fa-solid fa-location-dot text-[10px]"></i> ${v.district}</p>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            ${v.skills.map(s => `<span class="text-[10px] px-2 py-1 bg-gray-900 border border-gray-800 rounded-md text-gray-400 font-medium">${s}</span>`).join('')}
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } catch (e) { console.error(e); }
        }

        async function runAIMatch() {
            const btn = document.getElementById('btn-run-match');
            const loader = document.getElementById('matching-loader');
            const results = document.getElementById('matches-results');

            btn.classList.add('hidden');
            loader.classList.remove('hidden');
            results.innerHTML = '';

            try {
                const response = await fetch('/volunteers/match', { method: 'POST' });
                const data = await response.json();

                setTimeout(() => {
                    loader.classList.add('hidden');
                    btn.classList.remove('hidden');

                    (data.matches || []).forEach(m => {
                        const div = document.createElement('div');
                        div.className = 'glass p-8 rounded-[32px] border-l-4 border-indigo-500';
                        div.innerHTML = `
                            <div class="flex justify-between items-start mb-4">
                                <div>
                                    <h4 class="text-lg font-bold">${m.volunteer_name}</h4>
                                    <p class="text-xs text-indigo-400 font-bold uppercase tracking-wider">${m.need_category || 'Community Need'}</p>
                                </div>
                                <span class="text-[10px] px-3 py-1 bg-indigo-500/10 text-indigo-500 rounded-lg font-bold uppercase">${m.priority}</span>
                            </div>
                            <p class="text-sm text-gray-300 leading-relaxed italic mb-4">"${m.task_summary}"</p>
                            <div class="bg-indigo-500/5 p-4 rounded-2xl border border-indigo-500/10 mb-4">
                                <p class="text-[10px] font-bold text-indigo-300 uppercase tracking-widest mb-2 flex items-center gap-2">
                                    <i class="fa-solid fa-sparkles"></i> AI Reasoning
                                </p>
                                <p class="text-xs text-gray-400 leading-relaxed">${m.match_reason}</p>
                            </div>
                            <div class="flex items-center justify-between">
                                <div class="flex gap-4">
                                    <span class="text-xs text-gray-500 flex items-center gap-1"><i class="fa-solid fa-car"></i> ${m.distance || m.estimated_travel_km}km</span>
                                    <span class="text-xs text-gray-500 flex items-center gap-1"><i class="fa-solid fa-star"></i> ${(m.match_score * 100).toFixed(0)}% Match</span>
                                </div>
                                <button class="text-xs font-bold text-indigo-400 hover:text-indigo-300">Notify Volunteer <i class="fa-solid fa-chevron-right ml-1"></i></button>
                            </div>
                        `;
                        results.appendChild(div);
                    });
                }, 1500);
            } catch (e) {
                console.error(e);
                loader.classList.add('hidden');
                btn.classList.remove('hidden');
            }
        }

        async function submitNewSurvey() {
            const form = document.getElementById('survey-form');
            const formData = new FormData(form);
            const data = {
                location: { latitude: parseFloat(formData.get('lat')), longitude: parseFloat(formData.get('lng')) },
                district: formData.get('district'),
                state: "Maharashtra",
                category: formData.get('category'),
                description: formData.get('description'),
                severity: parseInt(formData.get('severity')),
                affected_count: parseInt(formData.get('affected_count')),
                source: "digital_form"
            };

            try {
                const response = await fetch('/surveys/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                if (response.ok) {
                    alert('✅ Survey submitted successfully!');
                    form.reset();
                    switchTab('dashboard');
                }
            } catch (e) { console.error(e); }
        }

        function updateChart(data) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            const labels = Object.keys(data || {}).map(l => l.charAt(0).toUpperCase() + l.slice(1));
            const values = Object.values(data || {});

            if (chartInstance) chartInstance.destroy();

            chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#f43f5e', '#f59e0b', '#3b82f6', '#10b981', '#a855f7'],
                        borderRadius: 8,
                        barThickness: 40
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                        x: { grid: { display: false }, ticks: { color: '#64748b', font: { weight: 'bold', size: 10 } } }
                    }
                }
            });
        }

        function getCategoryColor(cat) {
            return { healthcare: 'rose', food: 'amber', education: 'blue', sanitation: 'teal' }[cat] || 'gray';
        }
        function getCategoryIcon(cat) {
            return { healthcare: 'fa-heart-pulse', food: 'fa-bowl-food', education: 'fa-school', sanitation: 'fa-faucet-drip' }[cat] || 'fa-circle-info';
        }

        window.onload = fetchData;
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
