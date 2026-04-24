#!/bin/bash
# VolunteerMap — One-Command Deploy Script
# Deploys backend to Google Cloud Run and frontend to Firebase Hosting
#
# Usage: chmod +x deploy.sh && ./deploy.sh
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - firebase CLI installed
#   - .env file configured with all API keys
#   - Firebase project initialized

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🗺️  VolunteerMap Deploy Script       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Check Prerequisites ─────────────────────────────────────────────

echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! gcloud auth print-identity-token &> /dev/null; then
    echo -e "${RED}Error: gcloud is not authenticated.${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

if ! command -v firebase &> /dev/null; then
    echo -e "${YELLOW}Warning: firebase CLI not found. Installing...${NC}"
    npm install -g firebase-tools
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project set.${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK (Project: $PROJECT_ID)${NC}"

# ─── Step 2: Build Backend Docker Image ──────────────────────────────────────

echo ""
echo -e "${YELLOW}[2/6] Building backend Docker image...${NC}"

IMAGE_NAME="gcr.io/$PROJECT_ID/volunteermap-backend"
TAG="latest"

cd backend
docker build -t "$IMAGE_NAME:$TAG" .
echo -e "${GREEN}✓ Docker image built: $IMAGE_NAME:$TAG${NC}"

# ─── Step 3: Push Image to Container Registry ────────────────────────────────

echo ""
echo -e "${YELLOW}[3/6] Pushing image to Google Container Registry...${NC}"

gcloud auth configure-docker --quiet
docker push "$IMAGE_NAME:$TAG"
echo -e "${GREEN}✓ Image pushed to GCR${NC}"

# ─── Step 4: Deploy Backend to Cloud Run ──────────────────────────────────────

echo ""
echo -e "${YELLOW}[4/6] Deploying backend to Cloud Run...${NC}"

BACKEND_SERVICE="volunteermap-backend"
REGION="asia-south1"  # Mumbai region for India

gcloud run deploy "$BACKEND_SERVICE" \
    --image "$IMAGE_NAME:$TAG" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --set-env-vars "GEMINI_API_KEY=$(grep GEMINI_API_KEY ../.env | cut -d= -f2-)" \
    --set-env-vars "FIREBASE_SERVICE_ACCOUNT_JSON=$(grep FIREBASE_SERVICE_ACCOUNT_JSON ../.env | cut -d= -f2-)" \
    --set-env-vars "CLOUD_VISION_API_KEY=$(grep CLOUD_VISION_API_KEY ../.env | cut -d= -f2-)" \
    --quiet

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format 'value(status.url)')
echo -e "${GREEN}✓ Backend deployed: $BACKEND_URL${NC}"

cd ..

# ─── Step 5: Update Frontend Config ──────────────────────────────────────────

echo ""
echo -e "${YELLOW}[5/6] Updating frontend configuration...${NC}"

# Create/update .env for frontend
cat > frontend/.env << EOF
BACKEND_URL=$BACKEND_URL
GOOGLE_MAPS_API_KEY=$(grep GOOGLE_MAPS_API_KEY .env | cut -d= -f2-)
EOF

echo -e "${GREEN}✓ Frontend .env updated with backend URL${NC}"

# ─── Step 6: Deploy Frontend to Firebase Hosting ─────────────────────────────

echo ""
echo -e "${YELLOW}[6/6] Deploying frontend to Firebase Hosting...${NC}"

firebase deploy --only hosting --project "$PROJECT_ID"

HOSTING_URL="https://$PROJECT_ID.web.app"
echo -e "${GREEN}✓ Frontend deployed to Firebase Hosting${NC}"

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🎉 Deployment Complete!          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Backend API:  $BACKEND_URL${NC}"
echo -e "${GREEN}Frontend App: $HOSTING_URL${NC}"
echo -e "${GREEN}Health Check: $BACKEND_URL/health${NC}"
echo -e "${GREEN}API Docs:     $BACKEND_URL/docs${NC}"
echo ""
echo -e "${YELLOW}Built for Google Solution Challenge 2026 — Build with AI 🚀${NC}"
