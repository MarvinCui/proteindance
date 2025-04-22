from typing import List, Tuple
import os
from chembl_webresource_client.new_client import new_client
from rdkit import Chem
from rdkit.Chem import AllChem
from openbabel import pybel
from vina import Vina


def fetch_chembl_smiles(uniprot_acc: str, max_hits: int = 10) -> List[str]:
    """
    通过 ChEMBL REST API 拉取该 UniProt 蛋白的 IC50 抑制化合物 SMILES。
    """
    target = new_client.target
    res = target.filter(target_components__accession=uniprot_acc).only(["target_chembl_id"])
    if not res:
        print(f"⚠ ChEMBL 中未找到 UniProt {uniprot_acc} 对应的 target，跳过。")
        return []
    chembl_id = res[0]["target_chembl_id"]
    print(f"ChEMBL Target ID: {chembl_id}")

    activity = new_client.activity.filter(
        target_chembl_id=chembl_id,
        standard_type="IC50"
    ).only([
        "molecule_chembl_id",
        "canonical_smiles",
        "standard_value"
    ]).order_by("standard_value")[: max_hits]

    smiles = []
    for act in activity:
        smi = act.get("canonical_smiles")
        if smi:
            smiles.append(smi)
    # 去重且保留顺序
    smiles = list(dict.fromkeys(smiles))
    print(f"自动获取到 {len(smiles)} 条 SMILES")
    return smiles


def prepare_receptor(pdb_path: str, receptor_pdbqt: str) -> None:
    """
    使用 OpenBabel(pybel) 将 PDB 转为 PDBQT，供 Vina 使用。
    """
    mol = next(pybel.readfile("pdb", pdb_path))
    mol.addh()  # 加氢
    mol.write("pdbqt", receptor_pdbqt, overwrite=True)
    print(f"Receptor prepared: {receptor_pdbqt}")


def prepare_ligand(smi: str, ligand_pdbqt: str) -> bool:
    """
    用 RDKit 生成 3D 结构，并用 OpenBabel 转为 PDBQT。
    返回 True 表示成功。
    """
    # 1. RDKit 从 SMILES 生成分子并加氢
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return False
    m = Chem.AddHs(m)
    # 2. 生成 3D 构象
    if AllChem.EmbedMolecule(m, AllChem.ETKDG()) != 0:
        return False
    AllChem.UFFOptimizeMolecule(m)
    # 3. 写出为临时 PDB，然后用 pybel 转为 PDBQT
    tmp_pdb = ligand_pdbqt.replace(".pdbqt", ".pdb")
    with open(tmp_pdb, "w") as f:
        f.write(Chem.MolToPDBBlock(m))
    mol = next(pybel.readfile("pdb", tmp_pdb))
    mol.addh()
    mol.write("pdbqt", ligand_pdbqt, overwrite=True)
    os.remove(tmp_pdb)
    return True


def dock_smiles_to_pocket(
        pdb_pocket_file: str,
        uniprot_acc: str,
        max_hits: int = 10,
        exhaustiveness: int = 8,
        center: Tuple[float, float, float] = (0, 0, 0),
        box_size: Tuple[float, float, float] = (20, 20, 20),
) -> List[Tuple[str, float]]:
    """
    整合上述步骤：读取口袋 PDB、抓取 SMILES、制备文件、执行 docking，
    返回 (SMILES, docking_score) 列表，按分数（自由能，越小越好）升序排序。
    """
    # 1) 准备 receptor
    receptor_pdbqt = "receptor.pdbqt"
    prepare_receptor(pdb_pocket_file, receptor_pdbqt)

    # 2) 获取 SMILES
    smiles_list = fetch_chembl_smiles(uniprot_acc, max_hits=max_hits)
    if not smiles_list:
        return []

    # 3) 逐个配体 docking
    results = []
    v = Vina(sf_name='vina')
    v.set_receptor(receptor_pdbqt)
    v.compute_vina_maps(center=center, box_size=box_size)
    v.configuration(exhaustiveness=exhaustiveness)

    for idx, smi in enumerate(smiles_list, start=1):
        ligand_pdbqt = f"ligand_{idx}.pdbqt"
        ok = prepare_ligand(smi, ligand_pdbqt)
        if not ok:
            print(f"⚠ 无法制备配体 {smi}, 跳过。")
            continue

        v.set_ligand_from_file(ligand_pdbqt)
        score = v.dock()[0]  # 返回最优打分
        results.append((smi, score))
        print(f"[{idx}/{len(smiles_list)}] SMILES: {smi} -> Score: {score:.2f}")

        # 清理
        os.remove(ligand_pdbqt)

    # 按分数排序并返回
    results.sort(key=lambda x: x[1])
    return results


if __name__ == "__main__":
    # 使用示例
    pocket_file = "./pocket2_atm.pdb"  # 你的口袋文件
    uniprot = "P12345"  # 你的 UniProt Accession
    hits = dock_smiles_to_pocket(
        pdb_pocket_file=pocket_file,
        uniprot_acc=uniprot,
        max_hits=20,
        exhaustiveness=16,
        center=(10.513, 1.720, -8.182),  # 根据实际 pocket 调整
        box_size=(19.554, 10.345, 11.423)
    )
    print("Top hits (SMILES, score):")
    for smi, sc in hits[:5]:
        print(f"  {smi}  =>  {sc:.2f}")
