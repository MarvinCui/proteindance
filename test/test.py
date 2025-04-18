from Bio.PDB.alphafold_db import get_predictions

for pred in get_predictions("P00520"):
    # pred 是一个 dict，包含 model_id、pdb_url、pae_url 等
    print(pred)
    print(pred["pdbUrl"])
