#!/bin/bash
# Setup script for molecular docking environment

echo "=== Molecular Docking Environment Setup ==="

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "✗ Error: conda not found. Please install Anaconda or Miniconda first."
    echo "  Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Create conda environment
echo "Creating conda environment 'molecular-docking'..."
conda env create -f environment.yml

if [ $? -eq 0 ]; then
    echo "✓ Conda environment created successfully"
else
    echo "⚠ Environment creation failed or already exists. Updating instead..."
    conda env update -f environment.yml
fi

echo ""
echo "=== Environment Setup Complete ==="
echo ""
echo "To activate the environment, run:"
echo "  conda activate molecular-docking"
echo ""
echo "To test the setup, run:"
echo "  python run_docking_pipeline.py --help"
echo ""
echo "Example usage:"
echo "  python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt"
echo ""

# Make scripts executable
chmod +x molecular_docking.py
chmod +x docking_visualization.py  
chmod +x run_docking_pipeline.py

echo "✓ Made scripts executable"
echo ""
echo "Ready to run molecular docking pipeline!"