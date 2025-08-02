# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The docking_test directory contains a standalone molecular docking pipeline that integrates AutoDock Vina with PyMOL and web-based visualization. This is a testing environment for molecular docking functionality that can be integrated with the main ProteinDance platform.

## Architecture

### Core Components
- **molecular_docking.py** - Core docking engine with protein preprocessing and AutoDock Vina integration
- **docking_visualization.py** - PyMOL-based visualization and 3DMol.js web viewer generation
- **run_docking_pipeline.py** - Main pipeline orchestrator combining docking and visualization
- **docking_web_api.py** - Flask API server providing web interface for the pipeline

### Pipeline Structure
```
Input: protein_structure.pdbqt + original_ligand.pdbqt
  ↓
Protein Preprocessing (removes ROOT/ENDROOT tags)
  ↓
AutoDock Vina Docking
  ↓
Dual Visualization (PyMOL + 3DMol.js)
  ↓
Output: docking_results/ with images and web viewer
```

### External Dependencies
- **AutoDock Vina** - Molecular docking executable (./vina binary)
- **PyMOL** - 3D visualization and high-quality image generation
- **3DMol.js** - Web-based interactive molecular viewer
- **molecular-docking conda environment** - Isolated environment with all dependencies

## Common Development Commands

### Environment Setup
```bash
# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate environment
conda activate molecular-docking

# Install additional pip dependencies
pip install -r requirements.txt
```

### Quick Start
```bash
# Start web interface (recommended)
bash start_web_interface.sh
# Opens Flask server on http://localhost:5000

# Command line pipeline
python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt

# Individual modules
python molecular_docking.py protein_structure.pdbqt original_ligand.pdbqt
python docking_visualization.py protein_receptor.pdbqt docking_results.pdbqt
```

### Web API Development
```bash
# Start Flask development server
python docking_web_api.py

# Test API endpoints
curl -X POST http://localhost:5000/api/docking -F "protein=@protein_structure.pdbqt" -F "ligand=@original_ligand.pdbqt"
```

## Key Integration Points

### File Processing Pipeline
1. **ProteinPreprocessor.fix_protein_structure()** - Removes ROOT/ENDROOT tags from PDBQT files
2. **VinaDocking.run_docking()** - Executes AutoDock Vina with customizable parameters
3. **DockingVisualizer.create_pymol_session()** - Generates PyMOL session and images
4. **DockingVisualizer.create_web_viewer()** - Creates interactive 3DMol.js HTML viewer

### Configuration Points
- **Search space parameters** in molecular_docking.py (center coordinates, dimensions)
- **Vina execution parameters** (exhaustiveness, num_modes, energy_range)
- **PyMOL visualization settings** (colors, representations, image resolution)
- **Web interface styling** in docking_web_interface.html

### Output Structure
```
docking_results/
├── protein_receptor.pdbqt      # Cleaned protein structure
├── docking_results.pdbqt       # Multiple binding poses with energies
├── 3dmol_docking_viewer.html   # Interactive web viewer
├── pymol_docking_viewer.py     # PyMOL session script
├── *.png                       # High-quality images (overview, binding_site, etc.)
└── api.log                     # Pipeline execution log
```

## Development Notes

### Python Environment
- Uses hardcoded Python path: `/Users/wenzhenxiong/Documents/DevProj/proteindance/.conda/bin/python`
- Scripts are designed to work with this specific PyMOL-enabled Python installation
- All Python scripts have shebang pointing to this interpreter

### Conda Environment Management
- **molecular-docking** environment contains PyMOL, RDKit, OpenBabel, and scientific computing stack
- Isolated from main ProteinDance environment to avoid dependency conflicts
- Environment defined in environment.yml with conda-forge, bioconda channels

### AutoDock Vina Integration
- Vina binary must be executable: `chmod +x vina`
- Default search space: center (0,0,0), size (20,20,20)
- Configurable via command line parameters in molecular_docking.py
- Error handling for missing binary or execution failures

### Visualization Architecture
- **PyMOL**: Headless mode for automated image generation, multiple viewing angles
- **3DMol.js**: Web-based viewer with protein surface, ligand highlighting, interaction display
- **Flask API**: RESTful endpoints for file upload, job status, result retrieval

### Web Interface Features
- Drag-and-drop file upload for protein and ligand structures
- Real-time progress tracking with job status API
- Automatic display of generated images and 3D viewer
- Download links for all output files

### Common Issues
- **PyMOL import errors**: Ensure molecular-docking conda environment is activated
- **Vina executable not found**: Check ./vina binary exists and is executable
- **PDBQT format issues**: Input files must be properly formatted PDBQT structures
- **Web interface CORS**: Flask-CORS enabled for cross-origin requests

## Integration with Main Project

This pipeline can be integrated into the main ProteinDance platform by:
1. Importing molecular_docking and docking_visualization modules into backend services
2. Adding REST API endpoints to backend/app.py using patterns from docking_web_api.py
3. Integrating 3DMol.js viewer into React frontend components
4. Adding molecular docking as a workflow step in the 8-step drug discovery process