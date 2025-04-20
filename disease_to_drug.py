#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
disease_to_drug.py
------------------
交互式一键流程：
1) 读取疾病名称 → DeepSeek Chat API 查询潜在蛋白靶点
2) UniProt / PDB / AlphaFold 结构检索 & 下载
3) 口袋预测（本地 P2Rank / 云端 PrankWeb / DoGSiteScorer）
4) 虚拟筛选（本地 AutoDock Vina / 在线 CB‑Dock2 / SwissDock）
5) RDKit 优化命中化合物，调用 ADMETlab API 预测 ADMET
6) 输出 SMILES、ADMET 表格与 PNG 结构图
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
★ 默认路径全部纯 Python + Requests 可直接运行；
★ 需要Brew安装OpenBable，Java17+；
> brew install open-babel
★ 云端接口函数已留出 (TODO) 位置，按注释填参数即可启用。
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
import openai             # pip install openai>=1.2.4

# ------------------------------------------------------------------
# 全局配置
# ------------------------------------------------------------------
OPENAI_API_BASE = "https://api.deepseek.com/v1"   # DeepSeek Chat 兼容 OpenAI
OPENAI_API_KEY  = "sk-3a70318988b545919d22f99b6c522704"      # TODO: ←← 在此填入 DeepSeek API Key
TMP_DIR = Path(tempfile.gettempdir()) / "drug_flow"
TMP_DIR.mkdir(exist_ok=True)

openai.api_base = OPENAI_API_BASE
openai.api_key  = OPENAI_API_KEY

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
    rsp = openai.ChatCompletion.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    text = rsp["choices"][0]["message"]["content"]
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
            name = "(no name)"
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
    调用 P2Rank >=2.4 二进制 `prank` 预测口袋。
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
# 4. 虚拟筛选（默认本地 AutoDock Vina；可选在线 CB‑Dock2 / SwissDock）
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

import subprocess, os, stat
from pathlib import Path
from typing import Tuple, List, Dict

def run_local_vina(
    pdb_file: Path,
    pocket_center: Tuple[float, float, float],
    ligand_smiles: str,
    vina_exe: str = "./vina"
) -> float:
    """
    调用本地 AutoDock Vina，对单个 ligand_smiles 进行对接。
    返回 binding affinity (kcal/mol)。对接过程的全部输出写入 TMP_DIR/'vina.log'。
    """
    # 确保 vina 可执行
    mode = os.stat(vina_exe).st_mode
    if not (mode & stat.S_IXUSR):
        os.chmod(vina_exe, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    banner("AutoDock Vina 对接")

    # 1) 准备受体 pdbqt
    receptor_pdbqt = pdb_file.with_suffix(".pdbqt")
    if not receptor_pdbqt.exists():
        print(f"▶ obabel 生成受体 pdbqt：obabel {pdb_file} -O {receptor_pdbqt}")
        subprocess.run(["obabel", str(pdb_file), "-O", str(receptor_pdbqt)], check=True)

    # 2) 准备配体 pdbqt
    ligand_pdbqt = smiles_to_pdbqt(ligand_smiles)

    # 3) 构造 vina 命令
    x, y, z = pocket_center
    cmd = [
        vina_exe,
        "--receptor", str(receptor_pdbqt),
        "--ligand", str(ligand_pdbqt),
        "--center_x", f"{x:.4f}",
        "--center_y", f"{y:.4f}",
        "--center_z", f"{z:.4f}",
        "--size_x", "20", "--size_y", "20", "--size_z", "20",
        "--exhaustiveness", "8",
        "--out", str(TMP_DIR / "vina_out.pdbqt"),
    ]
    print("▶", " ".join(cmd))

    # 4) 运行并捕获输出
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    # 5) 同步写入日志文件
    log_file = TMP_DIR / "vina.log"
    with open(log_file, "w") as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout or "(无 stdout)\n")
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr or "(无 stderr)\n")

    # 6) 检查返回码
    if result.returncode != 0:
        print(f"⚠ Vina 返回非零退出码 {result.returncode}，详情见 {log_file}")
        result.check_returncode()  # 会抛异常

    # 7) 从 stdout 里解析第一条打分记录
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        # 通常对接结果行以“1”开头： “1   -7.4    0.000   0.000 ...”
        if parts and parts[0].isdigit():
            try:
                score = float(parts[1])
                print(f"✔ 解析得分 {score} kcal/mol")
                return score
            except ValueError:
                continue

    # 若未能解析到，返回一个高分表示不理想
    print("⚠ 未能解析 vina 得分，返回 +99.0")
    return 99.0

