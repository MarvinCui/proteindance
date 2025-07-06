# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProteinDance is a drug discovery platform that combines AI-powered analysis with protein structure prediction and molecular docking. The application consists of a Python FastAPI backend and a React TypeScript frontend.

## Architecture

### Backend (Python FastAPI)
- **Main entry**: `backend/app.py` - FastAPI application with CORS middleware
- **Services layer**: `backend/services/` contains specialized engines:
  - `drug_discovery_api.py` - Main API orchestration class (singleton pattern)
  - `ai_engine.py` - AI-powered analysis and decision making
  - `pharma_engine.py` - Pharmaceutical data processing
  - `visualization_engine.py` - Molecular visualization
  - `workflow_engine.py` - Workflow coordination
- **Models**: `backend/models/` for data structures and exceptions
- **Core**: `backend/core/` for configuration and constants
- **Utils**: `backend/utils/` for validation and helper functions

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript, Vite build system
- **UI Libraries**: Emotion for styling, Framer Motion for animations
- **3D Visualization**: 3dmol library for molecular structure rendering
- **API Communication**: Centralized in `autoui/src/services/api.ts`

### External Tools
- **P2Rank**: Protein pocket prediction tool (pre-installed in `p2rank/` directory)
- **Vina**: Molecular docking (available in project root)

## Common Development Commands

### Backend Development
```bash
# Environment setup (Python 3.9.6 recommended)
conda create -p ./py396_env python=3.9.6 -y
conda activate ./py396_env

# Install dependencies (modify requirements.txt to remove version pins for ipython and scipy)
pip install -r requirements.txt

# Run backend server
uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
```

### Frontend Development
```bash
# Navigate to frontend directory
cd autoui

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check
```

### Production Deployment
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up --build
```

## Key Configuration Files

- **API Configuration**: `autoui/src/services/api.ts` - Set `API_BASE` to backend URL (e.g., `http://localhost:5001/api`)
- **Backend Config**: `backend/core/config.py` - Application settings
- **Environment**: `.env` file for environment variables
- **Docker**: `docker-compose.prod.yml` for production deployment

## Project Structure Notes

- The backend uses a service-oriented architecture with singleton pattern for the main API class
- All API endpoints are prefixed with `/api/`
- The frontend expects backend to run on port 5001
- The project includes extensive protein analysis tools and molecular visualization capabilities
- P2Rank configuration files are located in `p2rank/config/` with various model options

## Important Development Notes

- Always ensure the frontend `API_BASE` constant matches the backend URL
- The project requires specific Python package versions - modify requirements.txt as needed
- The application handles protein structure analysis, pocket prediction, and molecular docking workflows
- Use the provided conda environment setup for consistent Python environment