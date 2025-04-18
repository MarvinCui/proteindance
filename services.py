import os
import json
import requests
from requests.exceptions import HTTPError
from dotenv import load_dotenv
from openai import OpenAI
from Bio.PDB.alphafold_db import get_predictions

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
        client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
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
    returns a list of 5 UniProt keywords (strings) or empty list.
    """
    prompt = (
        f'''请以 JSON 数组形式，仅返回导致疾病“{disease}”的5个潜在靶点蛋白关键词（英文，可用于UniProt查询），不要其他文字。如["SLC6A4", "MAOA", "HTR2A", "COMT", "BDNF"]'''
    )
    raw = call_ai(client, model_name, prompt)
    print(raw)
    if not raw:
        return []
    try:
        arr = json.loads(raw.strip())
        if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
            return arr
    except json.JSONDecodeError:
        print(json.JSONDecodeError)
        pass
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
    Returns list of PDB URLs (strings).
    """
    for pred in get_predictions(accession):
        # pred 是包含 model_id、pdbUrl、paeUrl 等键的 dict
        print(f"PDB URL: {pred.get('pdbUrl')}")
    urls = []
    try:
        for pred in get_predictions(accession):
            url = pred.get('pdbUrl')
            print(pred)
            print(url)
            if url:
                urls.append(url)
    except Exception:
        print(Exception)
        pass
    return urls
