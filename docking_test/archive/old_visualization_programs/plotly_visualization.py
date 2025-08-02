#!/usr/bin/env python3
"""
Interactive 3D Molecular Visualization using Plotly
Creates interactive web-based 3D visualizations
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import re

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

def create_3d_molecular_plot(protein_atoms, ligand_atoms):
    """Create interactive 3D molecular visualization"""
    
    fig = go.Figure()
    
    # Add protein atoms
    if protein_atoms:
        # Sample protein atoms for better performance
        step = max(1, len(protein_atoms) // 2000)  # Show max 2000 atoms
        sampled_protein = protein_atoms[::step]
        
        protein_x = [atom['x'] for atom in sampled_protein]
        protein_y = [atom['y'] for atom in sampled_protein]
        protein_z = [atom['z'] for atom in sampled_protein]
        protein_text = [f"Protein {atom['name']}<br>({atom['x']:.2f}, {atom['y']:.2f}, {atom['z']:.2f})" 
                       for atom in sampled_protein]
        
        fig.add_trace(go.Scatter3d(
            x=protein_x,
            y=protein_y,
            z=protein_z,
            mode='markers',
            marker=dict(
                size=3,
                color='lightblue',
                opacity=0.4
            ),
            text=protein_text,
            hoverinfo='text',
            name='Protein'
        ))
    
    # Add ligand atoms
    if ligand_atoms:
        ligand_x = [atom['x'] for atom in ligand_atoms]
        ligand_y = [atom['y'] for atom in ligand_atoms]
        ligand_z = [atom['z'] for atom in ligand_atoms]
        ligand_colors = [ELEMENT_COLORS.get(atom['element'], ELEMENT_COLORS['default']) 
                        for atom in ligand_atoms]
        ligand_text = [f"Ligand {atom['name']} ({atom['element']})<br>({atom['x']:.2f}, {atom['y']:.2f}, {atom['z']:.2f})" 
                      for atom in ligand_atoms]
        
        fig.add_trace(go.Scatter3d(
            x=ligand_x,
            y=ligand_y,
            z=ligand_z,
            mode='markers',
            marker=dict(
                size=8,
                color=ligand_colors,
                opacity=0.8,
                line=dict(width=1, color='black')
            ),
            text=ligand_text,
            hoverinfo='text',
            name='Ligand'
        ))
        
        # Add bonds between nearby ligand atoms
        bond_x, bond_y, bond_z = [], [], []
        for i, atom1 in enumerate(ligand_atoms):
            for j, atom2 in enumerate(ligand_atoms[i+1:], i+1):
                dist = np.sqrt((atom1['x'] - atom2['x'])**2 + 
                              (atom1['y'] - atom2['y'])**2 + 
                              (atom1['z'] - atom2['z'])**2)
                if dist < 2.0:  # Bond if distance < 2 Angstroms
                    bond_x.extend([atom1['x'], atom2['x'], None])
                    bond_y.extend([atom1['y'], atom2['y'], None])
                    bond_z.extend([atom1['z'], atom2['z'], None])
        
        if bond_x:
            fig.add_trace(go.Scatter3d(
                x=bond_x,
                y=bond_y,
                z=bond_z,
                mode='lines',
                line=dict(color='gray', width=4),
                hoverinfo='skip',
                showlegend=False,
                name='Bonds'
            ))
    
    # Update layout
    fig.update_layout(
        title='Interactive 3D Molecular Structure',
        scene=dict(
            xaxis_title='X (Å)',
            yaxis_title='Y (Å)',
            zaxis_title='Z (Å)',
            bgcolor='white',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        showlegend=True,
        width=800,
        height=600
    )
    
    return fig

def create_binding_analysis_dashboard():
    """Create comprehensive binding analysis dashboard"""
    
    # Sample binding data
    binding_data = {
        'Mode': list(range(1, 10)),
        'Binding_Energy': [-44.8, -44.5, -43.2, -43.2, -43.0, -42.9, -42.8, -42.6, -42.3],
        'RMSD': [0.0, 1.2, 2.1, 2.3, 2.8, 3.1, 3.5, 3.9, 4.2],
        'Quality': ['Excellent', 'Excellent', 'Good', 'Good', 'Good', 'Good', 'Good', 'Good', 'Good']
    }
    
    df = pd.DataFrame(binding_data)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Binding Energy Distribution', 'Energy vs RMSD', 
                       'Quality Assessment', 'Binding Mode Analysis'),
        specs=[[{'type': 'bar'}, {'type': 'scatter'}],
               [{'type': 'pie'}, {'type': 'scatter'}]]
    )
    
    # 1. Binding Energy Distribution
    colors = ['gold' if i == 0 else 'lightblue' for i in range(len(df))]
    fig.add_trace(
        go.Bar(
            x=df['Mode'],
            y=df['Binding_Energy'],
            marker_color=colors,
            text=[f'{e:.1f}' for e in df['Binding_Energy']],
            textposition='outside',
            name='Binding Energy'
        ),
        row=1, col=1
    )
    
    # 2. Energy vs RMSD
    fig.add_trace(
        go.Scatter(
            x=df['RMSD'],
            y=df['Binding_Energy'],
            mode='markers+lines',
            marker=dict(
                size=10,
                color=df['Binding_Energy'],
                colorscale='Viridis',
                showscale=False
            ),
            text=[f'Mode {m}' for m in df['Mode']],
            name='Energy vs RMSD'
        ),
        row=1, col=2
    )
    
    # 3. Quality Assessment
    quality_counts = df['Quality'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=quality_counts.index,
            values=quality_counts.values,
            marker_colors=['gold', 'lightgreen'],
            name='Quality'
        ),
        row=2, col=1
    )
    
    # 4. Binding Mode Analysis
    fig.add_trace(
        go.Scatter(
            x=df['Mode'],
            y=df['Binding_Energy'],
            mode='markers+lines',
            marker=dict(
                size=12,
                color=df['Binding_Energy'],
                colorscale='RdYlBu_r',
                showscale=True,
                colorbar=dict(title='Binding Energy (kcal/mol)')
            ),
            line=dict(dash='dash'),
            name='Mode Analysis'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text='Molecular Docking Analysis Dashboard',
        showlegend=False,
        height=700
    )
    
    # Update axes
    fig.update_xaxes(title_text="Binding Mode", row=1, col=1)
    fig.update_yaxes(title_text="Binding Energy (kcal/mol)", row=1, col=1)
    fig.update_xaxes(title_text="RMSD (Å)", row=1, col=2)
    fig.update_yaxes(title_text="Binding Energy (kcal/mol)", row=1, col=2)
    fig.update_xaxes(title_text="Binding Mode", row=2, col=2)
    fig.update_yaxes(title_text="Binding Energy (kcal/mol)", row=2, col=2)
    
    return fig

def create_element_analysis(ligand_atoms):
    """Create element composition analysis"""
    
    if not ligand_atoms:
        return None
    
    # Count elements
    elements = [atom['element'] for atom in ligand_atoms]
    element_counts = pd.Series(elements).value_counts()
    
    # Create sunburst chart
    fig = go.Figure(go.Sunburst(
        labels=element_counts.index,
        values=element_counts.values,
        parents=[""] * len(element_counts),
        marker=dict(
            colors=[ELEMENT_COLORS.get(elem, ELEMENT_COLORS['default']) 
                   for elem in element_counts.index]
        )
    ))
    
    fig.update_layout(
        title="Ligand Element Composition",
        width=400,
        height=400
    )
    
    return fig

def main():
    """Main function to create all Plotly visualizations"""
    
    print("🧬 Creating Plotly Interactive Molecular Visualization")
    print("=" * 50)
    
    # Parse molecular files
    print("📖 Parsing molecular structures...")
    protein_atoms = parse_pdbqt('../protein_receptor.pdbqt')
    ligand_atoms = parse_pdbqt('docking_results.pdbqt')
    
    print(f"✓ Protein atoms: {len(protein_atoms)}")
    print(f"✓ Ligand atoms: {len(ligand_atoms)}")
    
    # Create 3D molecular visualization
    print("\n🎨 Creating 3D molecular plot...")
    fig1 = create_3d_molecular_plot(protein_atoms, ligand_atoms)
    fig1.write_html('plotly_3d_molecular.html')
    print("✓ 3D molecular plot saved: plotly_3d_molecular.html")
    
    # Create binding analysis dashboard
    print("\n📊 Creating binding analysis dashboard...")
    fig2 = create_binding_analysis_dashboard()
    fig2.write_html('plotly_binding_dashboard.html')
    print("✓ Binding dashboard saved: plotly_binding_dashboard.html")
    
    # Create element analysis
    print("\n🧪 Creating element analysis...")
    fig3 = create_element_analysis(ligand_atoms)
    if fig3:
        fig3.write_html('plotly_element_analysis.html')
        print("✓ Element analysis saved: plotly_element_analysis.html")
    
    print("\n✨ Plotly visualizations complete!")
    print("📁 Output files:")
    print("  - plotly_3d_molecular.html (3D molecular structure)")
    print("  - plotly_binding_dashboard.html (binding analysis)")
    print("  - plotly_element_analysis.html (element composition)")
    
    print("\n🌐 To view:")
    print("  Open any HTML file in a web browser for interactive visualization")
    print("  Features:")
    print("    - Pan, zoom, rotate with mouse")
    print("    - Hover for atom details")
    print("    - Toggle traces on/off")
    print("    - Download as PNG")
    
    # Show statistics
    if ligand_atoms:
        elements = [atom['element'] for atom in ligand_atoms]
        unique_elements = set(elements)
        print(f"\n🧪 Ligand contains {len(unique_elements)} different elements:")
        for elem in sorted(unique_elements):
            count = elements.count(elem)
            print(f"  {elem}: {count} atoms")
    
    return True

if __name__ == "__main__":
    main()