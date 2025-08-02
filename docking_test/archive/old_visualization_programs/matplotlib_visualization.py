#!/usr/bin/env python3
"""
3D Molecular Visualization using matplotlib
Creates static 3D visualizations from PDBQT files
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re
from matplotlib.colors import ListedColormap
import matplotlib.patches as patches

# Element colors (CPK coloring scheme)
ELEMENT_COLORS = {
    'C': '#909090',  # Carbon - gray
    'N': '#3050F8',  # Nitrogen - blue  
    'O': '#FF0D0D',  # Oxygen - red
    'S': '#FFFF30',  # Sulfur - yellow
    'P': '#FF8000',  # Phosphorus - orange
    'H': '#FFFFFF',  # Hydrogen - white
    'F': '#90E050',  # Fluorine - green
    'Cl': '#1FF01F', # Chlorine - green
    'Br': '#A62929', # Bromine - brown
    'I': '#940094',  # Iodine - purple
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
                # Parse PDB/PDBQT format
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

def create_molecular_surface(atoms, center, radius=8.0, resolution=50):
    """Create a molecular surface around atoms"""
    
    # Create a grid around the center
    x_range = np.linspace(center[0] - radius, center[0] + radius, resolution)
    y_range = np.linspace(center[1] - radius, center[1] + radius, resolution)
    z_range = np.linspace(center[2] - radius, center[2] + radius, resolution)
    
    X, Y, Z = np.meshgrid(x_range, y_range, z_range)
    
    # Calculate distance to nearest atom for each grid point
    distances = np.full(X.shape, np.inf)
    
    for atom in atoms:
        atom_distances = np.sqrt((X - atom['x'])**2 + (Y - atom['y'])**2 + (Z - atom['z'])**2)
        distances = np.minimum(distances, atom_distances)
    
    # Create surface where distance is approximately van der Waals radius
    surface_threshold = 3.0  # Approximate van der Waals radius
    surface_mask = (distances > surface_threshold - 0.5) & (distances < surface_threshold + 0.5)
    
    surface_points = []
    for i in range(resolution):
        for j in range(resolution):
            for k in range(resolution):
                if surface_mask[i, j, k]:
                    surface_points.append([X[i, j, k], Y[i, j, k], Z[i, j, k]])
    
    return np.array(surface_points) if surface_points else None

def create_3d_plot(protein_atoms, ligand_atoms, binding_energies=None):
    """Create 3D matplotlib visualization mimicking real docking images"""
    
    fig = plt.figure(figsize=(16, 12))
    
    # Main 3D plot - larger and centered
    ax1 = fig.add_subplot(221, projection='3d')
    
    # Calculate ligand center for focusing
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Plot protein surface (white/gray like in the image)
    if protein_atoms:
        # Sample protein atoms around binding site
        binding_site_atoms = []
        for atom in protein_atoms:
            dist_to_ligand = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                                   (atom['y'] - ligand_center[1])**2 + 
                                   (atom['z'] - ligand_center[2])**2)
            if dist_to_ligand < 15.0:  # Within 15Å of ligand
                binding_site_atoms.append(atom)
        
        if binding_site_atoms:
            # Create protein surface points
            protein_surface = create_molecular_surface(binding_site_atoms, ligand_center, radius=12.0)
            
            if protein_surface is not None:
                ax1.scatter(protein_surface[:, 0], protein_surface[:, 1], protein_surface[:, 2],
                           c='lightgray', alpha=0.6, s=15, label='Protein Surface')
        
        # Plot binding site atoms with orange surface (like in the image)
        binding_site_close = []
        for atom in binding_site_atoms:
            dist_to_ligand = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                                   (atom['y'] - ligand_center[1])**2 + 
                                   (atom['z'] - ligand_center[2])**2)
            if dist_to_ligand < 6.0:  # Very close to ligand
                binding_site_close.append(atom)
        
        if binding_site_close:
            binding_surface = create_molecular_surface(binding_site_close, ligand_center, radius=8.0, resolution=30)
            if binding_surface is not None:
                ax1.scatter(binding_surface[:, 0], binding_surface[:, 1], binding_surface[:, 2],
                           c='orange', alpha=0.7, s=20, label='Binding Site', 
                           marker='s', edgecolor='darkorange', linewidth=0.5)
    
    # Plot ligand atoms with bonds (blue like in the image)
    if ligand_atoms:
        ligand_x = [atom['x'] for atom in ligand_atoms]
        ligand_y = [atom['y'] for atom in ligand_atoms]
        ligand_z = [atom['z'] for atom in ligand_atoms]
        
        # Plot ligand as blue sticks/spheres
        ax1.scatter(ligand_x, ligand_y, ligand_z, 
                   c='blue', s=120, alpha=0.9, label='Ligand', 
                   edgecolor='darkblue', linewidth=1)
        
        # Add bonds between nearby atoms (blue bonds)
        for i, atom1 in enumerate(ligand_atoms):
            for j, atom2 in enumerate(ligand_atoms[i+1:], i+1):
                dist = np.sqrt((atom1['x'] - atom2['x'])**2 + 
                              (atom1['y'] - atom2['y'])**2 + 
                              (atom1['z'] - atom2['z'])**2)
                if dist < 2.0:  # Bond if distance < 2 Angstroms
                    ax1.plot([atom1['x'], atom2['x']], 
                            [atom1['y'], atom2['y']], 
                            [atom1['z'], atom2['z']], 
                            'blue', alpha=0.8, linewidth=4)
    
    # Style the plot to look more professional
    ax1.set_facecolor('white')
    ax1.grid(False)
    ax1.set_xlabel('X (Å)', fontsize=12)
    ax1.set_ylabel('Y (Å)', fontsize=12)
    ax1.set_zlabel('Z (Å)', fontsize=12)
    ax1.set_title('Molecular Docking Visualization\n(Protein Surface + Binding Site + Ligand)', 
                  fontsize=14, fontweight='bold')
    
    # Set view angle similar to the reference image
    ax1.view_init(elev=20, azim=45)
    
    # Focus on binding site
    if ligand_atoms:
        ax1.set_xlim(ligand_center[0] - 10, ligand_center[0] + 10)
        ax1.set_ylim(ligand_center[1] - 10, ligand_center[1] + 10)
        ax1.set_zlim(ligand_center[2] - 10, ligand_center[2] + 10)
    
    ax1.legend(loc='upper right', fontsize=10)
    
    # 2D projection views
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)
    
    # Calculate step for protein sampling
    step = max(1, len(protein_atoms) // 1000) if protein_atoms else 1
    
    # XY projection
    if protein_atoms:
        ax2.scatter([atom['x'] for atom in protein_atoms[::step]], 
                   [atom['y'] for atom in protein_atoms[::step]], 
                   c='lightblue', alpha=0.3, s=10, label='Protein')
    if ligand_atoms:
        ligand_colors = [ELEMENT_COLORS.get(atom['element'], ELEMENT_COLORS['default']) 
                        for atom in ligand_atoms]
        ax2.scatter([atom['x'] for atom in ligand_atoms], 
                   [atom['y'] for atom in ligand_atoms], 
                   c=ligand_colors, s=50, alpha=0.8, label='Ligand')
    ax2.set_xlabel('X (Å)')
    ax2.set_ylabel('Y (Å)')
    ax2.set_title('XY Projection')
    ax2.legend()
    
    # XZ projection
    if protein_atoms:
        ax3.scatter([atom['x'] for atom in protein_atoms[::step]], 
                   [atom['z'] for atom in protein_atoms[::step]], 
                   c='lightblue', alpha=0.3, s=10, label='Protein')
    if ligand_atoms:
        ax3.scatter([atom['x'] for atom in ligand_atoms], 
                   [atom['z'] for atom in ligand_atoms], 
                   c=ligand_colors, s=50, alpha=0.8, label='Ligand')
    ax3.set_xlabel('X (Å)')
    ax3.set_ylabel('Z (Å)')
    ax3.set_title('XZ Projection')
    ax3.legend()
    
    # Element composition or binding energies
    if binding_energies:
        # Plot binding energies
        modes = list(range(1, len(binding_energies) + 1))
        ax4.bar(modes, binding_energies, color='skyblue', alpha=0.7)
        ax4.set_xlabel('Binding Mode')
        ax4.set_ylabel('Binding Energy (kcal/mol)')
        ax4.set_title('Binding Energy Distribution')
        ax4.grid(True, alpha=0.3)
    elif ligand_atoms:
        # Plot element composition
        elements = [atom['element'] for atom in ligand_atoms]
        unique_elements, counts = np.unique(elements, return_counts=True)
        colors = [ELEMENT_COLORS.get(elem, ELEMENT_COLORS['default']) for elem in unique_elements]
        
        ax4.pie(counts, labels=unique_elements, colors=colors, autopct='%1.1f%%')
        ax4.set_title('Ligand Element Composition')
    
    plt.tight_layout()
    return fig

def create_binding_site_analysis():
    """Create binding site analysis visualization"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Read binding energies from the previous analysis
    binding_energies = [-44.8, -44.5, -43.2, -43.2, -43.0, -42.9, -42.8, -42.6, -42.3]
    
    # Binding energy distribution
    ax1 = axes[0, 0]
    modes = list(range(1, len(binding_energies) + 1))
    bars = ax1.bar(modes, binding_energies, color='skyblue', alpha=0.7)
    ax1.set_xlabel('Binding Mode')
    ax1.set_ylabel('Binding Energy (kcal/mol)')
    ax1.set_title('Binding Energy Distribution')
    ax1.grid(True, alpha=0.3)
    
    # Highlight best binding mode
    bars[0].set_color('gold')
    
    # Add value labels on bars
    for i, (bar, energy) in enumerate(zip(bars, binding_energies)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height - 1,
                f'{energy:.1f}', ha='center', va='top', fontweight='bold')
    
    # Energy vs mode scatter plot
    ax2 = axes[0, 1]
    ax2.scatter(modes, binding_energies, c=binding_energies, cmap='viridis', s=100, alpha=0.7)
    ax2.plot(modes, binding_energies, 'k--', alpha=0.5)
    ax2.set_xlabel('Binding Mode')
    ax2.set_ylabel('Binding Energy (kcal/mol)')
    ax2.set_title('Energy vs Binding Mode')
    ax2.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(ax2.collections[0], ax=ax2)
    cbar.set_label('Binding Energy (kcal/mol)')
    
    # Energy statistics
    ax3 = axes[1, 0]
    stats = {
        'Best Energy': min(binding_energies),
        'Mean Energy': np.mean(binding_energies),
        'Std Dev': np.std(binding_energies),
        'Range': max(binding_energies) - min(binding_energies)
    }
    
    y_pos = np.arange(len(stats))
    values = list(stats.values())
    colors = ['gold', 'lightblue', 'lightgreen', 'lightcoral']
    
    bars = ax3.barh(y_pos, values, color=colors, alpha=0.7)
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(stats.keys())
    ax3.set_xlabel('Energy (kcal/mol)')
    ax3.set_title('Binding Energy Statistics')
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, values)):
        width = bar.get_width()
        ax3.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                f'{value:.2f}', ha='left', va='center', fontweight='bold')
    
    # Quality assessment
    ax4 = axes[1, 1]
    
    # Define quality thresholds
    excellent_count = sum(1 for e in binding_energies if e <= -40)
    good_count = sum(1 for e in binding_energies if -40 < e <= -35)
    moderate_count = sum(1 for e in binding_energies if -35 < e <= -30)
    poor_count = sum(1 for e in binding_energies if e > -30)
    
    quality_labels = ['Excellent\n(≤-40)', 'Good\n(-40 to -35)', 'Moderate\n(-35 to -30)', 'Poor\n(>-30)']
    quality_counts = [excellent_count, good_count, moderate_count, poor_count]
    quality_colors = ['gold', 'lightgreen', 'orange', 'lightcoral']
    
    wedges, texts, autotexts = ax4.pie(quality_counts, labels=quality_labels, 
                                       colors=quality_colors, autopct='%1.0f%%')
    ax4.set_title('Binding Quality Assessment')
    
    plt.tight_layout()
    return fig

