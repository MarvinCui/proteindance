#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

disease_to_drug.py

------------------

交互式一键流程：

1) 读取疾病名称 → DeepSeek Chat API 查询潜在蛋白靶点

2) UniProt / PDB / AlphaFold 结构检索 & 下载

3) 口袋预测（本地 P2Rank / 云端 PrankWeb / DoGSiteScorer）

4) 获取候选化合物SMILES

5) 保存所有文件以便后续对接

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

★ 默认路径全部纯 Python + Requests 可直接运行；

★ 需要Brew安装OpenBable，Java17+；

> brew install open-babel

★ 云端接口函数已留出 (TODO) 位置，按注释填参数即可启用。

★ 需要Conda安装MGLTools

★ 在这里安装 AutoDock Vina：https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.7

"""

from __future__ import annotations

import os, sys, json, time, textwrap, subprocess, tempfile, shutil, stat

from pathlib import Path

from typing import List, Dict

import requests

from bs4 import BeautifulSoup

import time

import pandas as pd

import requests

import time

import tarfile

import io

import re

from pathlib import Path

from typing import Tuple

from shutil import which

from rdkit import Chem

from rdkit.Chem import AllChem, Draw

from chembl_webresource_client.new_client import new_client

from Bio.PDB import PDBList

import re

import openai
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)             # pip install openai>=1.2.4

# ------------------------------------------------------------------

# 全局配置

# ------------------------------------------------------------------

# 在每次运行前清理临时目录，防止历史数据污染
TMP_DIR = Path(tempfile.gettempdir()) / "drug_flow"
if TMP_DIR.exists():
    shutil.rmtree(TMP_DIR)
TMP_DIR.mkdir(parents=True, exist_ok=True)


OPENAI_API_BASE = "https://api.siliconflow.cn/v1"   # DeepSeek Chat 兼容 OpenAI

OPENAI_API_KEY  = "sk-kiuwnsdtlpclsjguvgajhuqdgowypqhmgozbxhhnenucutdp"      # TODO: ←← 在此填入 DeepSeek API Key

TMP_DIR = Path(tempfile.gettempdir()) / "drug_flow"

TMP_DIR.mkdir(exist_ok=True)

# TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(base_url=OPENAI_API_BASE)'
# openai.api_base = OPENAI_API_BASE


HEADERS_JSON = {"Content-Type": "application/json"}

UNIPROT_REST = "https://rest.uniprot.org"

# ------------------------------------------------------------------

# 工具函数

# ------------------------------------------------------------------

def banner(msg: str):

    print(f"\n{'='*10} {msg} {'='*10}")

def choose(items: List[str], prompt: str) -> int:

    """打印列表并让用户选择编号（从 1 开始）。"""

    for i, it in enumerate(items, 1):

        print(f"{i:2d}. {it}")

    while True:

        sel = input(prompt).strip()

        if sel.isdigit() and 1 <= int(sel) <= len(items):

            return int(sel) - 1

        print("输入无效，请重新输入编号！")

# ------------------------------------------------------------------

# 1. DeepSeek Chat 获得疾病→蛋白靶点

# ------------------------------------------------------------------

def get_targets_from_deepseek(disease_chinese: str, top_k=10) -> List[str]:

    """调用 DeepSeek Chat，返回蛋白候选名列表。"""

    prompt = f"列举与{disease_chinese}相关、可作为药物靶点的蛋白基因符号（仅返回{top_k}个以内，不要解释）。"

    rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
    
    messages=[{"role": "user", "content": prompt}],
    
    temperature=0.2)

    text = rsp.choices[0].message.content

    # 粗略解析：去掉序号等，仅提取字母/数字/下划线

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    proteins = []

    for l in lines:

        # 只保留 A-Z, a-z, 0-9, _ 及 -，去掉其它符号（逗号、句号等）

        token = re.sub(r"[^A-Za-z0-9_-]", "", l.split()[0])

        if 2 <= len(token) <= 12:

            proteins.append(token.upper())

    return proteins[:top_k]

# ------------------------------------------------------------------

# 2. UniProt → 获取 Accession + 结构条目

# ------------------------------------------------------------------

def search_uniprot(gene_symbol: str, organism_id="9606") -> List[Dict]:

    """返回 [{'acc': 'P31645', 'name': 'Sodium‑dependent serotonin transporter'}, ...]"""

    url = (UNIPROT_REST +

           f"/uniprotkb/search?query=(gene_exact:{gene_symbol}+AND+organism_id:{organism_id})"

           "&fields=accession,protein_name&format=json&size=10")

    res = requests.get(url, timeout=30)

    res.raise_for_status()

    data = res.json().get("results", [])

    hits = []

    for d in res.json().get("results", []):

        acc = d["primaryAccession"]

        desc = d.get("proteinDescription", {})

        if "recommendedName" in desc:

            name = desc["recommendedName"]["fullName"]["value"]

        elif "submissionNames" in desc and desc["submissionNames"]:

            name = desc["submissionNames"][0]["fullName"]["value"]

        elif "alternativeNames" in desc and desc["alternativeNames"]:

            name = desc["alternativeNames"][0]["fullName"]["value"]

        else:

            name = "(no name)"

        hits.append({"acc": acc, "name": name})

    return hits

def get_pdb_ids_for_uniprot(accession: str, max_ids=10) -> List[str]:

    """使用 RCSB Search API 通过 UniProtID 找 PDB 代码。"""

    query = {

        "query": {

            "type": "terminal",

            "service": "text",

            "parameters": {

                "attribute":

                    "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",

                "operator": "exact_match",

                "value": accession,

            },

        },

        "return_type": "entry",

        "request_options": {"return_all_hits": True},

    }

    url = "https://search.rcsb.org/rcsbsearch/v2/query"

    res = requests.post(url, headers=HEADERS_JSON, data=json.dumps(query), timeout=30)

    res.raise_for_status()

    ids = [it["identifier"] for it in res.json().get("result_set", [])]

    return ids[:max_ids]

def download_pdb(pdb_id: str, dest_dir=TMP_DIR) -> Path:

    pdb_list = PDBList()

    fname = pdb_list.retrieve_pdb_file(pdb_id, file_format="pdb", pdir=str(dest_dir))

    # Biopython 会存 gz → 解压

    if fname.endswith(".gz"):

        import gzip, shutil as sh

        out = dest_dir / f"{pdb_id}.pdb"

        with gzip.open(fname, "rb") as fin, open(out, "wb") as fout:

            sh.copyfileobj(fin, fout)

        return out

    return Path(fname)

def download_alphafold(uniprot_acc: str, dest_dir=TMP_DIR) -> Path | None:

    """AlphaFold DB 预测结构 v4，如果存在返回路径；否则返回 None。"""

    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_acc}-F1-model_v4.pdb"

    out = dest_dir / f"{uniprot_acc}_AF.pdb"

    r = requests.get(url, stream=True)

    if r.status_code == 200 and int(r.headers.get("Content-Length", 0)) > 1000:

        with open(out, "wb") as f:

            for chunk in r.iter_content(8192):

                f.write(chunk)

        return out

    return None

def get_pdb_ids_for_gene(gene_symbol: str, max_ids=10):

    query = {

        "query": {

            "type":"terminal","service":"text",

            "parameters":{"value":gene_symbol,"attribute":"rcsb_entity_source_organism.ncbi_gene_name.value"}

        },

        "return_type":"entry","request_options":{"return_all_hits":True}

    }

    res = requests.post("https://search.rcsb.org/rcsbsearch/v2/query",

                        headers=HEADERS_JSON, data=json.dumps(query), timeout=30)

    res.raise_for_status()

    return [x["identifier"] for x in res.json().get("result_set", [])][:max_ids]

# ------------------------------------------------------------------

# 3. 口袋预测（默认本地 P2Rank；可选云端 PrankWeb）

# ------------------------------------------------------------------

from shutil import which

import pandas as pd

import subprocess

import os

from pathlib import Path

from typing import List, Dict

def run_p2rank(pdb_path: Path, prank_bin: str | None = None) -> List[Dict]:

    """

