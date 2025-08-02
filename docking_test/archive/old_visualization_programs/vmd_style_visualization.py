#!/usr/bin/env python3
"""
VMD-style Professional Molecular Visualization
Creates publication-quality molecular graphics similar to VMD/ChimeraX
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial.distance import cdist
from scipy.spatial import ConvexHull
import re

def parse_pdbqt(filename):
    """Parse PDBQT file and extract atom information"""
    atoms = []
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    atom_name = line[12:16].strip()
                    res_name = line[17:20].strip()
                    chain_id = line[21:22].strip()
                    res_num = int(line[22:26].strip())
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    
                    # Extract element
                    element = re.sub(r'[0-9]', '', atom_name)
                    if len(element) > 1:
                        element = element[0]
                    
                    # Van der Waals radius
                    vdw_radii = {
                        'C': 1.7, 'N': 1.55, 'O': 1.52, 'S': 1.8,
                        'P': 1.8, 'H': 1.2, 'F': 1.47, 'Cl': 1.75
                    }
                    
                    atoms.append({
                        'name': atom_name,
                        'element': element,
                        'residue': res_name,
                        'chain': chain_id,
                        'res_num': res_num,
                        'x': x, 'y': y, 'z': z,
                        'vdw_radius': vdw_radii.get(element, 1.5)
                    })
                except (ValueError, IndexError):
                    continue
    
    except FileNotFoundError:
        print(f"⚠ File not found: {filename}")
        return []
    
    return atoms

def create_molecular_surface(atoms, resolution=1.0):
    """Create molecular surface using alpha shapes approximation"""
    
    if not atoms:
        return None
    
    # Extract coordinates and radii
    coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in atoms])
    radii = np.array([atom['vdw_radius'] for atom in atoms])
    
    # Create grid around molecules
    min_coords = coords.min(axis=0) - 5
    max_coords = coords.max(axis=0) + 5
    
    # Create surface points
    surface_points = []
    
    # Simple surface approximation - points at vdw radius
    for i, atom in enumerate(atoms):
        # Create sphere around atom
        phi = np.random.uniform(0, 2*np.pi, 50)
        theta = np.random.uniform(0, np.pi, 50)
        
        radius = atom['vdw_radius'] + 1.4  # Add probe radius
        
        x = atom['x'] + radius * np.sin(theta) * np.cos(phi)
        y = atom['y'] + radius * np.sin(theta) * np.sin(phi)
        z = atom['z'] + radius * np.cos(theta)
        
        # Check if point is not inside other atoms
        for j, other_atom in enumerate(atoms):
            if i != j:
                dist = np.sqrt((x - other_atom['x'])**2 + 
                              (y - other_atom['y'])**2 + 
                              (z - other_atom['z'])**2)
                mask = dist > (other_atom['vdw_radius'] + 1.4)
                x = x[mask]
                y = y[mask]
                z = z[mask]
        
        for k in range(len(x)):
            surface_points.append([x[k], y[k], z[k]])
    
    return np.array(surface_points) if surface_points else None

def create_cartoon_representation(atoms):
    """Create cartoon representation for protein backbone"""
    
    # Extract CA atoms for backbone
    ca_atoms = [atom for atom in atoms if atom['name'] == 'CA']
    
    if len(ca_atoms) < 4:
        return None
    
    # Create smooth backbone curve
    coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in ca_atoms])
    
    # Simple backbone representation
    backbone_lines = []
    for i in range(len(coords) - 1):
        backbone_lines.append([coords[i], coords[i+1]])
    
    return backbone_lines

def create_vmd_style_visualization(protein_atoms, ligand_atoms):
    """Create VMD-style professional visualization"""
    
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Set black background like VMD
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    
    # Calculate ligand center
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Create protein surface
    if protein_atoms:
        print("🔬 Creating protein molecular surface...")
        
        # Get atoms near binding site
        binding_site_atoms = []
        for atom in protein_atoms:
            dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                          (atom['y'] - ligand_center[1])**2 + 
                          (atom['z'] - ligand_center[2])**2)
            if dist < 15.0:
                binding_site_atoms.append(atom)
        
        # Create molecular surface
        if binding_site_atoms:
            surface = create_molecular_surface(binding_site_atoms[:500])  # Limit for performance
            
            if surface is not None:
                # Plot surface with professional coloring
                ax.scatter(surface[:, 0], surface[:, 1], surface[:, 2],
                          c='lightgray', alpha=0.6, s=8,
                          label='Protein Surface')
        
        # Create cartoon representation
        backbone = create_cartoon_representation(binding_site_atoms)
        if backbone:
            for line in backbone:
                ax.plot([line[0][0], line[1][0]], 
                       [line[0][1], line[1][1]], 
                       [line[0][2], line[1][2]], 
                       color='cyan', linewidth=3, alpha=0.8)
    
    # Create ligand representation
    if ligand_atoms:
        print("🔬 Creating ligand ball-and-stick representation...")
        
        # Color by element (CPK colors)
        element_colors = {
            'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D',
            'S': '#FFFF30', 'P': '#FF8000', 'H': '#FFFFFF'
        }
        
        # Plot atoms
        for atom in ligand_atoms:
            color = element_colors.get(atom['element'], '#FF1493')
            ax.scatter(atom['x'], atom['y'], atom['z'],
                      c=color, s=200, alpha=0.9,
                      edgecolor='white', linewidth=1)
        
        # Plot bonds
        coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in ligand_atoms])
        distances = cdist(coords, coords)
        
        for i in range(len(ligand_atoms)):
            for j in range(i+1, len(ligand_atoms)):
                if distances[i, j] < 2.0:  # Bond threshold
                    ax.plot([ligand_atoms[i]['x'], ligand_atoms[j]['x']], 
                           [ligand_atoms[i]['y'], ligand_atoms[j]['y']], 
                           [ligand_atoms[i]['z'], ligand_atoms[j]['z']], 
                           color='white', linewidth=3, alpha=0.8)
    
    # Professional styling
    ax.set_title('Molecular Docking Visualization\n(VMD-style rendering)', 
                 color='white', fontsize=16, fontweight='bold')
    
    # Remove axes and grid
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.grid(False)
    
    # Set viewing angle
    ax.view_init(elev=20, azim=45)
    
    # Focus on binding site
    if ligand_atoms:
        range_size = 12
        ax.set_xlim(ligand_center[0] - range_size, ligand_center[0] + range_size)
        ax.set_ylim(ligand_center[1] - range_size, ligand_center[1] + range_size)
        ax.set_zlim(ligand_center[2] - range_size, ligand_center[2] + range_size)
    
    # Add legend with white text
    legend = ax.legend(loc='upper right', fontsize=12)
    legend.get_frame().set_facecolor('black')
    for text in legend.get_texts():
        text.set_color('white')
    
    plt.tight_layout()
    return fig

def create_publication_quality_plot(protein_atoms, ligand_atoms):
    """Create publication-quality molecular visualization"""
    
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    # White background for publications
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    # Calculate ligand center
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Plot protein with professional styling
    if protein_atoms:
        # Separate by secondary structure (simplified)
        ca_atoms = [atom for atom in protein_atoms if atom['name'] == 'CA']
        other_atoms = [atom for atom in protein_atoms if atom['name'] != 'CA']
        
        # Filter by distance
        nearby_atoms = []
        for atom in other_atoms:
            dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                          (atom['y'] - ligand_center[1])**2 + 
                          (atom['z'] - ligand_center[2])**2)
            if 5.0 < dist < 15.0:
                nearby_atoms.append(atom)
        
        # Plot protein surface
        if nearby_atoms:
            step = max(1, len(nearby_atoms) // 1000)
            sampled = nearby_atoms[::step]
            
            ax.scatter([atom['x'] for atom in sampled],
                      [atom['y'] for atom in sampled],
                      [atom['z'] for atom in sampled],
                      c='lightgray', alpha=0.4, s=15,
                      label='Protein')
        
        # Plot backbone
        if ca_atoms:
            backbone_atoms = [atom for atom in ca_atoms 
                             if np.sqrt((atom['x'] - ligand_center[0])**2 + 
                                       (atom['y'] - ligand_center[1])**2 + 
                                       (atom['z'] - ligand_center[2])**2) < 15.0]
            
            if len(backbone_atoms) > 1:
                coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in backbone_atoms])
                ax.plot(coords[:, 0], coords[:, 1], coords[:, 2],
                       color='blue', linewidth=2, alpha=0.7, label='Backbone')
    
    # Plot ligand with ball-and-stick
    if ligand_atoms:
        element_colors = {
            'C': '#404040', 'N': '#0000FF', 'O': '#FF0000',
            'S': '#FFFF00', 'P': '#FF8000'
        }
        
        # Plot atoms
        for atom in ligand_atoms:
            color = element_colors.get(atom['element'], '#FF1493')
            ax.scatter(atom['x'], atom['y'], atom['z'],
                      c=color, s=150, alpha=0.9,
                      edgecolor='black', linewidth=1)
        
        # Plot bonds
        coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in ligand_atoms])
        distances = cdist(coords, coords)
        
        for i in range(len(ligand_atoms)):
            for j in range(i+1, len(ligand_atoms)):
                if distances[i, j] < 2.0:
                    ax.plot([ligand_atoms[i]['x'], ligand_atoms[j]['x']], 
                           [ligand_atoms[i]['y'], ligand_atoms[j]['y']], 
                           [ligand_atoms[i]['z'], ligand_atoms[j]['z']], 
                           color='gray', linewidth=2, alpha=0.8)
    
    # Publication styling
    ax.set_xlabel('X (Å)', fontsize=12)
    ax.set_ylabel('Y (Å)', fontsize=12)
    ax.set_zlabel('Z (Å)', fontsize=12)
    ax.set_title('Protein-Ligand Binding Site', fontsize=14, fontweight='bold')
    
    # Set optimal viewing angle
    ax.view_init(elev=25, azim=60)
    
    # Focus on binding site
    if ligand_atoms:
        range_size = 10
        ax.set_xlim(ligand_center[0] - range_size, ligand_center[0] + range_size)
        ax.set_ylim(ligand_center[1] - range_size, ligand_center[1] + range_size)
        ax.set_zlim(ligand_center[2] - range_size, ligand_center[2] + range_size)
    
    ax.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    return fig

def main():
    """Main function"""
    
    print("🧬 VMD-Style Professional Molecular Visualization")
    print("=" * 55)
    
    # Parse molecular files
    print("📖 Parsing molecular structures...")
    protein_atoms = parse_pdbqt('../protein_receptor.pdbqt')
    ligand_atoms = parse_pdbqt('docking_results.pdbqt')
    
    print(f"✓ Protein atoms: {len(protein_atoms)}")
    print(f"✓ Ligand atoms: {len(ligand_atoms)}")
    
    # Create VMD-style visualization
    print("\n🎨 Creating VMD-style visualization...")
    fig1 = create_vmd_style_visualization(protein_atoms, ligand_atoms)
    fig1.savefig('vmd_style_visualization.png', dpi=300, bbox_inches='tight',
                 facecolor='black', edgecolor='none')
    print("✓ VMD-style visualization saved: vmd_style_visualization.png")
    
    # Create publication-quality plot
    print("\n📊 Creating publication-quality plot...")
    fig2 = create_publication_quality_plot(protein_atoms, ligand_atoms)
    fig2.savefig('publication_quality_docking.png', dpi=300, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    print("✓ Publication-quality plot saved: publication_quality_docking.png")
    
    # Show plots
    plt.show()
    
    print("\n✨ Professional visualization complete!")
    print("📁 Output files:")
    print("  - vmd_style_visualization.png (VMD-style with black background)")
    print("  - publication_quality_docking.png (publication-ready)")
    
    return True

if __name__ == "__main__":
    main()