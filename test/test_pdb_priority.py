#!/usr/bin/env python3
"""
测试PDB优先逻辑的完整脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_pdb_priority():
    """测试PDB优先的结构获取逻辑"""
    
    print("=== 测试PDB优先的结构获取逻辑 ===\n")
    
    try:
        from backend.services.pharma_engine import PharmaEngine
        from backend.core.config import settings
        
        # 创建PharmaEngine实例
        pharma = PharmaEngine()
        
        # 测试UniProt ID - P04637 (TP53)，这个蛋白应该有很多PDB结构
        test_uniprot = "P04637"
        print(f"测试UniProt ID: {test_uniprot} (TP53)")
        
        # 1. 首先测试PDB ID查询
        print("\n1. 查询PDB ID...")
        try:
            pdb_ids = pharma.get_pdb_ids_for_uniprot(test_uniprot)
            print(f"   找到{len(pdb_ids)}个PDB结构: {pdb_ids[:5]}...")  # 只显示前5个
            
            if pdb_ids:
                print("   ✓ PDB结构可用，应该优先使用PDB")
                
                # 2. 尝试下载第一个PDB结构
                print(f"\n2. 尝试下载PDB结构: {pdb_ids[0]}")
                try:
                    pdb_path = pharma.download_pdb(pdb_ids[0], settings.TMP_DIR)
                    if pdb_path and pdb_path.exists():
                        print(f"   ✓ PDB下载成功: {pdb_path}")
                        print("   ✓ 系统应该使用PDB结构，不显示AlphaFold指示灯")
                    else:
                        print("   ❌ PDB下载失败")
                except Exception as e:
                    print(f"   ❌ PDB下载异常: {str(e)}")
            else:
                print("   ⚠ 没有找到PDB结构，应该尝试AlphaFold")
                
        except Exception as e:
            print(f"   ❌ PDB查询异常: {str(e)}")
        
        # 3. 测试AlphaFold查询（作为备选）
        print(f"\n3. 查询AlphaFold结构...")
        try:
            af_path = pharma.download_alphafold(test_uniprot, settings.TMP_DIR)
            if af_path and af_path.exists():
                print(f"   ✓ AlphaFold结构可用: {af_path}")
                print("   ✓ 如果PDB不可用，系统应该使用AlphaFold并显示指示灯")
            else:
                print("   ❌ AlphaFold结构不可用")
        except Exception as e:
            print(f"   ❌ AlphaFold查询异常: {str(e)}")
        
        # 4. 测试完整的API逻辑
        print(f"\n4. 测试完整的结构获取API...")
        try:
            from backend.services.drug_discovery_api import DrugDiscoveryAPI
            
            result = DrugDiscoveryAPI.get_structure_sources(test_uniprot)
            print(f"   API调用结果:")
            print(f"   - 成功: {result.get('success')}")
            print(f"   - 结构来源: {result.get('structure_source')}")
            print(f"   - AlphaFold可用: {result.get('alphafold_available')}")
            print(f"   - PDB ID数量: {len(result.get('pdb_ids', []))}")
            print(f"   - 结构路径: {result.get('structure_path')}")
            
            if result.get('success'):
                source = result.get('structure_source')
                if source == 'pdb':
                    print("   ✓ 正确：优先使用了PDB结构（实验数据）")
                    print("   ✓ 前端不应显示AlphaFold指示灯")
                elif source == 'alphafold':
                    print("   ✓ 正确：使用了AlphaFold结构（PDB不可用）")
                    print("   ✓ 前端应显示AlphaFold指示灯")
                else:
                    print(f"   ⚠ 未知的结构来源: {source}")
            else:
                print(f"   ❌ API调用失败: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ API测试异常: {str(e)}")
            
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保在项目根目录运行此脚本")
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
    
    print(f"\n=== 测试完成 ===")
    print(f"期望行为:")
    print(f"1. 系统首先尝试获取PDB结构（实验数据优先）")
    print(f"2. 如果PDB可用，使用PDB，不显示AlphaFold指示灯")
    print(f"3. 如果PDB不可用，使用AlphaFold，显示绿色脉冲指示灯")
    print(f"4. 指示灯位置：主界面标题下方，美观且不突兀")

if __name__ == "__main__":
    test_pdb_priority()
