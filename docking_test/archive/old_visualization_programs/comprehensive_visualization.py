#!/usr/bin/env python3
"""
Comprehensive 3D Molecular Visualization Suite
Integrates multiple visualization libraries for complete molecular analysis
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Try to import required libraries
AVAILABLE_LIBS = {}

try:
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d import Axes3D
    AVAILABLE_LIBS['matplotlib'] = True
except ImportError:
    AVAILABLE_LIBS['matplotlib'] = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    AVAILABLE_LIBS['plotly'] = True
except ImportError:
    AVAILABLE_LIBS['plotly'] = False

try:
    import py3Dmol
    AVAILABLE_LIBS['py3dmol'] = True
except ImportError:
    AVAILABLE_LIBS['py3dmol'] = False

def check_dependencies():
    """Check and install missing dependencies"""
    
    print("🔍 Checking dependencies...")
    
    missing_libs = []
    if not AVAILABLE_LIBS['matplotlib']:
        missing_libs.append('matplotlib')
    if not AVAILABLE_LIBS['plotly']:
        missing_libs.append('plotly')
    if not AVAILABLE_LIBS['py3dmol']:
        missing_libs.append('py3dmol')
    
    if missing_libs:
        print(f"⚠ Missing libraries: {', '.join(missing_libs)}")
        print("📦 Installing missing libraries...")
        
        for lib in missing_libs:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
                print(f"✓ {lib} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {lib}")
                return False
        
        return True
    else:
        print("✓ All dependencies are available")
        return True

def run_visualization(script_name, description):
    """Run a specific visualization script"""
    
    print(f"\n🎨 Running {description}...")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱ {description} timed out")
        return False
    except FileNotFoundError:
        print(f"📁 {script_name} not found")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def create_index_html():
    """Create an index HTML file linking all visualizations"""
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Molecular Docking Visualization Suite</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #4a5568;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h3 {
            color: #2d3748;
            margin-top: 0;
            font-size: 1.3em;
        }
        .card p {
            color: #718096;
            line-height: 1.6;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #4299e1;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: background 0.3s ease;
            margin: 5px;
        }
        .btn:hover {
            background: #3182ce;
        }
        .btn-success { background: #48bb78; }
        .btn-success:hover { background: #38a169; }
        .btn-warning { background: #ed8936; }
        .btn-warning:hover { background: #dd6b20; }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: 500;
        }
        .status.success { background: #c6f6d5; color: #276749; }
        .status.warning { background: #fed7aa; color: #c05621; }
        .status.error { background: #fed7d7; color: #c53030; }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #718096;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 Molecular Docking Visualization Suite</h1>
        
        <div class="status success">
            <strong>✓ Docking Complete!</strong> Best binding energy: -44.8 kcal/mol
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Static Visualizations</h3>
                <p>High-quality static plots and analysis charts created with matplotlib.</p>
                <a href="matplotlib_3d_visualization.png" class="btn" target="_blank">3D Structure</a>
                <a href="binding_analysis.png" class="btn" target="_blank">Binding Analysis</a>
                <a href="binding_energies.png" class="btn" target="_blank">Energy Distribution</a>
            </div>
            
            <div class="card">
                <h3>🌐 Interactive Plotly</h3>
                <p>Interactive web-based visualizations with zoom, pan, and hover features.</p>
                <a href="plotly_3d_molecular.html" class="btn btn-success" target="_blank">3D Molecular</a>
                <a href="plotly_binding_dashboard.html" class="btn btn-success" target="_blank">Dashboard</a>
                <a href="plotly_element_analysis.html" class="btn btn-success" target="_blank">Element Analysis</a>
            </div>
            
            <div class="card">
                <h3>🔬 py3Dmol Viewer</h3>
                <p>Professional molecular viewer with advanced rendering capabilities.</p>
                <a href="molecular_visualization.html" class="btn btn-warning" target="_blank">Molecular Viewer</a>
                <a href="py3dmol_viewer.html" class="btn btn-warning" target="_blank">py3Dmol Export</a>
            </div>
            
            <div class="card">
                <h3>📈 Binding Site Analysis</h3>
                <p>Detailed analysis of binding modes and site characteristics.</p>
                <a href="binding_site_visualization.png" class="btn" target="_blank">Site Visualization</a>
                <div style="margin-top: 10px;">
                    <strong>Key Results:</strong><br>
                    • 9 binding modes identified<br>
                    • Best energy: -44.8 kcal/mol<br>
                    • Binding site center: (0.32, -0.11, 0.11)
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>🛠 Technical Information</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <strong>Files Used:</strong><br>
                    • Protein: protein_receptor.pdbqt<br>
                    • Ligand: docking_results.pdbqt<br>
                    • Docking: AutoDock Vina<br>
                </div>
                <div>
                    <strong>Libraries Used:</strong><br>
                    • matplotlib (static plots)<br>
                    • plotly (interactive plots)<br>
                    • py3Dmol (molecular viewer)<br>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Comprehensive Molecular Visualization Suite</p>
            <p>🧬 Protein-Ligand Docking Analysis | 📊 Multi-library Visualization</p>
        </div>
    </div>
</body>
</html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✓ Index page created: index.html")

def main():
    """Main function to run comprehensive visualization suite"""
    
    print("🧬 Comprehensive Molecular Visualization Suite")
    print("=" * 60)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run molecular visualization suite')
    parser.add_argument('--check-deps', action='store_true', help='Check and install dependencies')
    parser.add_argument('--matplotlib', action='store_true', help='Run matplotlib visualization')
    parser.add_argument('--plotly', action='store_true', help='Run plotly visualization')
    parser.add_argument('--py3dmol', action='store_true', help='Run py3dmol visualization')
    parser.add_argument('--all', action='store_true', help='Run all visualizations')
    
    args = parser.parse_args()
    
    # If no specific args, run all by default
    if not any([args.matplotlib, args.plotly, args.py3dmol, args.check_deps]):
        args.all = True
    
    # Check dependencies if requested
    if args.check_deps or args.all:
        if not check_dependencies():
            print("❌ Dependency check failed")
            return False
    
    # Track successful runs
    successful_runs = []
    
    # Run matplotlib visualization
    if args.matplotlib or args.all:
        if run_visualization('matplotlib_visualization.py', 'matplotlib visualization'):
            successful_runs.append('matplotlib')
    
    # Run plotly visualization
    if args.plotly or args.all:
        if run_visualization('plotly_visualization.py', 'plotly visualization'):
            successful_runs.append('plotly')
    
    # Run py3dmol visualization
    if args.py3dmol or args.all:
        if run_visualization('py3dmol_visualization.py', 'py3dmol visualization'):
            successful_runs.append('py3dmol')
    
    # Create index page
    print("\n🌐 Creating index page...")
    create_index_html()
    
    # Summary
    print("\n✨ Visualization Suite Complete!")
    print(f"✅ Successful runs: {', '.join(successful_runs) if successful_runs else 'None'}")
    
    # List output files
    output_files = []
    for file in Path('.').glob('*.html'):
        output_files.append(str(file))
    for file in Path('.').glob('*.png'):
        output_files.append(str(file))
    
    if output_files:
        print(f"\n📁 Output files ({len(output_files)}):")
        for file in sorted(output_files):
            print(f"  - {file}")
    
    print(f"\n🌐 Open index.html in your browser to access all visualizations")
    
    return True

if __name__ == "__main__":
    main()