调用 P2Rank >=2.4 二进制 prank 预测口袋。

支持：

1. candidates 列表中自动查找项目目录下的 p2rank/prank 或用户主目录下的 p2rank/prank

2. $P2RANK_BIN 环境变量

3. PATH 中 which("prank")

4. prank_bin 参数

返回 [{'center': (x,y,z), 'score': s}, ...]，按 score 降序。

"""

    banner("P2Rank 口袋预测")

    # 1) 优先在项目目录或 HOME 下找 p2rank/prank

    candidates = [Path.cwd() / "p2rank/prank", Path.home() / "p2rank/prank"]

    bin_path = None

    for c in candidates:

        if c.exists() and c.is_file():

            bin_path = c

            break

    # 2) 再试环境变量

    if not bin_path:

        env = os.getenv("P2RANK_BIN")

        if env and Path(env).exists():

            bin_path = Path(env)

    # 3) 再试 which

    if not bin_path:

        w = which("prank")

        if w:

            bin_path = Path(w)

    # 4) 最后用传入的 prank_bin

    if not bin_path and prank_bin:

        cand = Path(prank_bin).expanduser()

        if cand.exists():

            bin_path = cand

    if not bin_path:

        raise FileNotFoundError(

            f"未找到 P2Rank 可执行文件。候选路径：{candidates}，"

            "环境变量 P2RANK_BIN，或 PATH 中的 prank。"

        )

    # 5) 执行预测

    out_dir = TMP_DIR / f"{pdb_path.stem}_p2rank"

    cmd = [str(bin_path), "predict", "-f", str(pdb_path), "-o", str(out_dir)]

    print("▶", " ".join(cmd))

    subprocess.run(cmd, check=True)

    # 6) 读取 CSV 并规范化列名

    csv_file = next(out_dir.glob("*_predictions.csv"))

    df = pd.read_csv(csv_file)

    df.columns = (

        df.columns

        .str.strip()

        .str.replace(r"\s+", "_", regex=True)

        .str.lower()

    )

    # 7) 提取 pockets

    pockets: List[Dict] = []

    for _, row in df.iterrows():

        x = row["center_x"]

        y = row["center_y"]

        z = row["center_z"]

        # 有些版本列名叫 score，有些叫 ligandability_score

        score = row.get("score", row.get("ligandability_score"))

        pockets.append({"center": (float(x), float(y), float(z)),

                        "score": float(score)})

    # 8) 返回按 score 降序

    return sorted(pockets, key=lambda p: p["score"], reverse=True)

def run_dogsite_api(pdb_path: Path) -> List[Dict]:

    """

