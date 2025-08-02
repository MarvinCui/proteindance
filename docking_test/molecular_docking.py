#!/Users/wenzhenxiong/Documents/DevProj/proteindance/.conda/bin/python
"""
Molecular Docking Pipeline
Integrates protein preparation, docking execution, and result analysis
"""

import os
import subprocess
import sys
from pathlib import Path

class ProteinPreprocessor:
    """Handles protein structure preparation for docking"""
    
    def __init__(self):
        self.input_file = None
        self.output_file = None
    
    def fix_protein_structure(self, input_file, output_file=None):
        """
        Clean protein structure by removing ROOT/ENDROOT tags
        Based on fix_new_protein.py functionality
        """
        if output_file is None:
            output_file = input_file.replace('.pdbqt', '_receptor.pdbqt')
        
        self.input_file = input_file
        self.output_file = output_file
        
        print(f"Processing protein structure: {input_file}")
        
        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
            
            # Filter out problematic lines
            filtered_lines = []
            removed_count = 0
            
            for line in lines:
                line_strip = line.strip()
                # Remove ROOT, ENDROOT, BRANCH, ENDBRANCH, TORSDOF tags
                if any(tag in line_strip for tag in ['ROOT', 'ENDROOT', 'BRANCH', 'ENDBRANCH', 'TORSDOF']):
                    removed_count += 1
                    continue
                filtered_lines.append(line)
            
            # Write cleaned file
            with open(output_file, 'w') as f:
                f.writelines(filtered_lines)
            
            print(f"✓ Cleaned protein structure saved as: {output_file}")
            print(f"✓ Removed {removed_count} problematic lines")
            
            return output_file
            
        except Exception as e:
            print(f"✗ Error processing protein: {e}")
            return None