def create_docking_visualization(protein_atoms, ligand_atoms):
    """Create a single high-quality docking visualization similar to the reference image"""
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Calculate ligand center
    ligand_center = [0, 0, 0]
    if ligand_atoms:
        ligand_center = [
            np.mean([atom['x'] for atom in ligand_atoms]),
            np.mean([atom['y'] for atom in ligand_atoms]),
            np.mean([atom['z'] for atom in ligand_atoms])
        ]
    
    # Create protein surface (white/gray surface like in reference)
    if protein_atoms:
        # Get atoms within binding region
        binding_region_atoms = []
        for atom in protein_atoms:
            dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                          (atom['y'] - ligand_center[1])**2 + 
                          (atom['z'] - ligand_center[2])**2)
            if dist < 20.0:  # Within 20Å of ligand
                binding_region_atoms.append(atom)
        
        # Create dense protein surface
        if binding_region_atoms:
            # Sample more densely for better surface
            step = max(1, len(binding_region_atoms) // 3000)
            sampled_atoms = binding_region_atoms[::step]
            
            protein_x = [atom['x'] for atom in sampled_atoms]
            protein_y = [atom['y'] for atom in sampled_atoms]
            protein_z = [atom['z'] for atom in sampled_atoms]
            
            # Create protein surface with white/light gray color
            ax.scatter(protein_x, protein_y, protein_z,
                      c='lightgray', alpha=0.4, s=30, 
                      label='Protein Surface')
        
        # Create binding pocket surface (orange like in reference)
        binding_pocket_atoms = []
        for atom in binding_region_atoms:
            dist = np.sqrt((atom['x'] - ligand_center[0])**2 + 
                          (atom['y'] - ligand_center[1])**2 + 
                          (atom['z'] - ligand_center[2])**2)
            if dist < 8.0:  # Very close to ligand (binding pocket)
                binding_pocket_atoms.append(atom)
        
        if binding_pocket_atoms:
            # Create binding pocket surface with orange color
            pocket_x = [atom['x'] for atom in binding_pocket_atoms]
            pocket_y = [atom['y'] for atom in binding_pocket_atoms]
            pocket_z = [atom['z'] for atom in binding_pocket_atoms]
            
            ax.scatter(pocket_x, pocket_y, pocket_z,
                      c='orange', alpha=0.8, s=25, 
                      label='Binding Pocket', marker='s')
    
    # Plot ligand (blue like in reference)
    if ligand_atoms:
        ligand_x = [atom['x'] for atom in ligand_atoms]
        ligand_y = [atom['y'] for atom in ligand_atoms]
        ligand_z = [atom['z'] for atom in ligand_atoms]
        
        # Plot ligand atoms as blue spheres
        ax.scatter(ligand_x, ligand_y, ligand_z,
                  c='blue', s=150, alpha=0.9, 
                  label='Ligand', edgecolor='darkblue', linewidth=2)
        
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
                           color='blue', linewidth=5, alpha=0.8)
    
    # Style the plot to match reference image
    ax.set_facecolor('white')
    ax.grid(False)
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_zlabel('')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    
    # Set viewing angle similar to reference
    ax.view_init(elev=15, azim=130)
    
    # Focus on binding site
    if ligand_atoms:
        range_size = 12
        ax.set_xlim(ligand_center[0] - range_size, ligand_center[0] + range_size)
        ax.set_ylim(ligand_center[1] - range_size, ligand_center[1] + range_size)
        ax.set_zlim(ligand_center[2] - range_size, ligand_center[2] + range_size)
    
    # Remove axes for cleaner look
    ax.set_axis_off()
    
    plt.tight_layout()
    return fig