调 ProteinsPlus REST，返回 [{'center': (x,y,z), 'score': druggability}, ...]

文档: https://proteins.plus/api/v2/docs

"""

    banner("ProteinsPlus DoGSiteScorer 在线口袋预测")

    url_job = "https://proteins.plus/api/v2/dogsite/start/"

    files = {"file": open(pdb_path, "rb")}

    r = requests.post(url_job, files=files, timeout=60)

    r.raise_for_status()

    job_id = r.json()["job_id"]

    # 轮询

    url_stat = f"https://proteins.plus/api/v2/dogsite/status/{job_id}/"

    url_res  = f"https://proteins.plus/api/v2/dogsite/result/{job_id}/"

    for _ in range(60):

        time.sleep(5)

        if requests.get(url_stat).json()["status"] == "FINISHED":

            data = requests.get(url_res).json()

            pockets = []

            for p in data["pockets"]:

                x, y, z = p["center"]

                pockets.append({"center": (x, y, z),

                                "score": p["druggability_score"]})

            # 分数高→更可成药；排序后返回

            return sorted(pockets, key=lambda x: x["score"], reverse=True)

    raise RuntimeError("DoGSite 预测超时")

# ------------------------------------------------------------------

# 4. 虚拟筛选（获取SMILES部分）

# ------------------------------------------------------------------

def fetch_chembl_smiles(uniprot_acc: str, max_hits: int = 10) -> List[str]:

    """

通过 ChEMBL REST API 拉取该 UniProt 蛋白的 IC50 抑制化合物 SMILES。

