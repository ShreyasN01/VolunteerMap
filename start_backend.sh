#!/bin/bash
# VolunteerMap — Backend Server Runner
# Use this to start the FastAPI backend with environment variables loaded.

echo "🚀 Starting VolunteerMap Backend..."

# Check if venv exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Using virtual environment."
fi

# Export variables from .env if needed (though python-dotenv handles it)
# export $(grep -v '^#' .env | xargs)

cd backend
python3 main.py
