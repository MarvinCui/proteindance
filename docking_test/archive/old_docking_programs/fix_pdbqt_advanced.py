#!/usr/bin/env python3
"""
高级PDBQT文件修复工具
"""

import os
import sys

def fix_protein_pdbqt(input_file, output_file=None):
    """
    修复蛋白质PDBQT文件
    - 移除ROOT/ENDROOT标记
    - 只保留ATOM行
    - 移除MODEL/ENDMDL标记
    """
    if output_file is None:
        output_file = input_file.replace('.pdbqt', '_receptor.pdbqt')
    
    print(f"🔧 Fixing protein PDBQT file: {input_file}")
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    in_root = False
    
    for line in lines:
        # 跳过MODEL/ENDMDL标记
        if line.startswith('MODEL') or line.startswith('ENDMDL'):
            continue
        
        # 跳过ROOT/ENDROOT块
        if line.startswith('ROOT'):
            in_root = True
            continue
        elif line.startswith('ENDROOT'):
            in_root = False
            continue
        
        # 如果在ROOT块中，跳过
        if in_root:
            continue
        
        # 只保留ATOM行和REMARK行
        if line.startswith('ATOM') or line.startswith('REMARK'):
            output_lines.append(line)
    
    # 写入修复后的文件
    with open(output_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"✅ Fixed protein file saved as: {output_file}")
    print(f"   Original lines: {len(lines)}")
    print(f"   Fixed lines: {len(output_lines)}")
    
    return output_file

def fix_ligand_pdbqt(input_file, output_file=None):
    """
    修复配体PDBQT文件
    - 确保只有一个MODEL
    - 保留ROOT/ENDROOT结构
    """
    if output_file is None:
        output_file = input_file.replace('.pdbqt', '_ligand.pdbqt')
    
    print(f"🔧 Fixing ligand PDBQT file: {input_file}")
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    output_lines = []
    model_count = 0
    in_first_model = False
    
    for line in lines:
        if line.startswith('MODEL'):
            model_count += 1
            if model_count == 1:
                in_first_model = True
                continue  # 不包含MODEL行
            else:
                break  # 只处理第一个MODEL
        elif line.startswith('ENDMDL'):
            if in_first_model:
                break  # 不包含ENDMDL行
            continue
        
        # 如果还没有遇到MODEL行，或者在第一个MODEL中
        if not in_first_model and model_count == 0:
            output_lines.append(line)
        elif in_first_model:
            output_lines.append(line)
    
    # 如果没有找到MODEL，直接使用所有行
    if model_count == 0:
        output_lines = lines
    
    # 写入修复后的文件
    with open(output_file, 'w') as f:
        f.writelines(output_lines)
    
    print(f"✅ Fixed ligand file saved as: {output_file}")
    print(f"   Original lines: {len(lines)}")
    print(f"   Fixed lines: {len(output_lines)}")
    print(f"   Models processed: {model_count}")
    
    return output_file

def analyze_pdbqt_file(filename):
    """分析PDBQT文件内容"""
    print(f"\n📊 Analyzing file: {filename}")
    
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return None
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    stats = {
        'total_lines': len(lines),
        'atom_lines': 0,
        'remark_lines': 0,
        'root_blocks': 0,
        'model_count': 0,
        'has_root': False,
        'has_model': False
    }
    
    for line in lines:
        if line.startswith('ATOM') or line.startswith('HETATM'):
            stats['atom_lines'] += 1
        elif line.startswith('REMARK'):
            stats['remark_lines'] += 1
        elif line.startswith('ROOT'):
            stats['root_blocks'] += 1
            stats['has_root'] = True
        elif line.startswith('MODEL'):
            stats['model_count'] += 1
            stats['has_model'] = True
    
    print(f"   Total lines: {stats['total_lines']}")
    print(f"   ATOM lines: {stats['atom_lines']}")
    print(f"   REMARK lines: {stats['remark_lines']}")
    print(f"   ROOT blocks: {stats['root_blocks']}")
    print(f"   MODEL count: {stats['model_count']}")
    print(f"   Has ROOT: {stats['has_root']}")
    print(f"   Has MODEL: {stats['has_model']}")
    
    return stats

def main():
    """主函数"""
    print("🔧 Advanced PDBQT File Fixer")
    print("=" * 50)
    
    # 分析原始文件
    protein_file = "protein_structure.pdbqt"
    ligand_file = "original_ligand.pdbqt"
    
    if os.path.exists(protein_file):
        protein_stats = analyze_pdbqt_file(protein_file)
        
        if protein_stats:
            # 如果蛋白质文件有ROOT标记，说明格式不对
            if protein_stats['has_root']:
                print(f"\n⚠️  Protein file contains ROOT blocks (should be receptor format)")
                fixed_protein = fix_protein_pdbqt(protein_file, "protein_receptor.pdbqt")
                print(f"   → Use {fixed_protein} as receptor")
            else:
                print(f"\n✅ Protein file format seems correct")
                if protein_stats['model_count'] > 1:
                    print(f"   But has {protein_stats['model_count']} models, fixing...")
                    fixed_protein = fix_protein_pdbqt(protein_file, "protein_receptor.pdbqt")
    else:
        print(f"❌ Protein file not found: {protein_file}")
    
    if os.path.exists(ligand_file):
        ligand_stats = analyze_pdbqt_file(ligand_file)
        
        if ligand_stats:
            if ligand_stats['model_count'] > 1:
                print(f"\n⚠️  Ligand file has {ligand_stats['model_count']} models")
                fixed_ligand = fix_ligand_pdbqt(ligand_file, "ligand_single.pdbqt")
                print(f"   → Use {fixed_ligand} as ligand")
            else:
                print(f"\n✅ Ligand file format seems correct")
    else:
        print(f"❌ Ligand file not found: {ligand_file}")
    
    print("\n🎯 Recommended files for docking:")
    if os.path.exists("protein_receptor.pdbqt"):
        print("   Receptor: protein_receptor.pdbqt")
    else:
        print("   Receptor: protein_structure.pdbqt (original)")
    
    if os.path.exists("ligand_single.pdbqt"):
        print("   Ligand: ligand_single.pdbqt")
    else:
        print("   Ligand: original_ligand.pdbqt (original)")

if __name__ == "__main__":
    main()