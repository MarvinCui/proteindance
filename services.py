import os
import json
import requests
from requests.exceptions import HTTPError
from dotenv import load_dotenv
# from openai import OpenAI
import openai
from Bio.PDB.alphafold_db import get_predictions
import re
import time

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
    try:
        client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
        return client
    except Exception:
        print(Exception)
        return None


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

# def run_dogsite_api(pdb_path: Path) -> List[Dict]:
#     """
#     调 ProteinsPlus REST，返回 [{'center': (x,y,z), 'score': druggability}, ...]
#     文档: https://proteins.plus/api/v2/docs
#     """
#     print("ProteinsPlus DoGSiteScorer 在线口袋预测")
#     url_job = "https://proteins.plus/api/v2/dogsite/start/"
#     files = {"file": open(pdb_path, "rb")}
#     r = requests.post(url_job, files=files, timeout=60)
#     r.raise_for_status()
#     job_id = r.json()["job_id"]
#
#     # 轮询
#     url_stat = f"https://proteins.plus/api/v2/dogsite/status/{job_id}/"
#     url_res = f"https://proteins.plus/api/v2/dogsite/result/{job_id}/"
#     for _ in range(60):
#         time.sleep(5)
#         if requests.get(url_stat).json()["status"] == "FINISHED":
#             data = requests.get(url_res).json()
#             pockets = []
#             for p in data["pockets"]:
#                 x, y, z = p["center"]
#                 pockets.append({"center": (x, y, z),
#                                 "score": p["druggability_score"]})
#             # 分数高→更可成药；排序后返回
#             return sorted(pockets, key=lambda x: x["score"], reverse=True)
#     raise RuntimeError("DoGSite 预测超时")
