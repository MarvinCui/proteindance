# PyMOL Visualization Script
# Load receptor structure
load protein_receptor.pdbqt, receptor

# Load docking results
load ./docking_results/docking_results.pdbqt, docking_results

# Display receptor as cartoon
show cartoon, receptor
color lightblue, receptor

# Display ligand as sticks
show sticks, docking_results
color by_element, docking_results

# Set background to white
bg_color white

# Show binding site surface
select binding_site, receptor within 5 of docking_results
show surface, binding_site
set transparency, 0.3, binding_site
color yellow, binding_site

# Adjust view
center docking_results
zoom docking_results, 10

# Show hydrogen bonds
distance hbonds, receptor, docking_results, 3.5, mode=2
hide labels, hbonds

# Add binding center marker
pseudoatom center, pos=[-0.45, 34.90, 3.59]
show spheres, center
color red, center

# Save session
save docking_session.pse
