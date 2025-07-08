from smolagents import tool, LiteLLMModel, CodeAgent
import requests
import logging
from typing import List, Dict, Optional, Tuple
import dotenv, os

dotenv.load_dotenv()
api_key = os.getenv("anthropic")


@tool
def search_uniprot( gene_symbol: str, organism_id: str = "9606") -> List[Dict]:
    """
    搜索UniProt数据库
    
    Args:
        gene_symbol: 基因符号 exp :c3
        organism_id: 物种ID (默认9606为人类)
    
    Returns:
        UniProt条目列表
        UniProt Accession : 蛋白的唯一识别号,常作为唯一键用于跨平台（如PDB、Ensembl、ChEMBL、AlphaFold）整合分析。在返回列表的acc
    """
    try:
        print(f"正在搜索UniProt数据库中的{gene_symbol}...")
        
        url = ("https://rest.uniprot.org/uniprotkb/search"
                f"?query=(gene_exact:{gene_symbol}+AND+organism_id:{organism_id})"
                f"&fields=accession,protein_name&format=json&size=10")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for entry in data.get("results", []):
            try:
                # 尝试获取蛋白质名称，处理不同的API响应格式
                name = "Unknown protein"
                if "proteinDescription" in entry:
                    desc = entry["proteinDescription"]
                    if "recommendedName" in desc and desc["recommendedName"]:
                        if "fullName" in desc["recommendedName"]:
                            name = desc["recommendedName"]["fullName"]["value"]
                    elif "submissionNames" in desc and desc["submissionNames"]:
                        name = desc["submissionNames"][0]["fullName"]["value"]

                results.append({
                    "acc": entry["primaryAccession"],
                    "name": name
                })
            except (KeyError, TypeError) as e:
                print(f"解析UniProt条目失败: {e}")
                # 仍然添加条目，但使用默认名称
                results.append({
                    "acc": entry.get("primaryAccession", "Unknown"),
                    "name": "Unknown protein"
                })
        
        print(f"找到{len(results)}个UniProt条目")
        print(results)
        return results  # 添加返回语句
        
    except Exception as e:
        print(f"UniProt搜索失败: {str(e)}")
        return []  # 出错时返回空列表

 

if __name__ == "__main__":
    model = LiteLLMModel(model_id="anthropic/claude-3-5-sonnet-latest", api_key=api_key)
    agent = CodeAgent(model = model, tools=[search_uniprot]) 
    agent.run("帮我查询抑郁症治病靶点蛋白的Accession(acc)")  