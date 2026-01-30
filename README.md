# NEXUS AI
**Road Network Intelligence & Risk Assessment System**

## Overview
Nexus AI is an advanced platform designed to monitor road network conditions, analyze weather risks, and predict infrastructure vulnerability in real-time. Specifically tailored for the challenging terrain of **North East India**, it leverages geospatial data and AI to provide actionable insights for disaster management.

## 🚀 Key Features
- **Real-time Dashboard**: Live monitoring of route health, weather conditions, and risk levels.
- **Geospatial Intelligence**: Interactive map visualizing road networks (NH-6, NH-27) with risk heatmaps.
- **Risk Simulation**: AI-driven predictive modeling for landslide and flood risks based on rainfall.
- **Weather Integration**: Live weather layers and alert system.

## 🛠️ Prerequisites
- **OS**: Windows 10/11 (Optimized), macOS, or Linux.
- **Tools**:
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Required for Database/Redis)
  - [Node.js](https://nodejs.org/) (v18 or higher)
  - [Python](https://www.python.org/) (v3.9 or higher)

## 🏁 Quick Start (Recommended)

We have provided a **Hybrid Launch Script** to bypass common Docker build issues on Windows.

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd Nexus_AI
    ```

2.  **Start the Application**
    Double-click the **`run_local.bat`** file in the root directory.
    
    *Alternatively, run from terminal:*
    ```powershell
    .\run_local.bat
    ```

    **This script will:**
    - Spin up PostgreSQL (PostGIS) and Redis in Docker containers.
    - Start the Backend (FastAPI) server locally on port `8000`.
    - Start the Frontend (Next.js) server locally on port `3000`.
    - Automatically open the dashboard in your browser.

3.  **Login**
    - **URL**: [http://localhost:3000](http://localhost:3000)
    - **Email**: `admin@nexus.ai`
    - **Password**: `NexusSecureStart2026!`

## 🧩 Architecture

- **Frontend**: Next.js 14, TailwindCSS, Recharts, React-Google-Maps.
- **Backend**: FastAPI, SQLAlchemy, Pydantic, GeoAlchemy2.
- **Database**: PostgreSQL with PostGIS extension.
- **Cache**: Redis.

## 📂 Project Structure
- **/Frontend**: Next.js application source code.
- **/BACKEND**: Python FastAPI application and data models.
- **run_local.bat**: Universal startup script for Windows.

---
*Built for DRISHTI-NE Hackathon 2026*