class MolecularDocker:
    """Handles AutoDock Vina molecular docking"""
    
    def __init__(self, vina_executable="./vina"):
        self.vina_executable = vina_executable
        self.receptor_file = None
        self.ligand_file = None
        self.output_file = None
        self.config = {
            'center_x': 2.8,
            'center_y': 23.3, 
            'center_z': 14.1,
            'size_x': 25.0,
            'size_y': 25.0,
            'size_z': 25.0,
            'exhaustiveness': 8,
            'num_modes': 9,
            'energy_range': 3
        }
    
    def set_files(self, receptor_file, ligand_file, output_file="docking_results.pdbqt"):
        """Set input and output files"""
        self.receptor_file = receptor_file
        self.ligand_file = ligand_file
        self.output_file = output_file
    
    def set_search_space(self, center_x, center_y, center_z, size_x=20, size_y=20, size_z=20):
        """Define docking search space"""
        self.config.update({
            'center_x': center_x,
            'center_y': center_y,
            'center_z': center_z,
            'size_x': size_x,
            'size_y': size_y,
            'size_z': size_z
        })
    
    def run_docking(self):
        """Execute molecular docking with Vina"""
        if not all([self.receptor_file, self.ligand_file]):
            print("✗ Error: Receptor and ligand files must be set")
            return False
        
        # Check if files exist
        if not os.path.exists(self.receptor_file):
            print(f"✗ Error: Receptor file not found: {self.receptor_file}")
            return False
            
        if not os.path.exists(self.ligand_file):
            print(f"✗ Error: Ligand file not found: {self.ligand_file}")
            return False
        
        # Check Vina executable
        if not os.path.exists(self.vina_executable):
            print(f"✗ Error: Vina executable not found: {self.vina_executable}")
            return False
        
        # Build Vina command
        cmd = [
            self.vina_executable,
            "--receptor", self.receptor_file,
            "--ligand", self.ligand_file,
            "--out", self.output_file,
            "--center_x", str(self.config['center_x']),
            "--center_y", str(self.config['center_y']),
            "--center_z", str(self.config['center_z']),
            "--size_x", str(self.config['size_x']),
            "--size_y", str(self.config['size_y']),
            "--size_z", str(self.config['size_z']),
            "--exhaustiveness", str(self.config['exhaustiveness']),
            "--num_modes", str(self.config['num_modes']),
            "--energy_range", str(self.config['energy_range'])
        ]
        
        print("Running molecular docking...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            # Run docking with longer timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("✓ Docking completed successfully!")
                print(f"✓ Results saved to: {self.output_file}")
                
                # Parse and display results
                self._parse_results()
                return True
            else:
                print(f"✗ Docking failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Docking timed out after 10 minutes")
            return False
        except Exception as e:
            print(f"✗ Error running docking: {e}")
            return False
    
    def _parse_results(self):
        """Parse and display docking results"""
        if not os.path.exists(self.output_file):
            return
        
        try:
            with open(self.output_file, 'r') as f:
                content = f.read()
            
            # Extract binding energies
            energies = []
            for line in content.split('\n'):
                if line.startswith('REMARK VINA RESULT:'):
                    parts = line.split()
                    if len(parts) >= 4:
                        energy = float(parts[3])
                        energies.append(energy)
            
            if energies:
                print(f"\n=== Docking Results ===")
                for i, energy in enumerate(energies, 1):
                    print(f"Model {i}: {energy:.3f} kcal/mol")
                
                best_energy = min(energies)
                print(f"Best binding energy: {best_energy:.3f} kcal/mol")
            
        except Exception as e:
            print(f"Warning: Could not parse results: {e}")

def run_complete_docking_pipeline(protein_file, ligand_file, output_dir="./docking_results", docking_params=None):
    """Run complete docking pipeline from raw files to results"""
    
    print("=== Molecular Docking Pipeline ===")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Step 1: Prepare protein
    print("\n1. Preparing protein structure...")
    preprocessor = ProteinPreprocessor()
    receptor_file = preprocessor.fix_protein_structure(
        protein_file, 
        os.path.join(output_dir, "protein_receptor.pdbqt")
    )
    
    if not receptor_file:
        print("✗ Failed to prepare protein structure")
        return False
    
    # Step 2: Run docking
    print("\n2. Running molecular docking...")
    docker = MolecularDocker()
    docker.set_files(
        receptor_file, 
        ligand_file, 
        os.path.join(output_dir, "docking_results.pdbqt")
    )
    
    # Apply custom docking parameters if provided
    if docking_params:
        print(f"Using custom docking parameters: {docking_params}")
        
        # Update search space
        if 'center_x' in docking_params:
            docker.config['center_x'] = docking_params['center_x']
        if 'center_y' in docking_params:
            docker.config['center_y'] = docking_params['center_y']
        if 'center_z' in docking_params:
            docker.config['center_z'] = docking_params['center_z']
        if 'search_size' in docking_params:
            size = docking_params['search_size']
            docker.config.update({
                'size_x': size,
                'size_y': size,
                'size_z': size
            })
        
        # Update computation parameters
        if 'exhaustiveness' in docking_params:
            docker.config['exhaustiveness'] = docking_params['exhaustiveness']
        if 'num_modes' in docking_params:
            docker.config['num_modes'] = docking_params['num_modes']
        
        print(f"Updated docking config: {docker.config}")
    
    success = docker.run_docking()
    
    if success:
        print(f"\n✓ Pipeline completed successfully!")
        print(f"✓ Results available in: {output_dir}")
        return True
    else:
        print(f"\n✗ Pipeline failed")
        return False

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 3:
        print("Usage: python molecular_docking.py <protein_file> <ligand_file> [output_dir]")
        print("Example: python molecular_docking.py protein_structure.pdbqt original_ligand.pdbqt")
        return
    
    protein_file = sys.argv[1]
    ligand_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "./docking_results"
    
    run_complete_docking_pipeline(protein_file, ligand_file, output_dir)

if __name__ == "__main__":
    main()