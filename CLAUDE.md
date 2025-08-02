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

### Package Management
- **Backend**: Uses `conda` for Python dependency management with local environment in `./conda_env`
- **Frontend**: Uses npm with `package.json` for Node.js dependencies  
- **Key Python Dependencies**: FastAPI, OpenAI, BioPython, RDKit, PyTorch, Transformers, PyMOL
- **Key Frontend Dependencies**: React 18, TypeScript, Vite, 3dmol, Emotion, Framer Motion

### Project Organization
```
proteindance/
├── backend/              # Core backend application
├── autoui/              # Frontend React application
├── p2rank/              # P2Rank protein pocket prediction tool
├── vina                 # Vina molecular docking binary
├── development/         # Development files and tests
│   └── test/           # All test scripts and test data
├── deployment/          # Production deployment files
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.backend.prod
│   └── Dockerfile.frontend.prod
├── archive/             # Archived/unused files
│   ├── guides/          # Old documentation
│   ├── logs/            # Old log files
│   ├── obsolete/        # Obsolete code
│   └── p2rank_test_data/ # P2Rank test datasets
├── proteindance.db      # SQLite database
├── start.sh             # Quick setup script
└── CLAUDE.md           # Project documentation
```

## Common Development Commands

### Environment Setup

**Prerequisites:**
- Python 3.11 (via Conda/Miniconda)
- Conda or Miniconda: https://docs.conda.io/en/latest/miniconda.html
- Node.js and npm (for frontend)

**Install Miniconda:**
```bash
# macOS (ARM64)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# Linux (x86_64)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### Environment Setup
```bash
# Automated setup script (recommended)
bash setup_conda_env.sh

# Manual conda environment creation
conda create -p ./conda_env python=3.11 -y
conda activate ./conda_env

# Install dependencies manually (if needed)
conda install -c conda-forge numpy scipy matplotlib pandas rdkit pymol-open-source -y
pip install fastapi uvicorn openai biopython py3dmol transformers torch

# Quick startup script for complete environment
bash start.sh

# Quick startup with custom options  
bash start.sh -p 8000              # Use custom backend port
bash start.sh -i 192.168.1.100     # Use custom IP address
bash start.sh --help               # Show all options
```

### Backend Development
```bash
# Activate conda environment and run backend server
export PATH="./conda_env/bin:$PATH"
export KMP_DUPLICATE_LIB_OK=TRUE
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
docker-compose -f deployment/docker-compose.prod.yml up --build
```

### Code Quality and Testing

#### Frontend Type Checking
```bash
# Navigate to frontend directory
cd autoui

# Run TypeScript type checking
npm run type-check
```

#### Backend Testing
```bash
# Set conda environment first
export PATH="./conda_env/bin:$PATH"
export KMP_DUPLICATE_LIB_OK=TRUE

# Run authentication system tests
python development/test/test_auth.py
# or
bash development/test/test_auth.sh

# Test model switching functionality
python development/test/test_model_switching.py
# or  
bash development/test/test_model_switching.sh

# Test PDB priority logic
python development/test/test_pdb_priority.py

# Test structure acquisition priority
python development/test/test_structure_priority.py

# Test compound optimization
python development/test/test_optimization.py

# Complete environment setup and startup
bash start.sh
```

#### Code Quality Status
- **Frontend**: TypeScript strict mode enabled, type checking via `npm run type-check`
- **Backend**: Manual testing scripts only (no automated linting/formatting)
- **Testing**: Manual test scripts for core functionality (located in `development/test/`)
- **Environment**: Conda-based dependency management with Python 3.11
- **CI/CD**: No automated pipeline configured

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
- API Base URL: `https://api.siliconflow.cn/v1`
- **Security Note**: API key is currently hardcoded for development (should be moved to environment variables for production)
- Local AI models stored in `backend/services/aimodels/` with configurations for different model versions

### Database
- SQLite database `proteindance.db` in project root
- Session management through `backend/database/session_manager.py`
- Automatic session persistence for workflow state

### Environment Variables
For production deployment, configure these environment variables:
- `OPENAI_API_KEY` - AI service API key (currently hardcoded in config.py)
- `ENV` - Environment setting (development/production)
- `LOG_LEVEL` - Logging verbosity (default: INFO)
- Database settings
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

