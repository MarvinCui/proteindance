#!/Users/wenzhenxiong/Documents/DevProj/proteindance/.conda/bin/python
"""
Web API for Molecular Docking Pipeline
Simple Flask API to interface with the docking modules
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import time

# Import our docking modules
from molecular_docking import run_complete_docking_pipeline
from docking_visualization import visualize_docking_results

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Configuration
UPLOAD_FOLDER = './uploads'
RESULTS_FOLDER = './docking_results'
LOG_FILE = os.path.join(RESULTS_FOLDER, 'api.log')
ALLOWED_EXTENSIONS = {'pdbqt', 'pdb'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to track job status
job_status = {
    'running': False,
    'progress': 0,
    'message': 'Ready',
    'log': [],
    'results': []
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_log(message):
    """Add message to job log"""
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    job_status['log'].append(log_entry)
    print(log_entry)  # Also print to console

    # Write to log file
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(log_entry + '\n')
    except Exception as e:
        print(f"ERROR: Could not write to log file: {e}")

def update_progress(percent, message):
    """Update job progress"""
    job_status['progress'] = percent
    job_status['message'] = message
    add_log(message)

@app.route('/')
def index():
    """Serve the main interface"""
    return send_file('docking_web_interface.html')

@app.route('/api/status')
def get_status():
    """Get current job status"""
    return jsonify(job_status)

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        # Create upload directory if it doesn't exist
        Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
        
        uploaded_files = {}
        
        # Handle protein file
        if 'protein' in request.files:
            protein_file = request.files['protein']
            if protein_file and allowed_file(protein_file.filename):
                filename = secure_filename(protein_file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, f"protein_{filename}")
                protein_file.save(filepath)
                uploaded_files['protein'] = filepath
                add_log(f"Uploaded protein file: {filename}")
        
        # Handle ligand file
        if 'ligand' in request.files:
            ligand_file = request.files['ligand']
            if ligand_file and allowed_file(ligand_file.filename):
                filename = secure_filename(ligand_file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, f"ligand_{filename}")
                ligand_file.save(filepath)
                uploaded_files['ligand'] = filepath
                add_log(f"Uploaded ligand file: {filename}")
        
        return jsonify({
            'success': True,
            'files': uploaded_files,
            'message': f"Uploaded {len(uploaded_files)} files successfully"
        })
        
    except Exception as e:
        add_log(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/run_pipeline', methods=['POST'])
def run_pipeline():
    """Run the complete docking pipeline"""
    if job_status['running']:
        return jsonify({
            'success': False,
            'error': 'Another job is already running'
        }), 400
    
    try:
        data = request.get_json()
        
        # Use test files if no files uploaded
        protein_file = data.get('protein_file', './protein_structure.pdbqt')
        ligand_file = data.get('ligand_file', './original_ligand.pdbqt')
        output_dir = data.get('output_dir', RESULTS_FOLDER)
        
        # Pipeline options
        run_docking = data.get('run_docking', True)
        run_visualization = data.get('run_visualization', True)
        use_pymol = data.get('use_pymol', True)
        use_web = data.get('use_web', True)
        
        # Start pipeline in background thread
        def run_pipeline_thread():
            try:
                job_status['running'] = True
                job_status['log'] = []
                job_status['results'] = []
                
                update_progress(5, "Starting molecular docking pipeline...")
                
                if run_docking:
                    update_progress(10, "Preparing protein structure...")
                    update_progress(30, "Running molecular docking...")
                    
                    # Get docking parameters from request
                    docking_params = data.get('docking_params', {})
                    add_log(f"DEBUG: Docking parameters: {docking_params}")
                    
                    success = run_complete_docking_pipeline(
                        protein_file, ligand_file, output_dir, docking_params
                    )
                    
                    if not success:
                        update_progress(0, "Docking failed")
                        job_status['running'] = False
                        return
                    
                    update_progress(60, "Docking completed successfully")
                
                if run_visualization:
                    update_progress(70, "Generating visualizations...")
                    add_log("DEBUG: Starting visualization step")
                    
                    # Use output files from docking or original files
                    receptor_file = os.path.join(output_dir, "protein_receptor.pdbqt") if run_docking else protein_file
                    results_file = os.path.join(output_dir, "docking_results.pdbqt") if run_docking else ligand_file
                    
                    add_log(f"DEBUG: Receptor file: {receptor_file}")
                    add_log(f"DEBUG: Results file: {results_file}")
                    add_log(f"DEBUG: Output dir: {output_dir}")
                    add_log(f"DEBUG: Use PyMOL: {use_pymol}")
                    add_log(f"DEBUG: Use web: {use_web}")
                    
                    # Check if input files exist
                    if not os.path.exists(receptor_file):
                        add_log(f"ERROR: Receptor file not found: {receptor_file}")
                    else:
                        add_log(f"DEBUG: Receptor file exists, size: {os.path.getsize(receptor_file)} bytes")
                    
                    if not os.path.exists(results_file):
                        add_log(f"ERROR: Results file not found: {results_file}")
                    else:
                        add_log(f"DEBUG: Results file exists, size: {os.path.getsize(results_file)} bytes")
                    
                    # Test PyMOL availability in current process
                    try:
                        import pymol
                        add_log("DEBUG: PyMOL imported successfully in API process")
                        from pymol import cmd
                        add_log("DEBUG: PyMOL cmd module available")
                    except ImportError as e:
                        add_log(f"ERROR: PyMOL not available in API process: {e}")
                    
                    add_log("DEBUG: Calling visualize_docking_results...")
                    
                    try:
                        viz_success = visualize_docking_results(
                            receptor_file, results_file, output_dir,
                            use_pymol=use_pymol, use_web=use_web, interactive_pymol=False
                        )
                        add_log(f"DEBUG: visualize_docking_results returned: {viz_success}")
                    except Exception as e:
                        add_log(f"ERROR: visualize_docking_results failed: {e}")
                        import traceback
                        add_log(f"ERROR: Traceback: {traceback.format_exc()}")
                        viz_success = False
                    
                    update_progress(90, "Visualization completed")
                    
                    # Scan for result files BEFORE and AFTER
                    add_log(f"DEBUG: Scanning output directory: {output_dir}")
                    result_files = []
                    scientific_data = {}
                    
                    if os.path.exists(output_dir):
                        all_files = list(Path(output_dir).glob("*"))
                        add_log(f"DEBUG: All files in output dir: {[f.name for f in all_files]}")
                        
                        # Collect visualization images
                        for file_path in Path(output_dir).glob("*.png"):
                            result_files.append(file_path.name)
                            add_log(f"DEBUG: Found PNG: {file_path.name}")
                        
                        # Collect HTML viewers
                        for file_path in Path(output_dir).glob("*.html"):
                            result_files.append(file_path.name)
                            add_log(f"DEBUG: Found HTML: {file_path.name}")
                        
                        # Collect scientific reports
                        for file_path in Path(output_dir).glob("*.txt"):
                            if "analysis" in file_path.name or "summary" in file_path.name:
                                result_files.append(file_path.name)
                                add_log(f"DEBUG: Found analysis report: {file_path.name}")
                                
                                # Try to extract key data from report for UI display
                                try:
                                    with open(file_path, 'r') as f:
                                        report_content = f.read()
                                        # Extract best binding energy
                                        import re
                                        energy_match = re.search(r'Best Binding Energy:\s*([-+]?\d+\.?\d*)\s*kcal/mol', report_content)
                                        if energy_match:
                                            scientific_data['best_energy'] = float(energy_match.group(1))
                                        
                                        # Extract total models
                                        models_match = re.search(r'Total Models Generated:\s*(\d+)', report_content)
                                        if models_match:
                                            scientific_data['total_models'] = int(models_match.group(1))
                                except Exception as e:
                                    add_log(f"DEBUG: Could not parse scientific data: {e}")
                                    
                    else:
                        add_log(f"ERROR: Output directory does not exist: {output_dir}")
                    
                    job_status['results'] = result_files
                    job_status['scientific_data'] = scientific_data
                    add_log(f"DEBUG: Final result files list: {result_files}")
                    add_log(f"DEBUG: Scientific data: {scientific_data}")
                    add_log(f"Found {len(result_files)} result files")
                
                update_progress(100, "Pipeline completed successfully!")
                job_status['running'] = False
                
            except Exception as e:
                add_log(f"Pipeline error: {str(e)}")
                update_progress(0, f"Pipeline failed: {str(e)}")
                job_status['running'] = False
        
        # Start background thread
        thread = threading.Thread(target=run_pipeline_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Pipeline started successfully'
        })
        
    except Exception as e:
        add_log(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/run_docking_only', methods=['POST'])
def run_docking_only():
    """Run only the docking step"""
    if job_status['running']:
        return jsonify({
            'success': False,
            'error': 'Another job is already running'
        }), 400
    
    try:
        data = request.get_json()
        protein_file = data.get('protein_file', './protein_structure.pdbqt')
        ligand_file = data.get('ligand_file', './original_ligand.pdbqt')
        output_dir = data.get('output_dir', RESULTS_FOLDER)
        
        def run_docking_thread():
            try:
                job_status['running'] = True
                job_status['log'] = []
                
                update_progress(10, "Starting molecular docking...")
                
                success = run_complete_docking_pipeline(
                    protein_file, ligand_file, output_dir
                )
                
                if success:
                    update_progress(100, "Docking completed successfully!")
                else:
                    update_progress(0, "Docking failed")
                
                job_status['running'] = False
                
            except Exception as e:
                add_log(f"Docking error: {str(e)}")
                update_progress(0, f"Docking failed: {str(e)}")
                job_status['running'] = False
        
        thread = threading.Thread(target=run_docking_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Docking started successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/run_visualization_only', methods=['POST'])
def run_visualization_only():
    """Run only the visualization step"""
    if job_status['running']:
        return jsonify({
            'success': False,
            'error': 'Another job is already running'
        }), 400
    
    try:
        data = request.get_json()
        
        # Allow specifying files, otherwise use defaults from docking results
        protein_file = data.get('protein_file', os.path.join(RESULTS_FOLDER, 'protein_receptor.pdbqt'))
        ligand_file = data.get('ligand_file', os.path.join(RESULTS_FOLDER, 'docking_results.pdbqt'))
        output_dir = data.get('output_dir', RESULTS_FOLDER)
        
        add_log(f"Starting visualization with protein: {protein_file} and ligand: {ligand_file}")

        # Check if files exist before starting the thread
        if not os.path.exists(protein_file):
            add_log(f"Error: Protein file not found at {protein_file}")
            return jsonify({'success': False, 'error': f'Protein file not found: {protein_file}'}), 404
        if not os.path.exists(ligand_file):
            add_log(f"Error: Ligand file not found at {ligand_file}")
            return jsonify({'success': False, 'error': f'Ligand file not found: {ligand_file}'}), 404

        def run_visualization_thread():
            try:
                job_status['running'] = True
                job_status['log'] = []
                job_status['results'] = []
                
                update_progress(20, "Starting visualization...")
                
                success = visualize_docking_results(
                    protein_file, ligand_file, output_dir,
                    use_pymol=True, use_web=True, interactive_pymol=False
                )
                
                if success:
                    # Scan for result files including scientific analysis
                    result_files = []
                    scientific_data = {}
                    
                    if os.path.exists(output_dir):
                        # Collect visualization images
                        for file_path in Path(output_dir).glob("*.png"):
                            result_files.append(file_path.name)
                        # Collect HTML viewers
                        for file_path in Path(output_dir).glob("*.html"):
                            result_files.append(file_path.name)
                        # Collect scientific reports
                        for file_path in Path(output_dir).glob("*.txt"):
                            if "analysis" in file_path.name or "summary" in file_path.name:
                                result_files.append(file_path.name)
                                
                                # Extract key data for UI display
                                try:
                                    with open(file_path, 'r') as f:
                                        report_content = f.read()
                                        import re
                                        energy_match = re.search(r'Best Binding Energy:\s*([-+]?\d+\.?\d*)\s*kcal/mol', report_content)
                                        if energy_match:
                                            scientific_data['best_energy'] = float(energy_match.group(1))
                                        models_match = re.search(r'Total Models Generated:\s*(\d+)', report_content)
                                        if models_match:
                                            scientific_data['total_models'] = int(models_match.group(1))
                                except Exception as e:
                                    add_log(f"Could not parse scientific data: {e}")
                    
                    job_status['results'] = result_files
                    job_status['scientific_data'] = scientific_data
                    update_progress(100, "Visualization completed successfully!")
                else:
                    update_progress(0, "Visualization failed")
                
                job_status['running'] = False
                
            except Exception as e:
                add_log(f"Visualization error: {str(e)}")
                update_progress(0, f"Visualization failed: {str(e)}")
                job_status['running'] = False
        
        thread = threading.Thread(target=run_visualization_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Visualization started successfully'
        })
        
    except Exception as e:
        add_log(f"API Error in run_visualization_only: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/results')
def list_results():
    """List available result files"""
    try:
        result_files = []
        if os.path.exists(RESULTS_FOLDER):
            for file_path in Path(RESULTS_FOLDER).glob("*"):
                if file_path.is_file():
                    result_files.append({
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix
                    })
        
        return jsonify({
            'success': True,
            'files': result_files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/results/<filename>')
def get_result_file(filename):
    """Download a specific result file"""
    try:
        return send_from_directory(RESULTS_FOLDER, filename)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404

@app.route('/api/clear')
def clear_results():
    """Clear all results and logs"""
    try:
        # Clear job status
        job_status['log'] = []
        job_status['results'] = []
        job_status['progress'] = 0
        job_status['message'] = 'Ready'
        
        # Clear results directory
        if os.path.exists(RESULTS_FOLDER):
            shutil.rmtree(RESULTS_FOLDER)
        Path(RESULTS_FOLDER).mkdir(exist_ok=True)
        
        # Clear uploads directory
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
        
        add_log("Results and uploads cleared")
        
        return jsonify({
            'success': True,
            'message': 'Results cleared successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    # Create necessary directories
    Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
    Path(RESULTS_FOLDER).mkdir(exist_ok=True)
    # Initialize or clear the API log file
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"=== API Log Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except Exception as e:
        print(f"ERROR: Could not initialize log file: {e}")
    
    print("Starting Molecular Docking Web API...")
    print("Interface available at: http://localhost:5000")
    print("API endpoints:")
    print("  GET  /                     - Web interface")
    print("  GET  /api/status           - Job status")
    print("  POST /api/upload           - Upload files")
    print("  POST /api/run_pipeline     - Run complete pipeline")
    print("  POST /api/run_docking_only - Run docking only")
    print("  POST /api/run_visualization_only - Run visualization only")
    print("  GET  /api/results          - List results")
    print("  GET  /api/results/<file>   - Download result file")
    print("  GET  /api/clear            - Clear results")
    
    app.run(debug=True, host='0.0.0.0', port=5000)