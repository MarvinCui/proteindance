#!/usr/bin/env python3
"""
使用现有PDBQT文件进行AutoDock Vina分子对接 - 修复版本
"""

import os
import subprocess
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re

# 设置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class VinaDockerWithFiles:
    def __init__(self, vina_executable="./vina"):
        """
        初始化对接器

        Args:
            vina_executable (str): vina可执行文件路径
        """
        self.vina_executable = vina_executable
        self.receptor_file = "protein_receptor.pdbqt"
        self.ligand_file = "original_ligand.pdbqt"
        self.output_dir = "./docking_results"

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 检查文件是否存在
        if not self._check_files():
            raise FileNotFoundError("Required files not found!")

    def _check_files(self):
        """检查必要的文件是否存在"""
        print("🔍 Checking files...")

        files_ok = True
        
        if not os.path.exists(self.receptor_file):
            print(f"❌ Receptor file not found: {self.receptor_file}")
            files_ok = False
        else:
            print(f"✅ Receptor file: {self.receptor_file}")

        if not os.path.exists(self.ligand_file):
            print(f"❌ Ligand file not found: {self.ligand_file}")
            files_ok = False
        else:
            print(f"✅ Ligand file: {self.ligand_file}")

        if not os.path.exists(self.vina_executable):
            print(f"❌ Vina executable not found: {self.vina_executable}")
            files_ok = False
        else:
            print(f"✅ Vina executable: {self.vina_executable}")

        return files_ok

    def get_ligand_center(self):
        """
        从配体文件中计算配体的几何中心，用作对接中心
        """
        try:
            with open(self.ligand_file, 'r') as f:
                lines = f.readlines()
            
            coords = []
            for line in lines:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    # 解析PDB格式的坐标
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())
                    coords.append([x, y, z])
            
            if coords:
                coords = np.array(coords)
                center = np.mean(coords, axis=0)
                print(f"📍 Ligand center calculated: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
                return tuple(center)
            else:
                print("⚠️ No coordinates found in ligand file, using default center")
                return (0.0, 0.0, 0.0)
        except Exception as e:
            print(f"⚠️ Error calculating ligand center: {e}")
            return (0.0, 0.0, 0.0)

    def run_docking(self, center=(-0.45, 34.90, 3.59), box_size=(20.0, 20.0, 20.0)):
        """
        运行分子对接

        Args:
            center (tuple): 结合口袋中心坐标
            box_size (tuple): 搜索盒子大小
        """
        # 如果没有提供中心，使用配体中心
        if center is None:
            center = self.get_ligand_center()

        print("🚀 Starting molecular docking...")
        print("=" * 60)
        print(f"📍 Docking center: {center}")
        print(f"📦 Search box size: {box_size}")

        # 输出文件
        output_file = os.path.join(self.output_dir, 'docking_results.pdbqt')
        
        # 构建vina命令
        cmd = [
            self.vina_executable,
            "--receptor", self.receptor_file,
            "--ligand", self.ligand_file,
            "--center_x", str(center[0]),
            "--center_y", str(center[1]),
            "--center_z", str(center[2]),
            "--size_x", str(box_size[0]),
            "--size_y", str(box_size[1]),
            "--size_z", str(box_size[2]),
            "--out", output_file,
            "--exhaustiveness", "8",
            "--num_modes", "3",
            "--energy_range", "3"
        ]

        print(f"🔄 Executing command: {' '.join(cmd)}")
        print("⏳ Docking calculation in progress (this may take a few minutes)...")

        try:
            # 运行对接
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            if result.returncode == 0:
                print("✅ Docking calculation completed!")
                print("\n📊 Vina output:")
                print(result.stdout)

                # 解析结果
                binding_energies = self._parse_results(result.stdout)

                if os.path.exists(output_file):
                    print(f"✅ Results saved to: {output_file}")
                    return output_file, binding_energies, center, box_size
                else:
                    print("❌ Output file not generated")
                    return None, [], center, box_size
            else:
                print("❌ Docking calculation failed!")
                print(f"Error: {result.stderr}")
                print(f"Stdout: {result.stdout}")
                return None, [], center, box_size

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            return None, [], center, box_size

    def _parse_results(self, vina_output):
        """解析Vina输出中的结合能信息"""
        binding_energies = []
        
        # 寻找结果表格
        lines = vina_output.split('\n')
        in_results = False
        
        for line in lines:
            # 查找结果表格开始
            if "mode |   affinity | dist from best mode" in line:
                in_results = True
                continue
            elif in_results and "-----+" in line:
                continue
            elif in_results and line.strip():
                # 解析结果行
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        mode = int(parts[0])
                        affinity = float(parts[1])  # 亲和力在第2列
                        rmsd_lb = float(parts[2]) if len(parts) > 2 else 0.0
                        rmsd_ub = float(parts[3]) if len(parts) > 3 else 0.0
                        
                        binding_energies.append({
                            'mode': mode,
                            'affinity': affinity,
                            'rmsd_lb': rmsd_lb,
                            'rmsd_ub': rmsd_ub
                        })
                    except (ValueError, IndexError):
                        continue
            elif in_results and not line.strip():
                # 空行表示结果表格结束
                break
                
        return binding_energies

    def analyze_results(self, binding_energies):
        """分析对接结果"""
        if not binding_energies:
            print("❌ No results to analyze")
            return

        print("\n" + "=" * 60)
        print("📊 Docking Results Analysis")
        print("=" * 60)

        print(f"{'Mode':<6} {'Affinity':<12} {'RMSD l.b.':<10} {'RMSD u.b.':<10}")
        print("-" * 50)

        for result in binding_energies:
            print(f"{result['mode']:<6} {result['affinity']:<12.2f} {result['rmsd_lb']:<10.2f} {result['rmsd_ub']:<10.2f}")

        # 最佳结果分析
        best_result = binding_energies[0]
        best_energy = best_result['affinity']

        print(f"\n🏆 Best binding pose:")
        print(f"   Mode: {best_result['mode']}")
        print(f"   Binding affinity: {best_energy:.2f} kcal/mol")

        if best_energy < -8.0:
            print("✅ Excellent binding affinity!")
        elif best_energy < -7.0:
            print("✅ Good binding affinity!")
        elif best_energy < -5.0:
            print("⚠️ Moderate binding affinity")
        else:
            print("❌ Weak binding affinity")

        return best_result

    def visualize_binding_site(self, center, box_size):
        """可视化结合位点和搜索空间"""
        fig = plt.figure(figsize=(15, 12))

        # 3D图
        ax1 = fig.add_subplot(221, projection='3d')

        # 绘制搜索盒子
        x_min, x_max = center[0] - box_size[0]/2, center[0] + box_size[0]/2
        y_min, y_max = center[1] - box_size[1]/2, center[1] + box_size[1]/2
        z_min, z_max = center[2] - box_size[2]/2, center[2] + box_size[2]/2

        # 绘制盒子边框
        edges = [
            [(x_min, y_min, z_min), (x_max, y_min, z_min)],
            [(x_min, y_max, z_min), (x_max, y_max, z_min)],
            [(x_min, y_min, z_max), (x_max, y_min, z_max)],
            [(x_min, y_max, z_max), (x_max, y_max, z_max)],
            [(x_min, y_min, z_min), (x_min, y_max, z_min)],
            [(x_max, y_min, z_min), (x_max, y_max, z_min)],
            [(x_min, y_min, z_max), (x_min, y_max, z_max)],
            [(x_max, y_min, z_max), (x_max, y_max, z_max)],
            [(x_min, y_min, z_min), (x_min, y_min, z_max)],
            [(x_max, y_min, z_min), (x_max, y_min, z_max)],
            [(x_min, y_max, z_min), (x_min, y_max, z_max)],
            [(x_max, y_max, z_min), (x_max, y_max, z_max)]
        ]

        for edge in edges:
            xs, ys, zs = zip(*edge)
            ax1.plot(xs, ys, zs, 'b-', alpha=0.6, linewidth=2)

        # 绘制中心点
        ax1.scatter([center[0]], [center[1]], [center[2]], 
                   c='red', s=100, marker='*', label='Binding Center')

        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        ax1.set_zlabel('Z (Å)')
        ax1.set_title('3D Search Space')
        ax1.legend()

        # 2D投影 - XY平面
        ax2 = fig.add_subplot(222)
        rect_xy = plt.Rectangle((x_min, y_min), box_size[0], box_size[1], 
                              fill=False, edgecolor='blue', linewidth=2)
        ax2.add_patch(rect_xy)
        ax2.plot(center[0], center[1], 'r*', markersize=15, label='Center')
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Y (Å)')
        ax2.set_title('XY Plane')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.axis('equal')

        # 2D投影 - XZ平面
        ax3 = fig.add_subplot(223)
        rect_xz = plt.Rectangle((x_min, z_min), box_size[0], box_size[2], 
                              fill=False, edgecolor='blue', linewidth=2)
        ax3.add_patch(rect_xz)
        ax3.plot(center[0], center[2], 'r*', markersize=15, label='Center')
        ax3.set_xlabel('X (Å)')
        ax3.set_ylabel('Z (Å)')
        ax3.set_title('XZ Plane')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.axis('equal')

        # 2D投影 - YZ平面
        ax4 = fig.add_subplot(224)
        rect_yz = plt.Rectangle((y_min, z_min), box_size[1], box_size[2], 
                              fill=False, edgecolor='blue', linewidth=2)
        ax4.add_patch(rect_yz)
        ax4.plot(center[1], center[2], 'r*', markersize=15, label='Center')
        ax4.set_xlabel('Y (Å)')
        ax4.set_ylabel('Z (Å)')
        ax4.set_title('YZ Plane')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        ax4.axis('equal')

        plt.tight_layout()

        # 保存图片
        plot_file = os.path.join(self.output_dir, 'binding_site_visualization.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Visualization saved: {plot_file}")

        # 不显示图片，直接关闭
        plt.close()

    def plot_binding_energies(self, binding_energies):
        """绘制结合能分布图"""
        if not binding_energies:
            print("❌ No binding energy data to plot")
            return

        modes = [result['mode'] for result in binding_energies]
        affinities = [result['affinity'] for result in binding_energies]

        plt.figure(figsize=(12, 8))

        # 柱状图
        bars = plt.bar(modes, affinities, color='skyblue', edgecolor='navy', alpha=0.7)

        # 标记最佳结果
        best_idx = 0
        bars[best_idx].set_color('gold')
        bars[best_idx].set_edgecolor('darkorange')

        plt.xlabel('Binding Mode')
        plt.ylabel('Binding Affinity (kcal/mol)')
        plt.title('Molecular Docking Binding Affinity Distribution')
        plt.grid(True, alpha=0.3)

        # 添加数值标签
        for i, (mode, affinity) in enumerate(zip(modes, affinities)):
            plt.text(mode, affinity + 0.1, f'{affinity:.1f}', 
                    ha='center', va='bottom', fontweight='bold' if i == 0 else 'normal')

        # 添加基准线
        plt.axhline(y=-7.0, color='green', linestyle='--', alpha=0.7, label='Good Threshold (-7.0)')
        plt.axhline(y=-5.0, color='orange', linestyle='--', alpha=0.7, label='Moderate Threshold (-5.0)')

        plt.legend()
        plt.tight_layout()

        # 保存图片
        plot_file = os.path.join(self.output_dir, 'binding_energies.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Binding energies plot saved: {plot_file}")

        # 不显示图片，直接关闭
        plt.close()

    def generate_pymol_script(self, docking_results_file, center):
        """生成PyMOL可视化脚本"""
        pymol_script = f"""# PyMOL Visualization Script
# Load receptor structure
load {self.receptor_file}, receptor

# Load docking results
load {docking_results_file}, docking_results

# Display receptor as cartoon
show cartoon, receptor
color lightblue, receptor

# Display ligand as sticks
show sticks, docking_results
color by_element, docking_results

# Set background to white
bg_color white

# Show binding site surface
select binding_site, receptor within 5 of docking_results
show surface, binding_site
set transparency, 0.3, binding_site
color yellow, binding_site

# Adjust view
center docking_results
zoom docking_results, 10

# Show hydrogen bonds
distance hbonds, receptor, docking_results, 3.5, mode=2
hide labels, hbonds

# Add binding center marker
pseudoatom center, pos=[{center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f}]
show spheres, center
color red, center

# Save session
save docking_session.pse
"""

        script_file = os.path.join(self.output_dir, 'pymol_visualization.py')
        with open(script_file, 'w') as f:
            f.write(pymol_script)

        print(f"📝 PyMOL script generated: {script_file}")
        print("💡 Usage: Run 'pymol pymol_visualization.py' in the results directory")

    def generate_3dmol_viewer(self, receptor_file, docking_results_file):
        """生成一个使用3Dmol.js的HTML可视化文件"""
        try:
            with open(receptor_file, 'r') as f:
                receptor_pdbqt = f.read()

            with open(docking_results_file, 'r') as f:
                docking_results_pdbqt = f.read()

            # 确保JS字符串是安全的
            receptor_pdbqt_js = receptor_pdbqt.replace('`', '\\`').replace('\\', '\\\\')
            docking_results_pdbqt_js = docking_results_pdbqt.replace('`', '\\`').replace('\\', '\\\\')

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Docking Results Viewer - 3Dmol</title>
    <script src="https://3dmol.org/build/3Dmol-min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 2em; }}
        h1 {{ color: #333; }}
        p {{ color: #555; }}
        #viewer-container {{
            width: 100%;
            max-width: 900px;
            height: 600px;
            position: relative;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>Molecular Docking Visualization</h1>
    <p><b>Receptor:</b> {os.path.basename(receptor_file)}</p>
    <p><b>Ligand Poses:</b> {os.path.basename(docking_results_file)}</p>
    <div id="viewer-container"></div>

    <script>
        (function() {{
            let viewer = $3Dmol.createViewer(document.getElementById('viewer-container'), {{ backgroundColor: 'white' }});

            let receptor_data = String.raw`{receptor_pdbqt_js}`;
            viewer.addModel(receptor_data, 'pdbqt');

            let ligand_data = String.raw`{docking_results_pdbqt_js}`;
            viewer.addModels(ligand_data, 'pdbqt');

            viewer.setStyle({{ hetflag: false }}, {{ cartoon: {{ color: 'spectrum' }} }});
            viewer.setStyle({{ hetflag: true }}, {{ stick: {{}} }});

            viewer.zoomTo();
            viewer.render();
        }})();
    </script>
</body>
</html>
"""
            output_html_file = os.path.join(self.output_dir, '3dmol_viewer.html')
            with open(output_html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"🌐 3Dmol viewer generated: {output_html_file}")

        except Exception as e:
            print(f"❌ Error generating 3Dmol viewer: {e}")

    def run_complete_docking(self):
        """运行完整的对接和可视化流程"""
        print("🎯 Starting complete molecular docking workflow")
        print("=" * 60)

        # 1. 运行对接
        docking_results_file, binding_energies, center, box_size = self.run_docking()

        if docking_results_file and binding_energies:
            # 2. 分析结果
            best_result = self.analyze_results(binding_energies)

            # 3. 可视化结合位点
            print("\n📊 Generating binding site visualization...")
            self.visualize_binding_site(center, box_size)

            # 4. 绘制结合能图
            print("📊 Generating binding energy plot...")
            self.plot_binding_energies(binding_energies)

            # 5. 生成PyMOL脚本
            print("📝 Generating PyMOL script...")
            self.generate_pymol_script(docking_results_file, center)

            # 6. 生成3Dmol HTML查看器
            print("🌐 Generating 3Dmol viewer...")
            self.generate_3dmol_viewer(self.receptor_file, docking_results_file)

            print("\n🎉 Docking and visualization completed!")
            print(f"📁 All results saved in: {self.output_dir}")
            print("\n📋 Generated files:")
            
            for file in sorted(os.listdir(self.output_dir)):
                file_path = os.path.join(self.output_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"   - {file} ({size} bytes)")

            # 返回结果摘要
            return {
                'success': True,
                'best_affinity': best_result['affinity'],
                'num_modes': len(binding_energies),
                'docking_file': docking_results_file,
                'center': center,
                'box_size': box_size
            }

        else:
            print("❌ Docking failed, cannot proceed with analysis")
            return {
                'success': False,
                'error': 'Docking calculation failed'
            }


if __name__ == "__main__":
    try:
        # 创建对接器实例
        docker = VinaDockerWithFiles("./vina")
        
        # 运行完整流程
        result = docker.run_complete_docking()
        
        if result['success']:
            print(f"\n🏆 Best binding affinity: {result['best_affinity']:.2f} kcal/mol")
            print(f"📊 Generated {result['num_modes']} binding modes")
        else:
            print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()