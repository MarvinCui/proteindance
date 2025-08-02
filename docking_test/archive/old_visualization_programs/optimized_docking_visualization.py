#!/usr/bin/env python3
"""
Optimized Docking Visualization - Shows binding site clearly
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re

# Element colors (CPK coloring scheme)
ELEMENT_COLORS = {
    'C': '#909090',  # Carbon - gray
    'N': '#3050F8',  # Nitrogen - blue  
    'O': '#FF0D0D',  # Oxygen - red
    'S': '#FFFF30',  # Sulfur - yellow
    'P': '#FF8000',  # Phosphorus - orange
    'H': '#FFFFFF',  # Hydrogen - white
    'default': '#FF1493'  # Default - pink
}

def parse_pdbqt(filename):
    """Parse PDBQT file and extract atom coordinates"""
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

def calculate_binding_site_exposure(protein_atoms, ligand_atoms):
    """Calculate which direction exposes the binding site best"""
    
    if not ligand_atoms or not protein_atoms:
        return 15, 130  # Default angle
    
    # Calculate ligand center
    ligand_center = np.array([
        np.mean([atom['x'] for atom in ligand_atoms]),
        np.mean([atom['y'] for atom in ligand_atoms]),
        np.mean([atom['z'] for atom in ligand_atoms])
    ])
    
    # Find binding site atoms (close to ligand)
    binding_atoms = []
    for atom in protein_atoms:
        dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                      (atom['y'] - ligand_center[1])**2 + 
                      (atom['z'] - ligand_center[2])**2)
        if dist < 8.0:  # Within 8Å of ligand
            binding_atoms.append(atom)
    
    if not binding_atoms:
        return 15, 130
    
    # Calculate center of mass of binding site
    binding_center = np.array([
        np.mean([atom['x'] for atom in binding_atoms]),
        np.mean([atom['y'] for atom in binding_atoms]),
        np.mean([atom['z'] for atom in binding_atoms])
    ])
    
    # Test different viewing angles and find the one with least occlusion
    best_angle = None
    min_occlusion = float('inf')
    
    for azim in range(0, 360, 30):  # Test every 30 degrees
        for elev in range(0, 60, 15):  # Test different elevations
            # Calculate view direction
            azim_rad = np.radians(azim)
            elev_rad = np.radians(elev)
            
            view_dir = np.array([
                np.cos(elev_rad) * np.cos(azim_rad),
                np.cos(elev_rad) * np.sin(azim_rad),
                np.sin(elev_rad)
            ])
            
            # Count occluding atoms (protein atoms between view and ligand)
            occlusion_count = 0
            for atom in protein_atoms:
                atom_pos = np.array([atom['x'], atom['y'], atom['z']])
                
                # Check if atom is between viewer and ligand
                to_atom = atom_pos - ligand_center
                to_atom_dist = np.linalg.norm(to_atom)
                
                if to_atom_dist > 0.1:  # Avoid division by zero
                    # Project view direction onto line from ligand to atom
                    projection = np.dot(view_dir, to_atom) / to_atom_dist
                    
                    # If projection is positive and atom is close to line of sight
                    if projection > 0 and to_atom_dist < 15.0:
                        occlusion_count += 1
            
            if occlusion_count < min_occlusion:
                min_occlusion = occlusion_count
                best_angle = (elev, azim)
    
    return best_angle if best_angle else (15, 130)

def create_optimized_docking_visualization(protein_atoms, ligand_atoms):
    """Create optimized docking visualization with clear binding site view"""
    
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Calculate ligand center
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Create protein surface with intelligent filtering
    if protein_atoms:
        # Separate protein atoms by distance from ligand
        near_atoms = []  # 4-10Å (binding pocket)
        far_atoms = []   # 10-20Å (protein surface)
        
        for atom in protein_atoms:
            dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                          (atom['y'] - ligand_center[1])**2 + 
                          (atom['z'] - ligand_center[2])**2)
            if 4.0 <= dist <= 10.0:
                near_atoms.append(atom)
            elif 10.0 < dist <= 20.0:
                far_atoms.append(atom)
        
        # Plot distant protein surface (very sparse, light gray)
        if far_atoms:
            step = max(1, len(far_atoms) // 800)  # Very sparse
            sampled_far = far_atoms[::step]
            
            ax.scatter([atom['x'] for atom in sampled_far], 
                      [atom['y'] for atom in sampled_far], 
                      [atom['z'] for atom in sampled_far],
                      c='lightgray', alpha=0.2, s=15, 
                      label='Protein Surface')
        
        # Plot binding pocket (orange, more prominent)
        if near_atoms:
            step = max(1, len(near_atoms) // 500)  # Moderate density
            sampled_near = near_atoms[::step]
            
            ax.scatter([atom['x'] for atom in sampled_near], 
                      [atom['y'] for atom in sampled_near], 
                      [atom['z'] for atom in sampled_near],
                      c='darkorange', alpha=0.8, s=35, 
                      label='Binding Pocket', marker='s',
                      edgecolor='orange', linewidth=0.5)
    
    # Plot ligand (prominent blue)
    if ligand_atoms:
        ligand_x = [atom['x'] for atom in ligand_atoms]
        ligand_y = [atom['y'] for atom in ligand_atoms]
        ligand_z = [atom['z'] for atom in ligand_atoms]
        
        # Plot ligand atoms
        ax.scatter(ligand_x, ligand_y, ligand_z,
                  c='blue', s=200, alpha=0.95, 
                  label='Ligand', edgecolor='darkblue', linewidth=2,
                  zorder=10)  # High z-order to appear on top
        
        # Add bonds between ligand atoms
        for i, atom1 in enumerate(ligand_atoms):
            for j, atom2 in enumerate(ligand_atoms[i+1:], i+1):
                dist = np.sqrt((atom1['x'] - atom2['x'])**2 + 
                              (atom1['y'] - atom2['y'])**2 + 
                              (atom1['z'] - atom2['z'])**2)
                if dist < 2.0:  # Chemical bond
                    ax.plot([atom1['x'], atom2['x']], 
                           [atom1['y'], atom2['y']], 
                           [atom1['z'], atom2['z']], 
                           color='blue', linewidth=6, alpha=0.9, zorder=10)
    
    # Calculate optimal viewing angle
    elev, azim = calculate_binding_site_exposure(protein_atoms, ligand_atoms)
    print(f"🔍 Optimal viewing angle: elevation={elev}°, azimuth={azim}°")
    
    # Style the plot
    ax.set_facecolor('white')
    ax.grid(False)
    
    # Set optimal viewing angle
    ax.view_init(elev=elev, azim=azim)
    
    # Focus tightly on binding site
    if ligand_atoms:
        range_size = 8  # Smaller range for tighter focus
        ax.set_xlim(ligand_center[0] - range_size, ligand_center[0] + range_size)
        ax.set_ylim(ligand_center[1] - range_size, ligand_center[1] + range_size)
        ax.set_zlim(ligand_center[2] - range_size, ligand_center[2] + range_size)
    
    # Add title and legend
    ax.set_title('Molecular Docking - Binding Site View\n(Optimized angle to show binding pocket)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=12)
    
    # Remove axes for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    
    plt.tight_layout()
    return fig

def create_multiple_angle_visualization(protein_atoms, ligand_atoms):
    """Create visualization with multiple viewing angles"""
    
    fig = plt.figure(figsize=(16, 12))
    
    # Calculate ligand center
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Different viewing angles
    angles = [
        (15, 45, "Front View"),
        (15, 135, "Side View"),
        (15, 225, "Back View"),
        (15, 315, "Side View 2")
    ]
    
    for i, (elev, azim, title) in enumerate(angles):
        ax = fig.add_subplot(2, 2, i+1, projection='3d')
        
        # Plot protein (sparse)
        if protein_atoms:
            step = max(1, len(protein_atoms) // 1000)
            sampled = protein_atoms[::step]
            
            # Filter by distance
            filtered = []
            for atom in sampled:
                dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                              (atom['y'] - ligand_center[1])**2 + 
                              (atom['z'] - ligand_center[2])**2)
                if 4.0 <= dist <= 15.0:
                    filtered.append(atom)
            
            if filtered:
                ax.scatter([atom['x'] for atom in filtered], 
                          [atom['y'] for atom in filtered], 
                          [atom['z'] for atom in filtered],
                          c='lightgray', alpha=0.4, s=10)
        
        # Plot ligand
        if ligand_atoms:
            ligand_x = [atom['x'] for atom in ligand_atoms]
            ligand_y = [atom['y'] for atom in ligand_atoms]
            ligand_z = [atom['z'] for atom in ligand_atoms]
            
            ax.scatter(ligand_x, ligand_y, ligand_z,
                      c='blue', s=100, alpha=0.9, 
                      edgecolor='darkblue', linewidth=1)
        
        # Style
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.view_init(elev=elev, azim=azim)
        
        # Focus on binding site
        if ligand_atoms:
            range_size = 10
            ax.set_xlim(ligand_center[0] - range_size, ligand_center[0] + range_size)
            ax.set_ylim(ligand_center[1] - range_size, ligand_center[1] + range_size)
            ax.set_zlim(ligand_center[2] - range_size, ligand_center[2] + range_size)
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
    
    plt.suptitle('Molecular Docking - Multiple Viewing Angles', fontsize=16, fontweight='bold')
    plt.tight_layout()
    return fig

def main():
    """Main function"""
    
    print("🧬 Creating Optimized Docking Visualization")
    print("=" * 50)
    
    # Parse molecular files
    print("📖 Parsing molecular structures...")
    protein_atoms = parse_pdbqt('../protein_receptor.pdbqt')
    ligand_atoms = parse_pdbqt('docking_results.pdbqt')
    
    print(f"✓ Protein atoms: {len(protein_atoms)}")
    print(f"✓ Ligand atoms: {len(ligand_atoms)}")
    
    # Create optimized single view
    print("\n🎨 Creating optimized binding site visualization...")
    fig1 = create_optimized_docking_visualization(protein_atoms, ligand_atoms)
    fig1.savefig('optimized_docking_view.png', dpi=300, bbox_inches='tight', 
                 facecolor='white', edgecolor='none')
    print("✓ Optimized view saved: optimized_docking_view.png")
    
    # Create multiple angle view
    print("\n🎨 Creating multiple angle visualization...")
    fig2 = create_multiple_angle_visualization(protein_atoms, ligand_atoms)
    fig2.savefig('multiple_angle_docking_view.png', dpi=300, bbox_inches='tight', 
                 facecolor='white', edgecolor='none')
    print("✓ Multiple angles saved: multiple_angle_docking_view.png")
    
    # Show plots
    plt.show()
    
    print("\n✨ Optimization complete!")
    print("📁 Output files:")
    print("  - optimized_docking_view.png (best angle)")
    print("  - multiple_angle_docking_view.png (4 different angles)")
    
    return True

if __name__ == "__main__":
    main()