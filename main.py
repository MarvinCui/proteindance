import requests
from requests.exceptions import HTTPError
from Bio.PDB.alphafold_db import get_predictions

from openai import OpenAI
from dotenv import load_dotenv
import os

BASE_URL = "https://rest.uniprot.org/uniprotkb"


# def find_target():


def search_proteins(raw_query, size=10):
    """
    调用 UniProt search 接口：
      1. 用 AND 拼接多词查询，符合 Lucene 语法；
      2. 不指定 fields，以获取默认返回的所有必要字段；
      3. 返回包含 accession、entry_name、protein_name 的结果列表。
    """
    # 1. Lucene 查询预处理
    terms = raw_query.strip().split()
    lucene_query = " AND ".join(terms) if len(terms) > 1 else terms[0]

    params = {
        "query": lucene_query,
        "format": "json",
        "size": size
    }

    try:
        resp = requests.get(f"{BASE_URL}/search", params=params)
        resp.raise_for_status()
    except HTTPError as e:
        print(f"Error fetching search results: {e}")
        print(f"Response body:\n{e.response.text}")
        return []

    data = resp.json()
    results = []
    for item in data.get("results", []):
        # 从默认 JSON 中提取字段
        accession = item.get("primaryAccession", "")
        entry_name = item.get("uniProtkbId", "")
        # 蛋白名称通常在 proteinDescription.recommendedName.fullName.value
        prot_desc = item.get("proteinDescription", {})
        prot_name = prot_desc.get("recommendedName", {}) \
            .get("fullName", {}) \
            .get("value", "")
        results.append({
            "accession": accession,
            "entry_name": entry_name,
            "protein_name": prot_name
        })
    return results


def fetch_fasta(accession):
    """
    根据 accession 获取 FASTA 序列。
    """
    try:
        resp = requests.get(f"{BASE_URL}/{accession}.fasta")
        resp.raise_for_status()
        return resp.text
    except HTTPError as e:
        print(f"Error fetching FASTA for {accession}: {e}")
        return ""


import json
import requests


def get_target_proteins(client, model_name, disease):
    """
    调用 DeepSeek 分析给定疾病的潜在靶点蛋白，返回一个包含 5 个英文关键词的列表。
    DeepSeek 的输出将仅包含一个 JSON 数组，例如：
        ["TP53", "EGFR", "BRCA1", "MYC", "VEGFA"]
    """
    # 提示 DeepSeek 仅输出 JSON 数组，不要任何多余文字
    prompt = (
        f"请以 JSON 数组的形式，仅返回与疾病“{disease}”相关的 5 个潜在靶点蛋白关键词（英文，"
        '''可用于 PDB 查询），不要输出任何解释或额外文字。如["SLC6A4", "MAOA", "HTR2A", "COMT", "BDNF"]'''
    )
    resp = call_gemini_api(client, model_name, prompt, "")
    if not resp:
        return []

    try:
        # 直接把响应解析成 Python 列表
        keywords = json.loads(resp)
        if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
            return keywords
        else:
            print("DeepSeek 返回的格式不正确，期望 JSON 数组：", resp)
            return []
    except json.JSONDecodeError:
        print("解析 DeepSeek 返回结果失败，请检查接口输出：", resp)
        return []
        pass


def call_gemini_api(client, model_name, prompt, content_string):
    """Calls the DeepSeek chat completions API with the combined prompt and content."""
    if not client:
        print("错误：DeepSeek 客户端未初始化。")
        return None
    if prompt is None or content_string is None:
        print("错误：提示或内容为空，无法调用 API。")
        return None

    full_prompt = f"{prompt}{content_string}"
    messages = [
        {"role": "system", "content": "You are a biology expert"},
        {"role": "user", "content": full_prompt},
    ]
    print("\n正在调用 DeepSeek API...")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=False
        )
        print("API 调用成功。")
        return response.choices[0].message.content
    except Exception as e:
        print(f"调用 DeepSeek API 时出错: {e}")
        return None


def interpret_fasta(fasta):
    # 1. 从 FASTA 文本中提取 header 和 accession
    lines = fasta.strip().splitlines()
    header = lines[0]  # e.g. ">sp|P31645|SC6A4_HUMAN …"
    accession = header.split("|")[1]  # 提取 "P31645"
    return accession


def initialize_genai_client(api_key):
    """Initializes and returns the DeepSeek (OpenAI) client."""
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        return client
    except Exception as e:
        print(f"Error initializing DeepSeek client: {e}")
        return None


def predict(accession):
    print(f"\n正在获取 {accession} 的 AlphaFold 结构预测模型…")
    for pred in get_predictions(accession):
        # pred 是包含 model_id、pdbUrl、paeUrl 等键的 dict
        print(f"PDB URL: {pred.get('pdbUrl')}")


def load_api_key():
    """Loads the DeepSeek API key from environment variables."""
    load_dotenv()
    api_key = os.getenv("DS_KEY")
    if not api_key:
        raise ValueError("API Key 'DS_KEY' not found in environment variables or .env file.")
    return api_key


def main():
    # DS_MODEL_NAME = "deepseek-reasoner"
    DS_MODEL_NAME = "deepseek-chat"
    disease = input("请输入疾病名称（中文）：").strip()
    if not disease:
        print("疾病名称不能为空。")
        return

    try:
        api_key = load_api_key()
        client = initialize_genai_client(api_key)
        if not client:
            return
    except ValueError as e:
        print(f"配置错误: {e}")
        return

    # 2）调用 DeepSeek 得到靶点蛋白列表
    proteins = get_target_proteins(client, DS_MODEL_NAME, disease)
    for p in proteins:
        print(p)

    choice = input(f"\n请选择蛋白编号（1-{len(proteins)}）：").strip()
    try:
        sel = proteins[int(choice) - 1]
    except (ValueError, IndexError):
        print("选择无效。")
        return

    # 4）下载并输出选中蛋白的 FASTA 序列
    # fasta = fetch_fasta(sel["uniprot_id"])
    # query = input("请输入要搜索的蛋白名称或关键词: ")
    candidates = search_proteins(sel)
    if not candidates:
        print("未找到匹配的条目，或请求出错。")
        return

    print("\n检索到以下候选：")
    for i, ent in enumerate(candidates, 1):
        print(f"{i}. {ent['entry_name']} ({ent['accession']}) — {ent['protein_name']}")
    choice = int(input(f"\n请选择 [1-{len(candidates)}]: "))
    sel = candidates[choice - 1]

    fasta = fetch_fasta(sel["accession"])
    id = interpret_fasta(fasta)
    pdb = predict(id)
    if fasta:
        print(f"\n> {sel['entry_name']} ({sel['accession']}) 的 FASTA 序列：\n")
        print(fasta)


if __name__ == "__main__":
    main()
