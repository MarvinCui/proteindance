#!/Users/wenzhenxiong/Documents/DevProj/proteindance/.conda/bin/python
"""
Complete Molecular Docking and Visualization Pipeline
Integrates docking execution and result visualization
"""

import os
import sys
import argparse
from pathlib import Path

# Import our modules
from molecular_docking import run_complete_docking_pipeline
from docking_visualization import visualize_docking_results

def setup_argument_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Complete Molecular Docking and Visualization Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline with default settings
  python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt
  
  # Specify custom output directory
  python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt --output ./my_results
  
  # Skip docking and only visualize existing results
  python run_docking_pipeline.py --visualize-only ./docking_results/protein_receptor.pdbqt ./docking_results/docking_results.pdbqt
  
  # Run with interactive PyMOL session
  python run_docking_pipeline.py protein_structure.pdbqt original_ligand.pdbqt --interactive
        """
    )
    
    parser.add_argument("protein_file", help="Input protein structure file (.pdbqt)")
    parser.add_argument("ligand_file", help="Input ligand file (.pdbqt)")
    parser.add_argument("--output", "-o", default="./docking_results", 
                       help="Output directory (default: ./docking_results)")
    parser.add_argument("--visualize-only", action="store_true",
                       help="Skip docking, only run visualization")
    parser.add_argument("--interactive", action="store_true",
                       help="Launch interactive PyMOL session")
    parser.add_argument("--no-pymol", action="store_true",
                       help="Skip PyMOL visualization")
    parser.add_argument("--no-web", action="store_true",
                       help="Skip web visualization")
    
    return parser

def main():
    """Main pipeline function"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    print("=" * 60)
    print("   MOLECULAR DOCKING AND VISUALIZATION PIPELINE")
    print("=" * 60)
    
    # Validate input files
    if not os.path.exists(args.protein_file):
        print(f"✗ Error: Protein file not found: {args.protein_file}")
        return 1
    
    if not os.path.exists(args.ligand_file):
        print(f"✗ Error: Ligand file not found: {args.ligand_file}")
        return 1
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    success = True
    
    if not args.visualize_only:
        # Step 1: Run molecular docking
        print("\\nSTEP 1: MOLECULAR DOCKING")
        print("-" * 30)
        
        docking_success = run_complete_docking_pipeline(
            args.protein_file, 
            args.ligand_file, 
            str(output_dir)
        )
        
        if not docking_success:
            print("✗ Docking pipeline failed")
            return 1
            
        # Set files for visualization
        receptor_file = output_dir / "protein_receptor.pdbqt"
        results_file = output_dir / "docking_results.pdbqt"
    else:
        print("\\nSKIPPING DOCKING - Visualization only mode")
        receptor_file = args.protein_file
        results_file = args.ligand_file
    
    # Step 2: Visualize results
    print("\\nSTEP 2: VISUALIZATION")
    print("-" * 20)
    
    viz_success = visualize_docking_results(
        str(receptor_file),
        str(results_file),
        str(output_dir),
        use_pymol=not args.no_pymol,
        use_web=not args.no_web,
        interactive_pymol=args.interactive
    )
    
    if not viz_success:
        print("⚠ Some visualization components failed")
        success = False
    
    # Summary
    print("\\n" + "=" * 60)
    if success:
        print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"✓ Results available in: {output_dir}")
        
        print("\\nGenerated files:")
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                print(f"  - {file_path.name}")
        
        print("\\nNext steps:")
        print("  1. Open 3dmol_docking_viewer.html in your browser")
        print("  2. View generated PNG images")
        if not args.no_pymol:
            print("  3. Re-run with --interactive for PyMOL session")
            
    else:
        print("⚠ PIPELINE COMPLETED WITH WARNINGS")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())