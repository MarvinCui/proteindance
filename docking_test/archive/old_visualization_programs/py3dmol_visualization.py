#!/usr/bin/env python3
"""
3D Molecular Visualization Script using py3Dmol
Alternative to PyMOL for interactive molecular visualization
"""

import py3Dmol
from IPython.display import display, HTML
import json

def create_3d_visualization():
    """Create interactive 3D molecular visualization"""
    
    # Create viewer
    viewer = py3Dmol.view(width=800, height=600)
    
    # Load protein structure
    try:
        with open('../protein_receptor.pdbqt', 'r') as f:
            protein_data = f.read()
        
        # Add protein to viewer
        viewer.addModel(protein_data, 'pdbqt')
        
        # Style protein as cartoon
        viewer.setStyle({'model': 0}, {
            'cartoon': {
                'color': 'lightblue',
                'opacity': 0.8
            }
        })
        
        print("✓ Protein structure loaded successfully")
        
    except FileNotFoundError:
        print("⚠ Protein file not found, using example structure")
        viewer.addModel('', 'pdb')
    
    # Load docking results
    try:
        with open('docking_results.pdbqt', 'r') as f:
            ligand_data = f.read()
        
        # Add ligand to viewer
        viewer.addModel(ligand_data, 'pdbqt')
        
        # Style ligand as sticks
        viewer.setStyle({'model': 1}, {
            'stick': {
                'colorscheme': 'default',
                'radius': 0.3
            }
        })
        
        print("✓ Ligand structure loaded successfully")
        
    except FileNotFoundError:
        print("⚠ Docking results file not found")
    
    # Set background color
    viewer.setBackgroundColor('white')
    
    # Add surface for binding site
    viewer.addSurface(py3Dmol.VDW, {
        'opacity': 0.3,
        'color': 'yellow'
    }, {
        'model': 0,
        'within': {'distance': 5, 'sel': {'model': 1}}
    })
    
    # Center view on ligand
    viewer.zoomTo({'model': 1})
    
    # Add zoom control
    viewer.zoom(1.2)
    
    return viewer

def create_html_visualization():
    """Create HTML file with embedded 3D visualization"""
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Molecular Docking Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/1.8.0/3Dmol-min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #viewer { width: 800px; height: 600px; border: 1px solid #ddd; }
        .controls { margin: 10px 0; }
        .info { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        button { margin: 5px; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
    </style>
</head>
<body>
    <h1>Molecular Docking Visualization</h1>
    
    <div class="info">
        <h3>Visualization Controls:</h3>
        <ul>
            <li><strong>Mouse:</strong> Left click + drag to rotate, Right click + drag to zoom, Middle click + drag to pan</li>
            <li><strong>Protein:</strong> Shown as cartoon in light blue</li>
            <li><strong>Ligand:</strong> Shown as sticks with element colors</li>
            <li><strong>Binding Site:</strong> Yellow surface around ligand</li>
        </ul>
    </div>
    
    <div class="controls">
        <button class="btn-primary" onclick="resetView()">Reset View</button>
        <button class="btn-secondary" onclick="toggleProtein()">Toggle Protein</button>
        <button class="btn-secondary" onclick="toggleLigand()">Toggle Ligand</button>
        <button class="btn-secondary" onclick="toggleSurface()">Toggle Surface</button>
    </div>
    
    <div id="viewer"></div>
    
    <script>
        let viewer;
        let proteinVisible = true;
        let ligandVisible = true;
        let surfaceVisible = true;
        
        function initViewer() {
            viewer = $3Dmol.createViewer('viewer', {
                defaultcolors: $3Dmol.elementColors.Jmol
            });
            
            // Load protein structure
            fetch('../protein_receptor.pdbqt')
                .then(response => response.text())
                .then(data => {
                    viewer.addModel(data, 'pdbqt');
                    viewer.setStyle({model: 0}, {
                        cartoon: {color: 'lightblue', opacity: 0.8}
                    });
                    
                    // Load ligand
                    return fetch('docking_results.pdbqt');
                })
                .then(response => response.text())
                .then(data => {
                    viewer.addModel(data, 'pdbqt');
                    viewer.setStyle({model: 1}, {
                        stick: {colorscheme: 'default', radius: 0.3}
                    });
                    
                    // Add binding site surface
                    viewer.addSurface($3Dmol.VDW, {
                        opacity: 0.3,
                        color: 'yellow'
                    }, {
                        model: 0,
                        within: {distance: 5, sel: {model: 1}}
                    });
                    
                    viewer.zoomTo({model: 1});
                    viewer.render();
                })
                .catch(error => {
                    console.error('Error loading files:', error);
                    document.getElementById('viewer').innerHTML = 
                        '<p style="text-align:center; color:red; padding:50px;">Error loading molecular structures. Please ensure the PDBQT files are in the correct location.</p>';
                });
        }
        
        function resetView() {
            viewer.zoomTo({model: 1});
            viewer.render();
        }
        
        function toggleProtein() {
            proteinVisible = !proteinVisible;
            viewer.setStyle({model: 0}, proteinVisible ? 
                {cartoon: {color: 'lightblue', opacity: 0.8}} : 
                {});
            viewer.render();
        }
        
        function toggleLigand() {
            ligandVisible = !ligandVisible;
            viewer.setStyle({model: 1}, ligandVisible ? 
                {stick: {colorscheme: 'default', radius: 0.3}} : 
                {});
            viewer.render();
        }
        
        function toggleSurface() {
            surfaceVisible = !surfaceVisible;
            if (surfaceVisible) {
                viewer.addSurface($3Dmol.VDW, {
                    opacity: 0.3,
                    color: 'yellow'
                }, {
                    model: 0,
                    within: {distance: 5, sel: {model: 1}}
                });
            } else {
                viewer.removeAllSurfaces();
            }
            viewer.render();
        }
        
        // Initialize when page loads
        window.onload = initViewer;
    </script>
</body>
</html>
    """
    
    with open('molecular_visualization.html', 'w') as f:
        f.write(html_content)
    
    print("✓ HTML visualization created: molecular_visualization.html")
    print("  Open this file in a web browser to view the interactive 3D structure")

def main():
    """Main function to run visualization"""
    print("🧬 Creating 3D Molecular Visualization")
    print("=" * 50)
    
    try:
        # Create HTML visualization (works without Jupyter)
        create_html_visualization()
        
        # Try to create py3Dmol visualization for Jupyter
        try:
            viewer = create_3d_visualization()
            print("✓ py3Dmol viewer created successfully")
            print("  Note: This requires Jupyter notebook to display")
            
            # Save viewer as HTML
            viewer.write_html('py3dmol_viewer.html')
            print("✓ py3Dmol HTML saved as: py3dmol_viewer.html")
            
        except Exception as e:
            print(f"⚠ py3Dmol visualization failed: {e}")
            print("  HTML fallback created instead")
        
        print("\n📁 Output files:")
        print("  - molecular_visualization.html (standalone HTML)")
        print("  - py3dmol_viewer.html (py3Dmol export)")
        
        print("\n🌐 To view:")
        print("  1. Open molecular_visualization.html in any web browser")
        print("  2. Or run this script in Jupyter notebook")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()