"""

    # 1) 根据 UniProt Accession 找对应的 ChEMBL Target ID

    target = new_client.target

    res = target.filter(target_components__accession=uniprot_acc).only(

        ["target_chembl_id"]

    )

    if not res:

        print(f"⚠ ChEMBL 中未找到 UniProt {uniprot_acc} 对应的 target，跳过。")

        return []

    chembl_id = res[0]["target_chembl_id"]

    print(f"ChEMBL Target ID: {chembl_id}")

    # 2) 拉活性数据，取前 max_hits 条 IC50

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

    smiles = list(dict.fromkeys(smiles))  # 去重，保顺序

    print(f"自动获取到 {len(smiles)} 条 SMILES")

    return smiles

def smiles_to_pdbqt(smiles: str, name="lig") -> Path:

    """RDKit SMILES → 3D 结构 → PDBQT (用 openbabel obabel 命令)."""

    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))

    AllChem.EmbedMolecule(mol, AllChem.ETKDG())

    AllChem.UFFOptimizeMolecule(mol)

    sdf = TMP_DIR / f"{name}.sdf"

    Chem.MolToMolFile(mol, str(sdf))

    pdbqt = TMP_DIR / f"{name}.pdbqt"

    subprocess.run(["obabel", str(sdf), "-O", str(pdbqt)], check=True)

    return pdbqt

# ------------------------------------------------------------------

# 主流程

# ------------------------------------------------------------------

def main():

    banner("疾病 → 蛋白靶点自动化工作流")

    disease = input("请输入疾病名称（中文）：").strip()

    # 1. DeepSeek 查询

    banner("调用 DeepSeek 获取蛋白列表")

    proteins = get_targets_from_deepseek(disease)

    idx = choose(proteins, "请选择蛋白编号：")

    gene_symbol = proteins[idx]

    print(f"已选择基因符号：{gene_symbol}")

    # 2. UniProt 查询

    banner("查询 UniProt Accession")

    uniprot_hits = search_uniprot(gene_symbol)

    if not uniprot_hits:

        print("⚠ UniProt 无结果，尝试直接搜索 PDB...")

        pdb_ids = get_pdb_ids_for_gene(gene_symbol)  # 需写一个简单函数

        if not pdb_ids:

            print("仍未找到结构，程序终止。")

            return

    idx = choose(

        [f'{h["acc"]} — {h["name"]}' for h in uniprot_hits], "请选择 UniProt 条目："

    )

    acc = uniprot_hits[idx]["acc"]

    print(f"已选择 UniProt ID: {acc}")

    # 获取结构来源

    banner("结构来源选择")

    sources = ["AlphaFold 预测结构", "PDB 实验结构"]

    src_idx = choose(sources, "请选择结构来源：")

    if src_idx == 0:

        struct_path = download_alphafold(acc)

        if not struct_path:

            print("AlphaFold 无可用模型，改用 PDB。")

            src_idx = 1

    if src_idx == 1:

        pdb_ids = get_pdb_ids_for_uniprot(acc)

        if not pdb_ids:

            print("无 PDB 结构！退出。")

            return

        pdb_idx = choose(pdb_ids, "请选择 PDB 编号：")

        struct_path = download_pdb(pdb_ids[pdb_idx])

    print(f"结构文件已下载：{struct_path}")

    # 3. 口袋预测

    banner("口袋预测方式")

    pocket_methods = ["本地 P2Rank（需要 Java 17+）"]

    p_idx = choose(pocket_methods, "请选择：")

    if p_idx == 0:

        pockets = run_p2rank(struct_path)

    else:

        pockets = run_dogsite_api(struct_path)

    if not pockets:

        print("口袋预测失败！")

        return

    pk_choices = [f"Score={p['score']:.2f}, Center={tuple(round(x,2) for x in p['center'])}"

                  for p in pockets]

    pk_idx = choose(pk_choices, "请选择作用口袋：")

    pocket_center = pockets[pk_idx]["center"]

    print("选定口袋中心坐标：", pocket_center)

    # 4. 获取候选配体SMILES

    banner("候选配体准备")

    mode = input("请选择候选配体来源：1-自动（ChEMBL IC50）  2-手动输入  [1/2]: ").strip()

    if mode == "1":

        smiles_list = fetch_chembl_smiles(acc, max_hits=10)

        if not smiles_list:

            print("未获取到 SMILES，转为手动输入模式。")

            mode = "2"

    if mode == "2":

        raw = input("请手动输入 SMILES 列表（逗号分隔）: ")

        smiles_list = [s.strip() for s in raw.split(",") if s.strip()]

    if not smiles_list:

        print("❌ 没有可用的候选配体，程序终止。")

        return

    # 保存结果文件
    results_file = TMP_DIR / "docking_input.txt"
    with open(results_file, "w") as f:
        f.write(f"疾病: {disease}\n")
        f.write(f"蛋白: {gene_symbol} (UniProt: {acc})\n")
        f.write(f"结构文件: {struct_path}\n")
        f.write(f"口袋中心坐标: {pocket_center}\n")
        f.write("\nSMILES列表:\n")
        for i, smi in enumerate(smiles_list, 1):
            f.write(f"{i}. {smi}\n")

    # 5. 保存配体SDF文件供后续使用
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol:
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())
            AllChem.UFFOptimizeMolecule(mol)
            sdf_file = TMP_DIR / f"ligand_{i+1}.sdf"
            Chem.MolToMolFile(mol, str(sdf_file))
            print(f"已保存配体{i+1}的SDF文件: {sdf_file}")

    banner("数据准备完成")
    print(f"所有文件已保存在: {TMP_DIR}")
    print("\n您可以使用以下网站进行后续虚拟筛选:")
    print("1. SwissDock: http://www.swissdock.ch/")
    print("2. CB-Dock: http://cao.labshare.cn/cb-dock2/")
    print("3. PrankWeb: https://prankweb.cz/")
    print("\n可以使用准备好的结构文件和口袋坐标进行对接，祝您科研顺利！")

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print("\n用户终止。")