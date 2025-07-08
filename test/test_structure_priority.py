#!/usr/bin/env python3
"""
测试结构获取优先级的脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.drug_discovery_api import DrugDiscoveryAPI

def test_structure_priority():
    """测试PDB优先的结构获取逻辑"""
    
    print("=== 测试结构获取优先级 ===")
    
    # 测试几个常见的UniProt ID
    test_cases = [
        "P04637",  # TP53 - 应该有PDB结构
        "P00533",  # EGFR - 应该有PDB结构  
        "Q9Y6K9",  # 一个可能只有AlphaFold的蛋白
    ]
    
    for uniprot_acc in test_cases:
        print(f"\n--- 测试 {uniprot_acc} ---")
        try:
            result = DrugDiscoveryAPI.get_structure_sources(uniprot_acc)
            print(f"成功: {result.get('success')}")
            print(f"结构来源: {result.get('structure_source')}")
            print(f"AlphaFold可用: {result.get('alphafold_available')}")
            print(f"PDB ID数量: {len(result.get('pdb_ids', []))}")
            print(f"结构路径: {result.get('structure_path')}")
            
            if result.get('success'):
                source = result.get('structure_source')
                if source == 'pdb':
                    print("✓ 正确使用了PDB结构（实验结构优先）")
                elif source == 'alphafold':
                    print("✓ 使用了AlphaFold结构（PDB不可用时的备选）")
                else:
                    print("⚠ 结构来源未知")
            else:
                print(f"❌ 失败: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")

if __name__ == "__main__":
    test_structure_priority()