def run_swissdock_api(
    ligand: Union[str, Path],
    target: Union[Path],
    box_center: Tuple[float, float, float],
    box_size:   Tuple[float, float, float],
    mode: str = "vina",              # "vina" 或 "ac"
    pH: Optional[float] = None,      # SMILES 专用
    water: bool = False,             # AC 专用，保留水分子
    exhaust: int = 4,                # Vina 默认 4；AC 默认 90
    cavity: Optional[int] = None,    # AC 专用，默认 70
    ric:    Optional[int] = None,    # AC 专用，默认 2
    name:   Optional[str] = None,    # 作业名称
    poll_interval: int = 10,
    max_wait:      int = 60
) -> float:
    """
    完整 SwissDock 对接流程，支持 AC 和 Vina 两种模式：

    1) 检查服务器
    2) 上传并准备配体 (Mol2 | SMILES | tar.gz)
    3) 上传并准备受体 (坐标文件 | tar.gz)
    4) 设置并检查参数 (exhaust, cavity, ric, boxCenter, boxSize, name)
    5) 启动对接
    6) 轮询状态
    7) 下载并解析最优 binding energy

    返回:
      最优结合能 (kcal/mol)
    """
    server = "https://www.swissdock.ch:8443"

    # 1) 检查服务器
    r = requests.get(f"{server}/")
    r.raise_for_status()
    if "Hello World!" not in r.text:
        raise RuntimeError("SwissDock 服务器未响应 ‘Hello World!’")

    # 2) 上传并准备配体
    params = {}
    files = None
    if isinstance(ligand, Path):
        # Mol2 文件或 tar.gz
        files = {"myLig": open(ligand, "rb")}
        if mode.lower() == "vina":
            params["Vina"] = ""
    else:
        # SMILES
        params["mySMILES"] = ligand
        if pH is not None:
            params["pH"] = pH
        if mode.lower() == "vina":
            params["Vina"] = ""
    r = requests.post(f"{server}/preplig", params=params, files=files) if files else \
        requests.get (f"{server}/preplig", params=params)
    r.raise_for_status()

    # 解析 sessionNumber
    resp = r.text.strip().strip('"')
    if resp.startswith("http"):
        qs = parse_qs(urlparse(resp).query)
        session = int(qs["sessionNumber"][0])
    else:
        m = re.search(r"(\d+)", resp)
        session = int(m.group(1)) if m else None
    if session is None:
        raise RuntimeError(f"无法解析 sessionNumber: {r.text}")
    print(f"→ Ligand prepared, session {session}")

    # 3) 上传并准备受体
    tgt_params = {"sessionNumber": session}
    if isinstance(target, Path) and target.suffix in (".tar", ".gz", ".tgz"):
        files = {"myTarget": open(target, "rb")}
    else:
        files = {"myTarget": open(target, "rb")}
        if mode.lower() == "ac" and water:
            tgt_params["water"] = ""
    if mode.lower() == "vina":
        tgt_params["sessionNumber"] = session
    r = requests.post(f"{server}/preptarget", params=tgt_params, files=files)
    r.raise_for_status()
    print("→ Target prepared")

    # 4) 设置并检查参数
    param_payload = {"sessionNumber": session}
    if mode.lower() == "vina":
        param_payload["exhaust"]   = exhaust
    else:
        param_payload["exhaust"]   = exhaust
        if cavity is not None: param_payload["cavity"] = cavity
        if ric    is not None: param_payload["ric"   ] = ric
    param_payload["boxCenter"] = f"{box_center[0]}_{box_center[1]}_{box_center[2]}"
    param_payload["boxSize"]   = f"{box_size[0]}_{box_size[1]}_{box_size[2]}"
    if name:
        param_payload["name"] = name

    r = requests.get(f"{server}/setparameters", params=param_payload)
    r.raise_for_status()
    print("→ Parameters set & checked")

    # 5) 启动对接
    r = requests.get(f"{server}/startdock", params={"sessionNumber": session})
    r.raise_for_status()
    print("→ Docking submitted")

    # 6) 轮询状态直到完成
    start = time.time()
    while True:
        r = requests.get(f"{server}/checkstatus", params={"sessionNumber": session})
        text = r.text
        if "Calculation is finished" in text:
            print("→ Calculation finished")
            break
        if time.time() - start > max_wait * 60:
            raise RuntimeError("SwissDock 对接超时")
        time.sleep(poll_interval)

    # 7) 下载并解析结果
    r = requests.get(f"{server}/retrievesession", params={"sessionNumber": session})
    r.raise_for_status()
    bio = io.BytesIO(r.content)
    energies = []
    with tarfile.open(fileobj=bio, mode="r:gz") as tf:
        for member in tf.getmembers():
            if member.name.lower().endswith(".txt"):
                f = tf.extractfile(member)
                if not f:
                    continue
                txt = f.read().decode(errors="ignore")
                energies += [float(x) for x in re.findall(r"[-+]?\d+\.\d+", txt)]

    if not energies:
        raise RuntimeError("未能从结果文件中提取能量值")
    best = min(energies)
    print(f"Best binding energy: {best} kcal/mol")
    return best

