import json
from requests.exceptions import HTTPError
from dotenv import load_dotenv
import openai
from Bio.PDB.alphafold_db import get_predictions
import re
import os
from pathlib import Path

# from __future__ import annotations

TMP_DIR = Path(os.getenv("TMP_DIR", "tmp"))
TMP_DIR.mkdir(exist_ok=True)

import os
import subprocess
import time
from pathlib import Path
from shutil import which
from typing import List, Dict, Optional

import pandas as pd
import requests

# 用于存放下载的 PDB 与本地 P2Rank 输出
TMP_DIR = Path(os.getenv("TMP_DIR", "tmp"))
TMP_DIR.mkdir(exist_ok=True)

UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb"
DS_MODEL_NAME = os.getenv('DS_MODEL_NAME', 'deepseek-chat')


def load_api_key():
    """Loads the DeepSeek API key from environment variables."""
    load_dotenv()
    api_key = os.getenv("DS_KEY")
    if not api_key:
        raise ValueError("API Key 'DS_KEY' not found in environment variables or .env file.")
    return api_key


def initialize_deepseek_client(key):
    """
    Initializes the DeepSeek (OpenAI) client using DS_API_KEY and DS_API_BASE.
    Returns None if the key is missing or client init fails.
    """
    if not key:
        return None
    # try:
    client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
    return client
    # except Exception as e:
    #     print(e.message)
    #     return None


def call_ai(client, model_name, prompt):
    """
    Calls DeepSeek chat completion with a system+user prompt.
    Returns the content string or None on error.
    """
    messages = [
        {"role": "system", "content": "You are a biology expert."},
        {"role": "user", "content": prompt}
    ]
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=False
        )
        return resp.choices[0].message.content
    except Exception:
        print(Exception)
        return None


def get_target_proteins(client, model_name, disease):
    """
    Given a DeepSeek client, model, and disease name (中文),
    returns a list of dicts: {"protein": UniProt关键词, "description": 解释}
    """
    prompt = (
        f'''请以 JSON 数组形式，仅返回导致疾病“{disease}”的6个潜在靶点蛋白关键词及其作为target的通俗学术解释，'''
        '''格式如下：
        [
          {
            "protein": "SLC6A4",
            "description": "Serotonin transporter, 在神经递质再摄取中起关键作用"
          },
          ...
        ]
        不要输出任何与 JSON 无关的文字。'''
    )
    raw = call_ai(client, model_name, prompt)
    if not raw:
        return []

    # 提取最外层的 [...] 部分
    match = re.search(r'\[.*\]', raw, re.S)
    if not match:
        print("未能在返回中找到 JSON 数组")
        return []

    try:
        data = json.loads(match.group(0))
        # 检查格式
        if isinstance(data, list) and all("protein" in p and "description" in p for p in data):
            return data
    except json.JSONDecodeError:
        print("JSON 解析失败:", match.group(0))
    return []


def search_uniprot(query, size=10):
    """
    Query UniProt using Lucene AND between terms.
    Returns list of dict with keys: accession, entry_name, protein_name.
    """
    terms = query.strip().split()
    lucene = " AND ".join(terms)
    params = {"query": lucene, "format": "json", "size": size}
    try:
        r = requests.get(f"{UNIPROT_BASE}/search", params=params, timeout=10)
        r.raise_for_status()
    except HTTPError:
        print(HTTPError)
        return []
    except requests.RequestException:
        print(requests.RequestException)
        return []

    js = r.json()
    results = []
    for it in js.get('results', []):
        acc = it.get('primaryAccession', '')
        entry = it.get('uniProtkbId', '')
        pname = it.get('proteinDescription', {}) \
            .get('recommendedName', {}) \
            .get('fullName', {}) \
            .get('value', '')
        results.append({
            'accession': acc,
            'entry_name': entry,
            'protein_name': pname
        })
    return results


def fetch_fasta(accession):
    """
    Fetch FASTA text for given UniProt accession.
    Returns FASTA string or empty.
    """
    try:
        r = requests.get(f"{UNIPROT_BASE}/{accession}.fasta", timeout=10)
        r.raise_for_status()
        return r.text
    except Exception:
        print(Exception)
        return ""


