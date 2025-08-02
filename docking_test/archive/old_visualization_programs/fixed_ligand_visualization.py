#!/usr/bin/env python3
"""
Fixed Ligand Visualization - Properly parse all ligand atoms
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re

def parse_ligand_pdbqt(filename):
    """Parse ligand PDBQT file and extract ALL atoms from first model"""
    atoms = []
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        in_first_model = False
        
        for line in lines:
            # Start reading from MODEL 1
            if line.startswith('MODEL 1'):
                in_first_model = True
                print("📖 Found MODEL 1, starting to parse ligand atoms...")
                continue
            
            # Stop at next model or end
            if line.startswith('MODEL 2') or line.startswith('ENDMDL'):
                if in_first_model:
                    print(f"✓ Finished parsing MODEL 1, found {len(atoms)} atoms")
                    break
            
            # Parse atoms only if we're in the first model
            if in_first_model and (line.startswith('ATOM') or line.startswith('HETATM')):
                try:
                    atom_name = line[12:16].strip()
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    
                    # Extract element from atom name
                    element = re.sub(r'[0-9]', '', atom_name)
                    if len(element) > 1:
                        element = element[0]
                    
                    atoms.append({
                        'name': atom_name,
                        'element': element,
                        'x': x,
                        'y': y,
                        'z': z
                    })
                except (ValueError, IndexError):
                    continue
    
    except FileNotFoundError:
        print(f"⚠ File not found: {filename}")
        return []
    
    return atoms

def parse_protein_pdbqt(filename):
    """Parse protein PDBQT file"""
    atoms = []
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    atom_name = line[12:16].strip()
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    
                    # Extract element from atom name
                    element = re.sub(r'[0-9]', '', atom_name)
                    if len(element) > 1:
                        element = element[0]
                    
                    atoms.append({
                        'name': atom_name,
                        'element': element,
                        'x': x,
                        'y': y,
                        'z': z
                    })
                except (ValueError, IndexError):
                    continue
    
    except FileNotFoundError:
        print(f"⚠ File not found: {filename}")
        return []
    
    return atoms

def create_proper_ligand_visualization(protein_atoms, ligand_atoms):
    """Create proper visualization showing the full ligand structure"""
    
    fig = plt.figure(figsize=(16, 12))
    
    # Main 3D plot
    ax1 = fig.add_subplot(221, projection='3d')
    
    # Calculate ligand center
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Plot protein atoms (sparse, around binding site)
    if protein_atoms:
        print(f"🔬 Plotting protein atoms around binding site...")
        
        # Filter protein atoms near ligand
        nearby_protein = []
        for atom in protein_atoms:
            dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                          (atom['y'] - ligand_center[1])**2 + 
                          (atom['z'] - ligand_center[2])**2)
            if 5.0 < dist < 15.0:  # 5-15Å from ligand
                nearby_protein.append(atom)
        
        # Sample protein atoms
        if nearby_protein:
            step = max(1, len(nearby_protein) // 1000)
            sampled_protein = nearby_protein[::step]
            
            protein_x = [atom['x'] for atom in sampled_protein]
            protein_y = [atom['y'] for atom in sampled_protein]
            protein_z = [atom['z'] for atom in sampled_protein]
            
            ax1.scatter(protein_x, protein_y, protein_z,
                       c='lightgray', alpha=0.3, s=10, 
                       label=f'Protein ({len(sampled_protein)} atoms)')
    
    # Plot ALL ligand atoms
    if ligand_atoms:
        print(f"🔬 Plotting ALL {len(ligand_atoms)} ligand atoms...")
        
        # Element colors
        element_colors = {
            'C': '#404040',  # Dark gray for carbon
            'N': '#0000FF',  # Blue for nitrogen
            'O': '#FF0000',  # Red for oxygen
            'S': '#FFFF00',  # Yellow for sulfur
            'P': '#FF8000',  # Orange for phosphorus
            'H': '#FFFFFF',  # White for hydrogen
            'F': '#90E050',  # Green for fluorine
            'Cl': '#1FF01F', # Green for chlorine
            'Br': '#A62929', # Brown for bromine
            'I': '#940094',  # Purple for iodine
            'default': '#FF1493'  # Pink for unknown
        }
        
        # Plot all ligand atoms
        for atom in ligand_atoms:
            color = element_colors.get(atom['element'], element_colors['default'])
            ax1.scatter(atom['x'], atom['y'], atom['z'],
                       c=color, s=80, alpha=0.8, 
                       edgecolor='black', linewidth=0.5)
        
        # Add bonds between nearby atoms
        print(f"🔗 Adding bonds between ligand atoms...")
        bond_count = 0
        for i, atom1 in enumerate(ligand_atoms):
            for j, atom2 in enumerate(ligand_atoms[i+1:], i+1):
                dist = np.sqrt((atom1['x'] - atom2['x'])**2 + 
                              (atom1['y'] - atom2['y'])**2 + 
                              (atom1['z'] - atom2['z'])**2)
                if dist < 2.0:  # Bond threshold
                    ax1.plot([atom1['x'], atom2['x']], 
                            [atom1['y'], atom2['y']], 
                            [atom1['z'], atom2['z']], 
                            color='gray', linewidth=1.5, alpha=0.7)
                    bond_count += 1
        
        print(f"✓ Added {bond_count} bonds")
    
    # Style the main plot
    ax1.set_title(f'Complete Ligand Structure\n({len(ligand_atoms)} atoms)', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('X (Å)')
    ax1.set_ylabel('Y (Å)')
    ax1.set_zlabel('Z (Å)')
    ax1.legend()
    
    # Focus on ligand
    if ligand_atoms:
        range_size = 12
        ax1.set_xlim(ligand_center[0] - range_size, ligand_center[0] + range_size)
        ax1.set_ylim(ligand_center[1] - range_size, ligand_center[1] + range_size)
        ax1.set_zlim(ligand_center[2] - range_size, ligand_center[2] + range_size)
    
    # Element composition pie chart
    ax2 = fig.add_subplot(222)
    if ligand_atoms:
        elements = [atom['element'] for atom in ligand_atoms]
        unique_elements, counts = np.unique(elements, return_counts=True)
        
        colors = [element_colors.get(elem, element_colors['default']) for elem in unique_elements]
        
        wedges, texts, autotexts = ax2.pie(counts, labels=unique_elements, 
                                          colors=colors, autopct='%1.1f%%',
                                          startangle=90)
        ax2.set_title('Ligand Element Composition')
    
    # Ligand size comparison
    ax3 = fig.add_subplot(223)
    if ligand_atoms:
        # Calculate ligand dimensions
        coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in ligand_atoms])
        dimensions = coords.max(axis=0) - coords.min(axis=0)
        
        ax3.bar(['X', 'Y', 'Z'], dimensions, color=['red', 'green', 'blue'], alpha=0.7)
        ax3.set_title('Ligand Dimensions (Å)')
        ax3.set_ylabel('Size (Å)')
    
    # Atom count comparison
    ax4 = fig.add_subplot(224)
    categories = ['Protein\n(sampled)', 'Ligand']
    atom_counts = [len(nearby_protein) if 'nearby_protein' in locals() else 0, len(ligand_atoms)]
    
    bars = ax4.bar(categories, atom_counts, color=['lightblue', 'orange'], alpha=0.7)
    ax4.set_title('Atom Count Comparison')
    ax4.set_ylabel('Number of Atoms')
    
    # Add value labels on bars
    for bar, count in zip(bars, atom_counts):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{count}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    return fig

def main():
    """Main function"""
    
    print("🧬 Fixed Ligand Visualization - Showing Complete Ligand Structure")
    print("=" * 70)
    
    # Parse molecular files with proper ligand parsing
    print("📖 Parsing protein structure...")
    protein_atoms = parse_protein_pdbqt('../protein_receptor.pdbqt')
    print(f"✓ Protein atoms: {len(protein_atoms)}")
    
    print("\n📖 Parsing ligand structure (MODEL 1 only)...")
    ligand_atoms = parse_ligand_pdbqt('docking_results.pdbqt')
    print(f"✓ Ligand atoms: {len(ligand_atoms)}")
    
    if not ligand_atoms:
        print("❌ No ligand atoms found! Check the file format.")
        return False
    
    # Show element composition
    if ligand_atoms:
        elements = [atom['element'] for atom in ligand_atoms]
        unique_elements, counts = np.unique(elements, return_counts=True)
        print(f"\n🧪 Ligand composition:")
        for elem, count in zip(unique_elements, counts):
            print(f"  {elem}: {count} atoms")
    
    # Create proper visualization
    print(f"\n🎨 Creating complete ligand visualization...")
    fig = create_proper_ligand_visualization(protein_atoms, ligand_atoms)
    fig.savefig('complete_ligand_visualization.png', dpi=300, bbox_inches='tight')
    print("✓ Complete ligand visualization saved: complete_ligand_visualization.png")
    
    # Show the plot
    plt.show()
    
    print(f"\n✨ Fixed ligand visualization complete!")
    print(f"📊 Now you can see the REAL ligand structure with {len(ligand_atoms)} atoms!")
    
    return True

if __name__ == "__main__":
    main()