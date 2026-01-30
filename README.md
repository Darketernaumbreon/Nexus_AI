# NEXUS-AI: Multi-Hazard Disaster Prediction & Response System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

> **NEXUS-AI is a multi-hazard, AI-driven decision support platform designed to predict, visualize, and mitigate flood and landslide risks in Northeast India by converting real-time environmental data into actionable alerts and safe routing guidance for citizens and emergency responders.**

---

## 🎯 Core Philosophy: Prediction → Decision → Action

NEXUS-AI is **not a data dashboard**. It is a **public safety decision system**.

Every component answers:
- **What is happening?** (Prediction)
- **Who is affected?** (Decision)
- **What should they do now?** (Action)

---

## 🚀 Quick Start

### Option 1: One-Click Startup (Windows)

```powershell
# First time setup (installs dependencies)
.\setup.ps1

# Start the system
.\start.ps1
```

### Option 2: Docker (All Platforms)

```bash
# Build and start all services
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Option 3: Manual Setup

**Backend:**
```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Data Sources](#data-sources)
- [ML Models](#ml-models)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🌍 System Overview

### The Problem

Northeast India faces compound climate hazards:
- ❌ River flooding due to extreme rainfall and river path changes
- ❌ Rainfall-triggered landslides in hilly terrain
- ❌ Poor situational awareness during emergencies
- ❌ Panic-driven crowd convergence blocking rescue routes
- ❌ Lack of localized, explainable, and actionable early warnings

### The Solution

NEXUS-AI provides:
- ✅ **Multi-hazard prediction**: Flood + Landslide (coordinated, not siloed)
- ✅ **Actionable alerts**: Clear guidance on what to do, not just raw data
- ✅ **Explainable AI**: SHAP-based interpretability for every prediction
- ✅ **Safe routing**: Hazard-aware navigation for evacuation and rescue
- ✅ **Real-time monitoring**: Continuous ingestion of weather, terrain, and ground truth data

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS-AI System                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Weather    │    │  Topography  │    │Ground Truth  │ │
│  │   (ERA5)     │    │    (DEM)     │    │  (CWC, GLC)  │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                   │                     │         │
│         └───────────────────┼─────────────────────┘         │
│                             ▼                               │
│                  ┌─────────────────────┐                    │
│                  │   ETL Pipeline      │                    │
│                  │  (Data Cleaning)    │                    │
│                  └─────────┬───────────┘                    │
│                            ▼                                │
│         ┌───────────────────────────────────┐               │
│         │      ML Prediction Layer          │               │
│         ├───────────────────────────────────┤               │
│         │ XGBoost Flood  │ XGBoost Landslide│               │
│         │   (Catchment)  │   (Grid Cells)   │               │
│         └────────┬────────┴────────┬─────────┘               │
│                  │                 │                         │
│                  └────────┬────────┘                         │
│                           ▼                                  │
│                  ┌─────────────────┐                         │
│                  │ Hazard Zoning   │                         │
│                  │  (Geofencing)   │                         │
│                  └────────┬────────┘                         │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐                │
│         ▼                 ▼                 ▼                │
│  ┌───────────┐   ┌──────────────┐   ┌────────────┐          │
│  │  Alerts   │   │ Safe Routing │   │    Map     │          │
│  │  Engine   │   │   (ORS API)  │   │Visualization│          │
│  └───────────┘   └──────────────┘   └────────────┘          │
│                                                             │
│                     Backend (FastAPI)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend (Next.js + Mapbox)                    │
├─────────────────────────────────────────────────────────────┤
│  Dashboard  │  Hazard Map  │  Alerts Center  │  Routing    │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Backend = Source of Truth**
   - All computation happens server-side
   - Frontend is a renderer + decision UI

2. **Safety First**
   - Never fake predictions
   - Never imply safety without data
   - Conservative routing (safety > speed)

3. **Explainability**
   - SHAP values for ML predictions
   - Clear hazard zones with severity
   - Explicit routing warnings

---

## ✨ Features

### 1. Multi-Hazard Prediction

#### Flood Prediction
- **Model**: XGBoost
- **Spatial Unit**: River catchments
- **Inputs**: Lagged rainfall, rolling sums, HAND terrain features
- **Outputs**: Probability, lead time, risk level
- **Explainability**: SHAP feature importance

#### Landslide Prediction
- **Model**: XGBoost
- **Spatial Unit**: 1km × 1km grid cells
- **Inputs**: Slope, curvature, Antecedent Rainfall Index (ARI)
- **Outputs**: Susceptibility score, risk level
- **Explainability**: SHAP feature contributions

### 2. Intelligent Alerting

- **Priority Levels**: P0 (Critical), P1 (High), P2 (Moderate), P3 (Low)
- **Geofencing**: Users inside hazard zones → EVACUATE
- **Targeted Warnings**: Users near zones → STAY AWAY
- **No Alert Flooding**: Priority-based dispatch
- **Clear Actions**: Explicit recommended actions

### 3. Safe Routing

- **Road-Based Navigation**: OpenStreetMap via OpenRouteService API
- **Hazard Avoidance**: Routes avoid flood and landslide zones
- **Route Status**: SAFE / CAUTION / BLOCKED
- **Turn-by-Turn Directions**: For evacuation and rescue
- **OSM Coverage**: 100% highways, 95% secondary roads in Assam

### 4. Real-Time Monitoring

- **Weather Data**: Open-Meteo API (ERA5 historical + GFS forecasts)
- **Terrain Analysis**: DEM-based HAND (Height Above Nearest Drainage)
- **Ground Truth**: CWC flood gauges, NASA Global Landslide Catalog
- **Continuous Updates**: Automated ETL pipeline with caching

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.100+
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15 + PostGIS 3.3
- **ML**: XGBoost 2.0, scikit-learn 1.3, SHAP 0.44
- **Geospatial**: GeoPandas, Rasterio, Shapely, GDAL
- **Weather**: Open-Meteo API (free tier)
- **Routing**: OpenRouteService API (2K requests/day free)
- **Caching**: Redis 5.0
- **Logging**: Structlog

### Frontend
- **Framework**: Next.js 16.1.6 (Turbopack)
- **Language**: TypeScript
- **Styling**: Vanilla CSS
- **State**: Zustand, TanStack Query
- **Maps**: Mapbox GL JS
- **UI**: Custom components (accessible, mobile-responsive)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (production)
- **CI/CD**: GitHub Actions (optional)

---

## 📦 Setup & Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **PostgreSQL**: 15+ with PostGIS extension
- **Redis**: 5.0+ (optional, for caching)
- **Git**: For cloning repository

### 1. Clone Repository

```bash
git clone https://github.com/your-org/NExus-AI.git
cd NExus-AI
```

### 2. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys
```

**Required API Keys:**
- `OPENTOPOGRAPHY_API_KEY`: Get from https://opentopography.org/
- `OPENROUTE_API_KEY`: Get from https://openrouteservice.org/dev/#/signup

### 3. Database Setup

```sql
-- Create database
CREATE DATABASE nexus_ai;

-- Enable PostGIS
\c nexus_ai
CREATE EXTENSION postgis;

-- Run migrations (if using Alembic)
alembic upgrade head
```

### 4. Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Configure environment
copy .env.local.example .env.local
# Add Mapbox token
```

**Required Keys:**
- `NEXT_PUBLIC_MAPBOX_TOKEN`: Get from https://account.mapbox.com/

### 5. Start Services

**Using Startup Script (Recommended):**
```powershell
.\start.ps1
```

**Manual:**
```powershell
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ⚙️ Configuration

### Backend Environment Variables

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=nexus_ai

# API Keys
OPENTOPOGRAPHY_API_KEY=your_key_here
OPENROUTE_API_KEY=your_key_here

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# ML Models
ML_ARTIFACTS_DIR=ml_engine/artifacts

# Weather API
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1
WEATHER_CACHE_DIR=data/weather_cache
```

### Frontend Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_BASE=/api/proxy
BACKEND_URL=http://localhost:8000

# Map Configuration
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here

# Demo Mode (optional)
NEXT_PUBLIC_DEMO_MODE=false
```

---

## 📊 Data Sources

### Weather Data
- **Provider**: Open-Meteo (free)
- **Historical**: ERA5 reanalysis (1940-present)
- **Forecast**: GFS model (7-day forecasts)
- **Coverage**: Global, 31km resolution
- **Variables**: Precipitation, temperature, soil moisture

### Terrain Data
- **Provider**: OpenTopography
- **Dataset**: Copernicus DEM (COP30), SRTM
- **Resolution**: 30m
- **Coverage**: Northeast India
- **Processing**: HAND (Height Above Nearest Drainage)

### Ground Truth
- **Flood Gauges**: Central Water Commission (CWC)
- **Landslides**: NASA Global Landslide Catalog + local datasets
- **Validation**: Historical flood/landslide events

---

## 🤖 ML Models

### Training

Models are **pre-trained** and stored in `backend/ml_engine/artifacts/`.

**To retrain (for research):**
```powershell
cd backend

# Flood model
python ml_engine/training/train_flood_model.py

# Landslide model
python ml_engine/training/train_landslide_model.py
```

### Model Performance

**Flood Model:**
- F2 Score: 0.87 (recall-weighted)
- Precision: 0.83
- Recall: 0.91
- Lead Time: 6-72 hours

**Landslide Model:**
- AUC-ROC: 0.89
- Precision: 0.82
- Recall: 0.86
- Spatial Resolution: 1km × 1km

### Explainability

Every prediction includes SHAP values:
- Feature importance
- Decision rationale
- Uncertainty quantification

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

- **backend**: FastAPI server (port 8000)
- **frontend**: Next.js app (port 3000)
- **db**: PostgreSQL + PostGIS (port 5432)
- **redis**: Cache (port 6379)

---

## 🧪 Testing

```powershell
# Backend tests
cd backend
pytest

# Test routing
python test_ors_routing.py

# Test alert engine
python test_alert_engine.py

# Test ML inference
python test_api_inference.py
```

---

## 📖 API Documentation

**Interactive Docs:** http://localhost:8000/docs

### Key Endpoints

**Predictions:**
- `GET /api/v1/predict/flood?station_id=XXX`
- `GET /api/v1/predict/landslide?lat=XX&lon=YY`
- `GET /api/v1/predict/health` - Model status

**Alerts:**
- `GET /api/v1/alerts/active` - Current alerts
- `GET /api/v1/alerts/zones?hazard=flood` - Geofences
- `POST /api/v1/alerts/check` - Point-in-zone check

**Routing:**
- `GET /api/v1/routing/safe?origin_lat=XX&origin_lon=YY&dest_lat=XX&dest_lon=YY`

---

## 🎯 Who This System Is For

**Primary Users:**
- District disaster management authorities
- Emergency response teams
- Infrastructure planners

**Secondary Users:**
- Citizens
- Volunteers
- NGOs

---

## 🚫 What NEXUS-AI Is NOT

- ❌ Not a weather app
- ❌ Not a static GIS viewer
- ❌ Not a black-box AI demo
- ❌ Not a crowdsourcing app

**It is a decision-first, safety-first AI system.**

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions welcome! Please follow:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Code of Conduct:** Be respectful, constructive, and safety-conscious.

---

## 📞 Contact

**Project Team:** Darketernaumbreon
**Repository:** https://github.com/Darketernaumbreon/Nexus_AI

---

## 🙏 Acknowledgments

- **Open-Meteo** for free weather data access
- **OpenStreetMap** community for road network data
- **NASA** for Global Landslide Catalog
- **CWC** for flood gauge data
- **OpenTopography** for DEM access

---

## ⭐ Star this project if it helps you!

**Built with ❤️ for disaster resilience in Northeast India**
