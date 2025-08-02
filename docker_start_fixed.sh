#!/bin/bash
set -e

echo "🧬 Starting ProteinDance with Conda Environment..."

# 权限修复（如果以root运行）
if [ "$(id -u)" = "0" ]; then
    echo "🔧 Fixing permissions for application directories..."
    mkdir -p /app/temp /app/backend/logs /app/docking_results /tmp/drug_flow
    chown -R 1000:1000 /app/temp /app/backend/logs /app/docking_results /tmp/drug_flow
    chmod 755 /app/temp /app/backend/logs /app/docking_results /tmp/drug_flow
fi

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate proteindance

# Set environment variables
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH="/app:$PYTHONPATH"

# Test all key dependencies
echo "🔍 Testing dependencies..."
python -c "
import sys
print(f'Python version: {sys.version}')

# Test core packages
try:
    import numpy as np
    print(f'✅ NumPy {np.__version__}')
except ImportError as e:
    print(f'❌ NumPy: {e}')

try:
    import rdkit
    from rdkit import Chem
    print(f'✅ RDKit {rdkit.__version__}')
except ImportError as e:
    print(f'❌ RDKit: {e}')

try:
    import pymol
    print('✅ PyMOL imported successfully')
    # Skip PyMOL initialization in Docker to avoid display issues
    print('⚠️  Skipping PyMOL GUI test in Docker environment')
except ImportError as e:
    print(f'❌ PyMOL import failed: {e}')

try:
    import fastapi
    print(f'✅ FastAPI {fastapi.__version__}')
except ImportError as e:
    print(f'❌ FastAPI: {e}')

try:
    import Bio
    print(f'✅ BioPython {Bio.__version__}')
except ImportError as e:
    print(f'❌ BioPython: {e}')
"

# Start backend server
echo "🚀 Starting backend server..."
uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload &
BACKEND_PID=$!

# Serve frontend static files
echo "🌐 Starting frontend server..."
cd /app/autoui/dist
python -m http.server 5173 --bind 0.0.0.0 &
FRONTEND_PID=$!

# Wait for services to start
sleep 5

echo "✅ ProteinDance started successfully!"
echo "📍 Backend API: http://localhost:5001"
echo "📍 Frontend App: http://localhost:5173"
echo "📖 API Docs: http://localhost:5001/docs"
echo "🔬 Conda Environment: proteindance"

# Cleanup function
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup EXIT INT TERM

# Keep container running
wait