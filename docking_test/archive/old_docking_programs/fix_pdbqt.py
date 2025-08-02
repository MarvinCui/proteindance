#!/usr/bin/env python3
"""
修复PDBQT文件中的多MODEL问题
"""

import os
import sys

def fix_pdbqt_file(input_file, output_file=None):
    """
    修复PDBQT文件，只保留第一个MODEL
    
    Args:
        input_file: 输入PDBQT文件
        output_file: 输出PDBQT文件，如果为None则覆盖原文件
    """
    if output_file is None:
        output_file = input_file + "_fixed.pdbqt"
    
    print(f"🔧 Fixing PDBQT file: {input_file}")
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # 提取第一个MODEL的内容
    output_lines = []
    in_first_model = False
    model_count = 0
    
    for line in lines:
        if line.startswith('MODEL'):
            model_count += 1
            if model_count == 1:
                in_first_model = True
                # 不添加MODEL行，直接开始内容
                continue
            else:
                # 遇到第二个MODEL就停止
                break
        elif line.startswith('ENDMDL'):
            if in_first_model:
                # 不添加ENDMDL行，直接结束
                break
            continue
        
        # 如果还没有遇到MODEL行，或者在第一个MODEL中，则添加内容
        if not in_first_model and not line.startswith('MODEL'):
            output_lines.append(line)
        elif in_first_model:
            output_lines.append(line)
    
    # 如果没有找到MODEL标记，则可能是单一结构，直接复制
    if model_count == 0:
        output_lines = lines
        print("   No MODEL tags found, copying as-is")
    else:
        print(f"   Found {model_count} models, keeping only the first one")
    
    # 写入修复后的文件
    with open(output_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"✅ Fixed file saved as: {output_file}")
    
    # 显示统计信息
    print(f"   Original lines: {len(lines)}")
    print(f"   Fixed lines: {len(output_lines)}")
    
    return output_file

def main():
    """主函数"""
    # 检查蛋白质结构文件
    protein_file = "protein_structure.pdbqt"
    ligand_file = "original_ligand.pdbqt"
    
    if not os.path.exists(protein_file):
        print(f"❌ File not found: {protein_file}")
        return
    
    if not os.path.exists(ligand_file):
        print(f"❌ File not found: {ligand_file}")
        return
    
    # 修复蛋白质文件
    print("🔧 Checking and fixing protein structure file...")
    
    # 检查是否有多个MODEL
    with open(protein_file, 'r') as f:
        content = f.read()
    
    model_count = content.count('MODEL')
    if model_count > 1:
        print(f"   Found {model_count} models in protein file")
        fixed_protein = fix_pdbqt_file(protein_file, "protein_structure_fixed.pdbqt")
        print(f"   Use {fixed_protein} for docking")
    else:
        print("   Protein file is OK (single model)")
    
    # 检查配体文件
    print("\n🔧 Checking ligand file...")
    with open(ligand_file, 'r') as f:
        content = f.read()
    
    model_count = content.count('MODEL')
    if model_count > 1:
        print(f"   Found {model_count} models in ligand file")
        fixed_ligand = fix_pdbqt_file(ligand_file, "original_ligand_fixed.pdbqt")
        print(f"   Use {fixed_ligand} for docking")
    else:
        print("   Ligand file is OK (single model)")
    
    print("\n✅ PDBQT files checked and fixed if needed")

if __name__ == "__main__":
    main()