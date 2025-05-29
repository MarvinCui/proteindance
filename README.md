# ProteinDance: Advanced Ligand-Binding Site Prediction and AI Molecular Optimization Framework

---

## Introduction

ProteinDance is a cutting-edge computational framework for molecular biology, integrating machine learning and artificial intelligence to predict ligand-binding pockets, optimize molecular structures, and streamline workflows in drug discovery. By leveraging state-of-the-art algorithms, ProteinDance enables researchers to accelerate ligand-binding site identification, molecular docking, and lead optimization.

## Key Features

1. **Ligand-Binding Site Prediction**:
   - **Algorithm**: ProteinDance employs advanced machine learning models to score and cluster points on a protein's solvent-accessible surface. The ligandability score is computed based on datasets of protein-ligand complexes, ensuring high prediction accuracy.
   - **Visualization**: Generates PyMol and ChimeraX visualizations of predicted pockets for enhanced interpretability.

2. **AI Molecular Optimization**:
   - Optimizes molecular structures using artificial intelligence to select the best candidate compounds for therapeutic applications.
   - Performs post-optimization analysis, including SMILES structure refinement and molecular visualization.

3. **Automated Workflows**:
   - Streamlined workflows for disease-specific target selection, ligand structure retrieval, ligand-binding site prediction, and molecular optimization.
   - ASCII visualization and high-quality molecule image generation for molecular structures.

4. **Integration with External Libraries**:
   - Utilizes FastRandomForest, BioJava, Chemistry Development Kit, and RDKit for computational efficiency and scientific rigor.

---

## Working Mechanism

### Ligand-Binding Site Prediction

ProteinDance employs a machine learning-based algorithm that clusters and scores solvent-accessible surface points on protein structures. Each point receives a ligandability score based on its likelihood of being part of a ligand-binding site. The algorithm is trained on datasets of known protein-ligand complexes, ensuring robust predictions across diverse protein structures.

### AI Molecular Optimization

- **SMILES Refinement**: AI models analyze SMILES strings to select optimal molecular candidates.
- **Compound Selection**: Machine learning models simulate docking processes to identify compounds with the highest therapeutic potential.
- **Visualization**: High-resolution molecular images are generated for analysis and presentation.

### Automated Workflow

An automated pipeline guides researchers through:
1. Disease-specific target identification.
2. Ligand structure retrieval and preprocessing.
3. Ligand-binding site prediction using machine learning algorithms.
4. AI-driven molecular optimization and visualization.

---

## Principles

ProteinDance adheres to the following computational principles:

1. **Scientific Accuracy**: Leveraging validated datasets and published algorithms to ensure reliability.
2. **Efficiency**: Optimized for multi-core systems, enabling parallel processing of large datasets.
3. **Interoperability**: Seamlessly integrates with external libraries and visualization tools for enhanced functionality.
4. **Transparency**: Detailed logging mechanisms and customizable configurations provide researchers with full control over computational workflows.

---

## Setup and Installation

### Requirements

- **Java**: Version 17 to 23
- **Python**: Required for molecular optimization workflows
- **Visualization Tools**:
  - PyMol
  - ChimeraX (optional)

### Installation

ProteinDance requires no installation. Binary packages are available as GitHub Releases.

- **Download**: [GitHub Releases](https://github.com/MarvinCui/proteindance/releases)
- **Source Code**: [GitHub Repository](https://github.com/MarvinCui/proteindance)

---

## Usage

### Ligand-Binding Site Prediction
```bash
prank predict -f test_data/1fbl.pdb         # Predict pockets on a single PDB file
```

### Molecular Optimization
```python
from services_func import automated_workflow
workflow_result = automated_workflow(disease="Cancer", selected_targets=["EGFR"])
```

### Visualizations
- Generate high-quality molecular images using integrated AI visualization modules.

---

## Publications and References

ProteinDance is built upon research from leading publications:
- [P2Rank: Machine Learning-Based Ligand Binding Site Prediction](https://doi.org/10.1186/s13321-018-0285-8)
- [DockRMSD: Open-Source Tool for RMSD Calculation](https://doi.org/10.1186/s13321-015-0059-5)

---

## Contributing

We welcome contributions to improve ProteinDance. Submit bug reports and feature requests via [GitHub Issues](https://github.com/MarvinCui/proteindance/issues).

---

## License

ProteinDance is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for details.

---

## Acknowledgements

ProteinDance integrates several open-source libraries and frameworks:
- FastRandomForest
- BioJava
- Chemistry Development Kit
- RDKit

---