### Authentication System
- JWT-based authentication with session management
- User registration and login functionality in `backend/services/auth_service.py`
- Test authentication flow with `development/test/test_auth.py` and `development/test/test_auth.sh`
- Frontend auth modal and service in `autoui/src/services/authService.ts`
- Authentication required for workflow persistence and session management

### Session Management
- Sessions auto-save after major workflow steps
- Session history component allows loading previous workflows
- All workflow state is serializable and restorable

### Model Management
- Multiple AI model configurations supported in `backend/services/aimodels/`
- Model switching capability for different analysis tasks
- Test model switching with `test/test_model_switching.py`

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
- Backend logs stored in `backend.log` and individual service logs
- Frontend dev tools available via browser console
- API documentation accessible at `http://localhost:5001/docs`

### Key Development Tools
- **start.sh**: Automated environment setup, IP detection, and service startup with port cleanup
- **uv**: Python package manager for fast dependency installation and environment management
- **Dynamic API Configuration**: Frontend automatically detects and configures backend endpoints
- **Session Persistence**: Workflow state automatically saved and resumable across sessions
- **Real-time 3D Visualization**: Integrated protein structure viewer with live updates during workflow

### Common Issues and Solutions
- **"Failed to fetch" errors**: 
  - **自动解决**: 点击前端右上角⚙️按钮打开API配置面板，点击"自动检测"
  - **手动配置**: 在配置面板中输入正确的后端地址和端口
  - **环境变量**: 复制 `autoui/.env.local.example` 为 `.env.local` 并修改配置
  - **脚本配置**: 运行 `bash start.sh` 自动配置正确的API地址
  - **验证后端**: `curl http://localhost:5001/docs` 检查后端服务状态
- **Port conflicts**: Use `start.sh` script which automatically cleans up port usage
- **Python dependency issues**: 
  - **重新安装环境**: 运行 `bash setup_conda_env.sh` 完全重建conda环境
  - **手动修复**: 删除 `./conda_env` 目录后重新创建环境
  - **OpenMP错误**: 设置 `export KMP_DUPLICATE_LIB_OK=TRUE` 环境变量
- **Frontend API connection**: 前端现已支持动态配置，无需手动修改代码
- **P2Rank not found**: Ensure binary is in `p2rank/` directory or system PATH
- **AI service failures**: Check API key configuration in `backend/core/config.py`
- **PyMOL加载失败**: 确保conda环境正确安装了PyMOL (`conda list | grep pymol`)
- **RDKit导入错误**: 验证RDKit安装 (`python -c "from rdkit import Chem; print('RDKit OK')"`)
- **Environment activation fails**: 使用完整路径 `export PATH="./conda_env/bin:$PATH"`

### Dynamic Configuration System

ProteinDance now includes a robust dynamic configuration system to eliminate hardcoded API addresses:

#### Environment Variables
- **Development**: Configure via `autoui/.env.development`
- **Production**: Configure via `autoui/.env.production` 
- **Local Override**: Copy `autoui/.env.local.example` to `.env.local` for custom settings
- **Available Variables**:
  - `VITE_API_BASE_URL` - Complete API URL (e.g., `http://localhost:5001/api`)
  - `VITE_BACKEND_HOST` - Backend hostname (e.g., `localhost`)
  - `VITE_BACKEND_PORT` - Backend port number (e.g., `5001`)

#### Frontend Configuration Panel
- Access via ⚙️ button in top-right corner
- **Auto-detect**: Automatically finds available backend service
- **Manual config**: Set custom host and port
- **Real-time status**: Shows connection health with auto-recovery
- **Config persistence**: Settings saved for future sessions

#### API Management Features
- **Auto-detection**: Scans common ports (5001, 8000, 3001, 8080) and hosts
- **Health monitoring**: Continuous connection status checking  
- **Fallback recovery**: Automatically switches to available backend
- **Console access**: Use `api.getConfig()`, `api.updateConfig()`, `api.autoDetect()` in browser console

## Important Development Constraints

- ~~Frontend expects backend on port 5001 with `/api` prefix~~ (Now dynamically configurable)
- Python environment requires specific package versions (see requirements.txt modifications)
- P2Rank binary must be accessible in `p2rank/` directory or PATH
- 3D molecular visualization requires proper CORS configuration for structure file access
- Scientific analysis requires valid OpenAI API configuration for optimal results