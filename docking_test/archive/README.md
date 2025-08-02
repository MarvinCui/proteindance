# Molecular Docking Pipeline

Complete molecular docking and visualization pipeline integrating AutoDock Vina with PyMOL and web-based visualization.

## Features

🧬 **Molecular Docking**
- Protein structure preprocessing (removes ROOT/ENDROOT tags)
- AutoDock Vina integration for molecular docking
- Multiple binding pose generation
- Binding energy analysis

🎨 **Visualization**
- PyMOL-based 3D visualization with high-quality image generation
- Web-based interactive viewer using 3DMol.js
- Multiple viewing modes and model switching
- Professional molecular graphics

## Quick Start

### 1. Environment Setup

```bash
# Create conda environment
bash setup_environment.sh

# Activate environment
conda activate molecular-docking
```

### 2. Web Interface (Recommended)

```bash
# Start web interface
bash start_web_interface.sh

# Open browser to http://localhost:5000
```

The web interface provides:
- 🎨 **Beautiful GUI** with drag-and-drop file upload
- 📊 **Real-time progress** tracking and logging
- 🖼️ **Image display** of generated visualizations
- 🔬 **Interactive 3D viewer** with molecular controls
- ⚙️ **Pipeline configuration** options

### 3. Command Line Interface

```bash
# Basic usage
python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt

# With custom output directory
python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt --output ./my_results

# Interactive PyMOL session
python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt --interactive
```

### 4. View Results

- **Web interface**: Automatic display of results and 3D viewer
- **Web viewer**: Open `docking_results/3dmol_docking_viewer.html` in browser
- **Images**: View generated PNG files in output directory
- **PyMOL**: Use `--interactive` flag for live PyMOL session

## File Structure

```
docking_test/
├── molecular_docking.py       # Core docking module
├── docking_visualization.py   # Visualization module  
├── run_docking_pipeline.py    # Main pipeline script
├── environment.yml            # Conda environment
├── requirements.txt           # Python dependencies
├── setup_environment.sh       # Setup script
├── vina                       # AutoDock Vina executable
├── protein_structure.pdbqt    # Test protein
├── original_ligand.pdbqt      # Test ligand
└── docking_results/           # Output directory
    ├── protein_receptor.pdbqt
    ├── docking_results.pdbqt
    ├── 3dmol_docking_viewer.html
    └── *.png images
```

## Usage Examples

### Complete Pipeline
```bash
# Run docking + visualization
python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt
```

### Visualization Only
```bash
# Visualize existing results
python run_docking_pipeline.py --visualize-only ./docking_results/protein_receptor.pdbqt ./docking_results/docking_results.pdbqt
```

### Individual Modules
```bash
# Docking only
python molecular_docking.py protein_structure.pdbqt original_ligand.pdbqt

# Visualization only  
python docking_visualization.py protein_receptor.pdbqt docking_results.pdbqt
```

## Dependencies

### Core Requirements
- Python 3.9+
- NumPy, Matplotlib, Pandas
- BioPython for molecular structure handling

### Visualization
- **PyMOL**: `conda install -c conda-forge pymol-open-source`
- **3DMol.js**: Web-based viewer (no installation needed)
- **py3Dmol**: Python interface to 3DMol.js

### Optional
- **RDKit**: Advanced chemical informatics
- **OpenBabel**: Chemical format conversion

## Command Line Options

### run_docking_pipeline.py
```
python run_docking_pipeline.py <protein_file> <ligand_file> [options]

Options:
  --output, -o DIR      Output directory (default: ./docking_results)
  --visualize-only      Skip docking, only run visualization
  --interactive         Launch interactive PyMOL session
  --no-pymol           Skip PyMOL visualization
  --no-web             Skip web visualization
```

## Troubleshooting

### PyMOL Issues
```bash
# Install PyMOL via conda
conda install -c conda-forge pymol-open-source

# Alternative: pip install (may have issues)
pip install pymol
```

### Vina Executable
- Ensure `vina` binary is executable: `chmod +x vina`
- Download from: http://vina.scripps.edu/

### File Format Issues
- Input files must be in PDBQT format
- Use protein preparation tools if needed
- Check for ROOT/ENDROOT tags in protein files

## Output Files

### Docking Results
- `protein_receptor.pdbqt`: Cleaned protein structure
- `docking_results.pdbqt`: Multiple binding poses with energies

### Visualization
- `3dmol_docking_viewer.html`: Interactive web viewer
- `pymol_*.png`: High-quality images from PyMOL
- Multiple viewing angles and binding pose focuses

## Advanced Usage

### Custom Docking Parameters
Edit `molecular_docking.py` to modify:
- Search space dimensions
- Number of binding modes
- Exhaustiveness settings
- Energy range thresholds

### Visualization Customization
Edit `docking_visualization.py` to modify:
- Color schemes
- Molecular representations
- Image resolution and quality
- Viewing angles

## Integration with Main Project

This pipeline can be integrated with the ProteinDance platform:
1. Import modules into main backend
2. Use REST API endpoints for docking execution
3. Integrate web viewer into React frontend
4. Add workflow step for molecular docking

## License

This project uses:
- AutoDock Vina (Apache License 2.0)
- PyMOL (Open source license)
- 3DMol.js (BSD-3-Clause license)