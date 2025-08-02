#!/usr/bin/env python3
"""
修复配体位置，将其移动到蛋白质结合区域
"""

def fix_ligand_coordinates(input_file, output_file, target_center=(2.8, 23.3, 14.1)):
    """
    将配体移动到目标中心位置
    """
    print(f"修复配体位置: {input_file} -> {output_file}")
    print(f"目标中心: {target_center}")
    
    # 读取原始配体坐标
    ligand_coords = []
    other_lines = []
    
    with open(input_file, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                x = float(line[30:38].strip())
                y = float(line[38:46].strip()) 
                z = float(line[46:54].strip())
                ligand_coords.append((x, y, z))
                other_lines.append(line)
            else:
                other_lines.append(line)
    
    if not ligand_coords:
        print("错误：没有找到配体原子坐标")
        return False
        
    # 计算当前配体中心
    current_center = (
        sum(coord[0] for coord in ligand_coords) / len(ligand_coords),
        sum(coord[1] for coord in ligand_coords) / len(ligand_coords),
        sum(coord[2] for coord in ligand_coords) / len(ligand_coords)
    )
    
    print(f"当前配体中心: ({current_center[0]:.3f}, {current_center[1]:.3f}, {current_center[2]:.3f})")
    
    # 计算平移向量
    translation = (
        target_center[0] - current_center[0],
        target_center[1] - current_center[1], 
        target_center[2] - current_center[2]
    )
    
    print(f"平移向量: ({translation[0]:.3f}, {translation[1]:.3f}, {translation[2]:.3f})")
    
    # 应用平移并写入新文件
    with open(output_file, 'w') as f:
        coord_index = 0
        for line in other_lines:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                # 解析坐标
                prefix = line[:30]
                x = float(line[30:38].strip())
                y = float(line[38:46].strip()) 
                z = float(line[46:54].strip())
                suffix = line[54:]
                
                # 应用平移
                new_x = x + translation[0]
                new_y = y + translation[1]
                new_z = z + translation[2]
                
                # 重新格式化坐标
                new_line = f"{prefix}{new_x:8.3f}{new_y:8.3f}{new_z:8.3f}{suffix}"
                f.write(new_line)
                coord_index += 1
            else:
                f.write(line)
    
    print(f"✓ 配体坐标已修复，保存到: {output_file}")
    print(f"✓ 处理了 {coord_index} 个原子")
    return True

if __name__ == "__main__":
    # 修复原始配体位置
    success = fix_ligand_coordinates(
        './original_ligand.pdbqt',
        './ligand_fixed_position.pdbqt',
        target_center=(2.8, 23.3, 14.1)  # 蛋白质几何中心
    )
    
    if success:
        print("\n验证修复后的坐标:")
        # 验证新坐标
        with open('./ligand_fixed_position.pdbqt', 'r') as f:
            coords = []
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip()) 
                    z = float(line[46:54].strip())
                    coords.append((x, y, z))
        
        if coords:
            new_center = (
                sum(coord[0] for coord in coords) / len(coords),
                sum(coord[1] for coord in coords) / len(coords),
                sum(coord[2] for coord in coords) / len(coords)
            )
            print(f"新配体中心: ({new_center[0]:.3f}, {new_center[1]:.3f}, {new_center[2]:.3f})")
            
            x_range = (min(coord[0] for coord in coords), max(coord[0] for coord in coords))
            y_range = (min(coord[1] for coord in coords), max(coord[1] for coord in coords))
            z_range = (min(coord[2] for coord in coords), max(coord[2] for coord in coords))
            
            print(f"配体坐标范围:")
            print(f"  X: {x_range[0]:.1f} 到 {x_range[1]:.1f}")
            print(f"  Y: {y_range[0]:.1f} 到 {y_range[1]:.1f}")
            print(f"  Z: {z_range[0]:.1f} 到 {z_range[1]:.1f}")