def main():
    """Main function to create all visualizations"""
    
    print("🧬 Creating matplotlib 3D Molecular Visualization")
    print("=" * 50)
    
    # Parse molecular files
    print("📖 Parsing molecular structures...")
    protein_atoms = parse_pdbqt('../protein_receptor.pdbqt')
    ligand_atoms = parse_pdbqt('docking_results.pdbqt')
    
    print(f"✓ Protein atoms: {len(protein_atoms)}")
    print(f"✓ Ligand atoms: {len(ligand_atoms)}")
    
    # Create reference-style docking visualization
    print("\n🎨 Creating reference-style docking visualization...")
    fig_docking = create_docking_visualization(protein_atoms, ligand_atoms)
    fig_docking.savefig('docking_visualization_reference_style.png', dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
    print("✓ Reference-style docking visualization saved: docking_visualization_reference_style.png")
    
    # Create 3D molecular visualization
    print("\n🎨 Creating comprehensive 3D molecular plot...")
    binding_energies = [-44.8, -44.5, -43.2, -43.2, -43.0, -42.9, -42.8, -42.6, -42.3]
    
    fig1 = create_3d_plot(protein_atoms, ligand_atoms, binding_energies)
    fig1.savefig('matplotlib_3d_visualization.png', dpi=300, bbox_inches='tight')
    print("✓ 3D visualization saved: matplotlib_3d_visualization.png")
    
    # Create binding site analysis
    print("\n📊 Creating binding site analysis...")
    fig2 = create_binding_site_analysis()
    fig2.savefig('binding_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Binding analysis saved: binding_analysis.png")
    
    # Show plots
    plt.show()
    
    print("\n✨ Visualization complete!")
    print("📁 Output files:")
    print("  - docking_visualization_reference_style.png (main result)")
    print("  - matplotlib_3d_visualization.png")
    print("  - binding_analysis.png")
    
    # Element summary
    if ligand_atoms:
        elements = [atom['element'] for atom in ligand_atoms]
        unique_elements, counts = np.unique(elements, return_counts=True)
        print(f"\n🧪 Ligand composition:")
        for elem, count in zip(unique_elements, counts):
            print(f"  {elem}: {count} atoms")
    
    return True

if __name__ == "__main__":
    main()