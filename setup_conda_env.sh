#!/bin/bash
# ProteinDance Conda Environment Setup Script
# This script creates a complete conda environment for the ProteinDance project

set -e  # Exit on any error

echo "🔬 Setting up ProteinDance Conda Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Conda not found. Please install Miniconda or Anaconda first.${NC}"
    echo "   Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Remove existing environment if it exists
if [ -d "./conda_env" ]; then
    echo -e "${YELLOW}⚠️  Removing existing conda environment...${NC}"
    rm -rf ./conda_env
fi

echo -e "${GREEN}📦 Creating conda environment with Python 3.11...${NC}"
conda create -p ./conda_env python=3.11 -y

echo -e "${GREEN}🔧 Installing core scientific packages via conda...${NC}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ./conda_env

# Install core packages via conda
conda install -c conda-forge numpy scipy matplotlib pandas pillow scikit-learn requests beautifulsoup4 click jinja2 packaging python-dateutil pytz tqdm -y

echo -e "${GREEN}🧬 Installing RDKit and PyMOL...${NC}"
conda install -c conda-forge rdkit pymol-open-source -y

echo -e "${GREEN}🌐 Installing FastAPI and web dependencies...${NC}"
pip install --no-cache-dir fastapi uvicorn pydantic email-validator PyJWT passlib bcrypt

echo -e "${GREEN}🤖 Installing AI and molecular packages...${NC}"
pip install --no-cache-dir openai biopython py3dmol

echo -e "${GREEN}🔬 Installing biology/chemistry API clients...${NC}"
pip install --no-cache-dir chembl-webresource-client gprofiler-official mygene biothings-client python-dotenv

echo -e "${GREEN}🧠 Installing PyTorch (CPU version)...${NC}"
pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo -e "${GREEN}🤗 Installing Transformers library...${NC}"
pip install --no-cache-dir transformers safetensors

echo -e "${GREEN}✅ Environment setup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Dependency Installation Summary:${NC}"
echo "   • Python 3.11.13"
echo "   • Scientific packages: NumPy, SciPy, Matplotlib, Pandas"
echo "   • Chemistry: RDKit, PyMOL, ChEMBL client"
echo "   • Biology: BioPython, UniProt clients"
echo "   • Web framework: FastAPI, Uvicorn, Pydantic"
echo "   • AI/ML: PyTorch, Transformers, OpenAI client"
echo "   • Visualization: py3Dmol, Pillow"
echo "   • Authentication: PyJWT, Passlib, BCrypt"
echo ""
echo -e "${GREEN}🚀 To start the backend server:${NC}"
echo "   export PATH=\"\$(pwd)/conda_env/bin:\$PATH\""
echo "   export KMP_DUPLICATE_LIB_OK=TRUE"
echo "   uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload"
echo ""
echo -e "${YELLOW}💡 Note: The environment is created in './conda_env' directory${NC}"