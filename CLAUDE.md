# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProteinDance is a drug discovery platform that combines AI-powered analysis with protein structure prediction and molecular docking. The application consists of a Python FastAPI backend and a React TypeScript frontend.

## Architecture

### Backend (Python FastAPI)
- **Main entry**: `backend/app.py` - FastAPI application with CORS middleware
- **Services layer**: `backend/services/` contains specialized engines:
  - `drug_discovery_api.py` - Main API orchestration class (singleton pattern)
  - `ai_engine.py` - AI-powered analysis and decision making using DeepSeek
  - `pharma_engine.py` - Pharmaceutical data processing (UniProt, ChEMBL, RCSB PDB, AlphaFold)
  - `visualization_engine.py` - Molecular visualization and image generation
  - `workflow_engine.py` - Complete workflow coordination (6-step drug discovery process)
- **Models**: `backend/models/` for data structures and exceptions
- **Core**: `backend/core/` for configuration and constants
- **Utils**: `backend/utils/` for validation and helper functions
- **Database**: SQLite with session management for workflow persistence

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript, Vite build system
- **UI Libraries**: Emotion for styling, Framer Motion for animations
- **3D Visualization**: 3dmol library for molecular structure rendering
- **State Management**: React hooks with comprehensive session persistence
- **API Communication**: Centralized in `autoui/src/services/api.ts`
- **Workflow UI**: 8-step visual workflow with real-time updates

### External Tools
- **P2Rank**: Protein pocket prediction tool (pre-installed in `p2rank/` directory)
- **Vina**: Molecular docking (available in project root)

## Common Development Commands

### Environment Setup
```bash
# Create conda environment (Python 3.9.6 recommended)
conda create -p ./py396_env python=3.9.6 -y
conda activate ./py396_env

# Modify requirements.txt first: remove version pins for ipython and scipy
# Then install dependencies
pip install -r requirements.txt
```

### Backend Development
```bash
# Run backend server with auto-reload
uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload

# Test individual components
python -c "from backend.services.ai_engine import AIEngine; ai = AIEngine(); print('AI Engine loaded')"

# Check API endpoints
curl http://localhost:5001/api/disease-targets -X POST -H "Content-Type: application/json" -d '{"disease": "cancer"}'
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

# Preview production build locally
npm run preview
```

### Production Deployment
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up --build
```

### Testing Commands

#### Backend Testing
```bash
# Run authentication system tests
python test_auth.py
# or
bash test_auth.sh

# Test PDB priority logic
python test_pdb_priority.py

# Test structure acquisition priority
python test_structure_priority.py

# Complete environment setup and startup
bash start.sh
```

## Critical Configuration

### API Base URL Configuration
The frontend **must** be configured to point to the correct backend URL in `autoui/src/services/api.ts`:
```typescript
const API_BASE = 'http://localhost:5001/api';  // Development
// Production URLs may differ - adjust as needed
```

### AI Configuration
Backend AI services are configured in `backend/core/config.py`:
- OpenAI API endpoint: SiliconFlow (DeepSeek-V3 model)
- **Security Note**: API key is currently hardcoded for development (should be moved to environment variables for production)

### Database
- SQLite database `proteindance.db` in project root
- Session management through `backend/database/session_manager.py`
- Automatic session persistence for workflow state

### Environment Variables
For production deployment, configure these environment variables:
- API keys (currently hardcoded in config.py)
- Database settings
- Log levels
- External API endpoints

## Workflow Architecture

The application implements an 8-step drug discovery workflow:

1. **Target Discovery** - AI identifies disease-related protein targets
2. **AI Decision** - Selects optimal target using AI reasoning
3. **UniProt Retrieval** - Fetches protein metadata and sequences
4. **Structure Acquisition** - Downloads PDB or AlphaFold structures
5. **Pocket Prediction** - Identifies drug binding sites using P2Rank
6. **Ligand Acquisition** - Retrieves active compounds from ChEMBL
7. **Compound Optimization** - AI-powered molecular optimization
8. **Results & Analysis** - Scientific analysis and visualization

### State Management
- Each workflow step maintains persistent state
- Real-time updates to 3D protein viewer in sidebar
- Session history allows resuming interrupted workflows
- Complete workflow data serialization for session persistence

## Key Integration Points

### AI Engine Integration
- All AI decisions use DeepSeek-V3 through SiliconFlow API
- Scientific analysis generation in `ai_explain_results()` method
- Decision-making for target selection, pocket selection, and compound optimization
- Comprehensive workflow analysis with professional terminology

### Data Flow
1. Frontend initiates workflow through step-by-step API calls (not batch processing)
2. Each step updates both workflow state and real-time visualization
3. Scientific analysis is generated after compound optimization
4. Results are integrated into unified display panel

### External API Dependencies
- UniProt REST API for protein data
- RCSB PDB for experimental structures
- AlphaFold database for predicted structures
- ChEMBL API for bioactive compounds
- Optional: DogSite API for backup pocket prediction

## Development Notes

### Session Management
- Sessions auto-save after major workflow steps
- Session history component allows loading previous workflows
- All workflow state is serializable and restorable

### Error Handling
- Comprehensive fallback mechanisms for external API failures
- Graceful degradation when AI services are unavailable
- Alternative target selection when primary targets fail

### Scientific Analysis Integration
- Scientific analysis module combines target analysis and comprehensive workflow explanation
- Real-time generation after compound optimization step
- Integration with existing result display components

### Debugging
- Extensive logging throughout workflow execution
- Console debugging outputs in development mode
- Step-by-step progress tracking with detailed error messages

## Important Development Constraints

- Frontend expects backend on port 5001 with `/api` prefix
- Python environment requires specific package versions (see requirements.txt modifications)
- P2Rank binary must be accessible in `p2rank/` directory or PATH
- 3D molecular visualization requires proper CORS configuration for structure file access
- Scientific analysis requires valid OpenAI API configuration for optimal results