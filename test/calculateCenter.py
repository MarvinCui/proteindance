from Bio.PDB import PDBParser
import numpy as np

parser = PDBParser(QUIET=True)
stru = parser.get_structure('pocket', './pocket2_atm.pdb')
coords = np.array([atom.get_coord() for atom in stru.get_atoms()])

# 质心
center = coords.mean(axis=0)
print(f"Center of pocket.pdb →  X={center[0]:.3f},  Y={center[1]:.3f},  Z={center[2]:.3f}")

# （可选）口袋大小：xyz 三个方向的跨度
spans = coords.max(axis=0) - coords.min(axis=0)
print(f"Pocket size (W,H,L) ≈ {spans[0]:.3f}, {spans[1]:.3f}, {spans[2]:.3f}")