# ------------------------------------------------------------------
# 5. RDKit 分子优化 & ADMETlab 预测
# ------------------------------------------------------------------
def admetlab_predict(smiles_list: List[str]) -> pd.DataFrame:
    """
    使用 ADMETlab 3.0 批量预测。
    官方 API 目前**无需任何身份验证**，POST JSON 即可。
    文档示例端点:  https://admetlab3.scbdd.com/api/v2/predict/batch
    输入: {"smiles": ["C[C@H](N)C(=O)O", ...]}
    返回: {"C[C@H](N)C(=O)O": {"LogS":‑2.31, ...}, ...}
    """
    url = "https://admetlab3.scbdd.com/api/v2/predict/batch"
    payload = {"smiles": smiles_list}
    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠ ADMETlab 请求失败：{e}")
        return pd.DataFrame({"SMILES": smiles_list})

    raw = r.json()
    records = []
    for smi, props in raw.items():
        row = {"SMILES": smi}
        row.update(props)          # 展开 119 个 ADMET 属性
        records.append(row)
    return pd.DataFrame(records)

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

    # 4. 虚拟筛选
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
    method_vs = choose(["本地 AutoDock Vina", "SwissDock"], "选择对接方式：")
    scores = []
    DEFAULT_BOX_SIZE = (20.0, 20.0, 20.0)
    for smi in smiles_list:
        if method_vs == 0:
            score = run_local_vina(struct_path, pocket_center, smi)
        else:
            # 这里把 pocket_center 和 box_size 传进去
            score = run_swissdock_api(
                smi,  # ligand
                struct_path,  # target
                pocket_center,
                DEFAULT_BOX_SIZE
            )
            scores.append({"smiles": smi, "score": score})
        print(f"SMI={smi}, Score={score}")
    scores.sort(key=lambda x: x["score"])  #  score 越低越好

    # 5. 取 top1 优化 & ADMET
    top_hit = scores[0]["smiles"]
    opt_smiles = optimize_smiles(top_hit)
    banner("优化后 SMILES")
    print(opt_smiles)
    draw_smiles(opt_smiles, TMP_DIR / "hit.png")
    print("结构图已保存:", TMP_DIR / "hit.png")

    admet_df = admetlab_predict([opt_smiles])
    if not admet_df.empty:
        banner("ADMET 预测结果")
        print(admet_df.to_markdown(index=False))

    banner("流程结束，祝你科研顺利！")
    print(f"所有中间文件保存在: {TMP_DIR}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户终止。")