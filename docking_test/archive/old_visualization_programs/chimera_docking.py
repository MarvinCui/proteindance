
# ChimeraX script for professional molecular visualization
# Run this script in ChimeraX: chimera --nogui --script chimera_docking.py

# Load protein structure
open ../protein_receptor.pdbqt

# Load ligand
open docking_results.pdbqt

# Style protein
cartoon #1
color #1 lightblue
surface #1
transparency #1 70

# Style ligand
stick #2
color #2 blue

# Set background
set bgColor white

# Position view
view all
turn y 45
turn x 15

# Add labels
label #2 text "Ligand"

# Save high-quality image
save docking_chimera.png supersample 3 width 1200 height 900

# Save session
save docking_session.cxs

quit