def predict_structure(accession):
    """
    Retrieve AlphaFold predictions for a UniProt accession.
    Returns a list of prediction dicts (each containing model_id, pdbUrl, paeUrl, etc.).
    """
    try:
        preds = get_predictions(accession)
    except Exception as e:
        print("Error retrieving predictions:", e)
        return []
    return preds


# 临时目录，用于存放 PDB 文件和 P2Rank 输出
TMP_DIR = Path(os.getenv('TMP_DIR', 'tmp'))
TMP_DIR.mkdir(exist_ok=True)


def run_p2rank(pdb_path: Path, prank_bin: Optional[str] = None) -> List[Dict]:
    """
    本地调用 P2Rank 预测口袋 (>=2.4)。
    返回：[{ 'center': (x, y, z), 'score': s }, ...]，按 score 降序。
    """
    # 1) 在项目或 HOME 下寻找 p2rank/prank
    candidates = [Path.cwd() / "p2rank/prank", Path.home() / "p2rank/prank"]
    bin_path: Optional[Path] = None
    for c in candidates:
        if c.is_file():
            bin_path = c
            break

    # 2) 环境变量 P2RANK_BIN
    if not bin_path:
        env = os.getenv("P2RANK_BIN")
        if env and Path(env).is_file():
            bin_path = Path(env)

    # 3) PATH 中 which("prank")
    if not bin_path:
        w = which("prank")
        if w:
            bin_path = Path(w)

    # 4) 传入的 prank_bin 参数
    if not bin_path and prank_bin:
        cand = Path(prank_bin).expanduser()
        if cand.is_file():
            bin_path = cand

    if not bin_path:
        raise FileNotFoundError(
            f"未找到 P2Rank 可执行文件。候选路径：{candidates}、"
            "环境变量 P2RANK_BIN，或 PATH 中的 prank。"
        )

    # 5) 执行预测
    out_dir = TMP_DIR / f"{pdb_path.stem}_p2rank"
    cmd = [str(bin_path), "predict", "-f", str(pdb_path), "-o", str(out_dir)]
    subprocess.run(cmd, check=True)

    # 6) 读取 CSV 并标准化列名
    csv_file = next(out_dir.glob("*_predictions.csv"))
    df = pd.read_csv(csv_file)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"\s+", "_", regex=True)
        .str.lower()
    )

    # 7) 提取口袋列表
    pockets: List[Dict] = []
    for _, row in df.iterrows():
        x, y, z = row["center_x"], row["center_y"], row["center_z"]
        score = row.get("score", row.get("ligandability_score"))
        pockets.append({
            "center": (float(x), float(y), float(z)),
            "score": float(score)
        })

    # 8) 返回按 score 降序
    return sorted(pockets, key=lambda p: p["score"], reverse=True)


def run_dogsite_api(pdb_path: Path) -> List[Dict]:
    """
    调用 ProteinsPlus DoGSiteScorer 在线口袋预测。
    返回：[{ 'center': (x, y, z), 'score': druggability }, ...]，按 score 降序。
    """
    # 1) 提交任务
    url_start = "https://proteins.plus/api/v2/dogsite/start/"
    with open(pdb_path, "rb") as f:
        r = requests.post(url_start, files={"file": f}, timeout=60)
    r.raise_for_status()
    job_id = r.json()["job_id"]

    # 2) 轮询状态
    url_status = f"https://proteins.plus/api/v2/dogsite/status/{job_id}/"
    url_result = f"https://proteins.plus/api/v2/dogsite/result/{job_id}/"
    for _ in range(60):
        time.sleep(5)
        status = requests.get(url_status).json().get("status")
        if status == "FINISHED":
            data = requests.get(url_result).json()
            pockets: List[Dict] = []
            for p in data.get("pockets", []):
                x, y, z = p["center"]
                pockets.append({
                    "center": (x, y, z),
                    "score": p["druggability_score"]
                })
            return sorted(pockets, key=lambda x: x["score"], reverse=True)

    raise RuntimeError("DoGSite 预测超时（>5 分钟）")
