#!/usr/bin/env python3
"""
AutoDock Vina分子对接与PyMOL可视化集成应用
提供Web界面上传蛋白质受体和配体文件，配置对接参数，并可视化结果
"""

import os
import uuid
import time
import json
import shutil
import threading
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适用于Web服务器
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d import Axes3D
import re
import traceback
from pathlib import Path
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory, url_for, redirect

# 尝试导入PyMOL (可能需要特殊安装)
try:
    import pymol
    from pymol import cmd
    PYMOL_AVAILABLE = True
except ImportError:
    print("警告: PyMOL未安装或无法导入。可视化功能将受限。")
    PYMOL_AVAILABLE = False

# 应用配置
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['RESULTS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
app.config['VINA_EXECUTABLE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vina')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB上传限制

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# 保存当前正在进行的任务
active_tasks = {}

class FileValidator:
    """PDBQT文件验证类"""
    
    @staticmethod
    def validate_receptor_file(filepath):
        """
        验证受体蛋白文件格式
        返回: (是否有效, 错误消息)
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # 检查文件是否为空
            if not content.strip():
                return False, "文件为空"
                
            # 检查是否包含ATOM或HETATM行
            if not re.search(r'^(ATOM|HETATM)', content, re.MULTILINE):
                return False, "文件中未找到ATOM或HETATM记录"
                
            # 检查是否包含配体专用的标签，这些不应该出现在受体文件中
            if re.search(r'^(ROOT|BRANCH|TORSDOF)', content, re.MULTILINE):
                return False, "文件包含配体格式标签(ROOT/BRANCH)，这可能不是正确的受体文件"
                
            return True, ""
                
        except Exception as e:
            return False, f"文件读取错误: {str(e)}"
    
    @staticmethod
    def validate_ligand_file(filepath):
        """
        验证配体分子文件格式
        返回: (是否有效, 错误消息)
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # 检查文件是否为空
            if not content.strip():
                return False, "文件为空"
                
            # 检查是否包含必要的PDBQT标签(对于PDBQT格式)
            if filepath.lower().endswith('.pdbqt'):
                if not re.search(r'^ROOT', content, re.MULTILINE):
                    return False, "PDBQT文件缺少ROOT标签"
                    
                if not re.search(r'^TORSDOF', content, re.MULTILINE):
                    return False, "PDBQT文件缺少TORSDOF标签"
                
            # 对于其他格式，至少要有原子信息
            elif not re.search(r'^(ATOM|HETATM)', content, re.MULTILINE):
                return False, "文件中未找到原子记录"
                
            return True, ""
                
        except Exception as e:
            return False, f"文件读取错误: {str(e)}"

class VinaDocker:
    """AutoDock Vina分子对接类"""
    def __init__(self, vina_executable, work_dir):
        """
        初始化对接器

        Args:
            vina_executable (str): vina可执行文件路径
            work_dir (str): 工作目录
        """
        self.vina_executable = vina_executable
        self.work_dir = work_dir
        self.receptor_file = None
        self.ligand_file = None
        self.output_dir = os.path.join(work_dir, "docking_results")

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

    def set_files(self, receptor_file, ligand_file):
        """设置受体和配体文件"""
        self.receptor_file = receptor_file
        self.ligand_file = ligand_file
        return self._check_files()

    def _check_files(self):
        """检查必要的文件是否存在和格式是否正确"""
        print("🔍 Checking files...")

        files_ok = True
        
        if not os.path.exists(self.receptor_file):
            print(f"❌ Receptor file not found: {self.receptor_file}")
            files_ok = False
        else:
            print(f"✅ Receptor file: {self.receptor_file}")
            # 验证受体文件格式
            is_valid, error_msg = FileValidator.validate_receptor_file(self.receptor_file)
            if not is_valid:
                print(f"❌ Receptor file validation failed: {error_msg}")
                files_ok = False

        if not os.path.exists(self.ligand_file):
            print(f"❌ Ligand file not found: {self.ligand_file}")
            files_ok = False
        else:
            print(f"✅ Ligand file: {self.ligand_file}")
            # 验证配体文件格式
            is_valid, error_msg = FileValidator.validate_ligand_file(self.ligand_file)
            if not is_valid:
                print(f"❌ Ligand file validation failed: {error_msg}")
                files_ok = False

        if not os.path.exists(self.vina_executable):
            print(f"❌ Vina executable not found: {self.vina_executable}")
            files_ok = False
        else:
            print(f"✅ Vina executable: {self.vina_executable}")
            # 确保vina可执行
            os.chmod(self.vina_executable, 0o755)

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

    def run_docking(self, center=None, box_size=(20.0, 20.0, 20.0), exhaustiveness=8, num_modes=9, energy_range=3):
        """
        运行分子对接

        Args:
            center (tuple): 结合口袋中心坐标
            box_size (tuple): 搜索盒子大小
            exhaustiveness (int): 搜索彻底程度
            num_modes (int): 生成构象的数量
            energy_range (int): 能量范围
        """
        # 如果没有提供中心，使用配体中心
        if center is None:
            center = self.get_ligand_center()

        print("🚀 Starting molecular docking...")
        print("=" * 60)
        print(f"📍 Docking center: {center}")
        print(f"📦 Search box size: {box_size}")
        print(f"🔍 Exhaustiveness: {exhaustiveness}")
        print(f"🔢 Number of modes: {num_modes}")
        print(f"🔋 Energy range: {energy_range}")

        # 输出文件
        output_file = os.path.join(self.output_dir, 'docking_results.pdbqt')
        log_file = os.path.join(self.output_dir, 'docking_log.txt')
        
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
            "--exhaustiveness", str(exhaustiveness),
            "--num_modes", str(num_modes),
            "--energy_range", str(energy_range),
            "--log", log_file
        ]

        print(f"🔄 Executing command: {' '.join(cmd)}")
        print("⏳ Docking calculation in progress (this may take a few minutes)...")

        try:
            # 运行对接
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

            if result.returncode == 0:
                print("✅ Docking calculation completed!")
                
                # 从日志文件读取输出
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        vina_output = f.read()
                else:
                    vina_output = result.stdout
                
                # 解析结果
                binding_energies = self._parse_results(vina_output)

                if os.path.exists(output_file):
                    print(f"✅ Results saved to: {output_file}")
                    return output_file, binding_energies, center, box_size
                else:
                    print("❌ Output file not generated")
                    return None, [], center, box_size
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                print(f"❌ Docking calculation failed!")
                print(f"Error: {error_msg}")
                
                # 保存错误日志
                error_log = os.path.join(self.output_dir, 'error_log.txt')
                with open(error_log, 'w') as f:
                    f.write(f"Command: {' '.join(cmd)}\n\n")
                    f.write(f"Return code: {result.returncode}\n\n")
                    f.write(f"Stderr:\n{result.stderr}\n\n")
                    f.write(f"Stdout:\n{result.stdout}\n")
                
                return None, [], center, box_size

        except Exception as e:
            print(f"❌ Error during execution: {e}")
            traceback.print_exc()
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
            return None

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
            assessment = "✅ Excellent binding affinity!"
        elif best_energy < -7.0:
            assessment = "✅ Good binding affinity!"
        elif best_energy < -5.0:
            assessment = "⚠️ Moderate binding affinity"
        else:
            assessment = "❌ Weak binding affinity"
            
        print(assessment)

        best_result['assessment'] = assessment
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

        # 关闭图形
        plt.close(fig)
        
        return plot_file

    def plot_binding_energies(self, binding_energies):
        """绘制结合能分布图"""
        if not binding_energies:
            print("❌ No binding energy data to plot")
            return None

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

        # 关闭图形
        plt.close()
        
        return plot_file

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
        .controls {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .btn {{
            padding: 8px 15px;
            margin-right: 5px;
            border: none;
            border-radius: 4px;
            background-color: #2575fc;
            color: white;
            cursor: pointer;
        }}
        .btn:hover {{
            background-color: #1a68e5;
        }}
    </style>
</head>
<body>
    <h1>Molecular Docking Visualization</h1>
    <p><b>Receptor:</b> {os.path.basename(receptor_file)}</p>
    <p><b>Ligand Poses:</b> {os.path.basename(docking_results_file)}</p>
    
    <div class="controls">
        <button id="showSurface" class="btn">显示/隐藏表面</button>
        <button id="showCartoon" class="btn">显示/隐藏卡通</button>
        <button id="showSticks" class="btn">显示/隐藏配体棍状图</button>
        <button id="colorByAtom" class="btn">按元素着色</button>
        <button id="resetView" class="btn">重置视图</button>
    </div>
    
    <div id="viewer-container"></div>

    <script>
        (function() {{
            let viewer = $3Dmol.createViewer(document.getElementById('viewer-container'), {{ backgroundColor: 'white' }});
            let surfaceOn = false;
            let cartoonOn = true;
            let sticksOn = true;

            // 加载受体
            let receptor_data = String.raw`{receptor_pdbqt_js}`;
            let receptorModel = viewer.addModel(receptor_data, 'pdbqt');
            
            // 加载配体
            let ligand_data = String.raw`{docking_results_pdbqt_js}`;
            let ligandModels = viewer.addModels(ligand_data, 'pdbqt');

            // 初始化显示风格
            function setInitialStyles() {{
                // 受体蛋白设置为卡通图
                viewer.setStyle({{model: receptorModel}}, {{cartoon: {{color: 'spectrum'}}}});
                
                // 配体设置为棍状模型
                viewer.setStyle({{hetflag: true}}, {{
                    stick: {{
                        radius: 0.15,
                        colorscheme: 'defaultColor'
                    }},
                    sphere: {{
                        radius: 0.3,
                        colorscheme: 'defaultColor'
                    }}
                }});
                
                // 按元素着色
                viewer.setColorByElement({{hetflag: true}});
                
                viewer.zoomTo();
                viewer.render();
            }}
            
            // 设置初始样式
            setInitialStyles();
            
            // 事件处理
            document.getElementById('showSurface').addEventListener('click', function() {{
                surfaceOn = !surfaceOn;
                if(surfaceOn) {{
                    viewer.addSurface($3Dmol.SurfaceType.VDW, {{
                        opacity: 0.7,
                        color: 'white'
                    }}, {{model: receptorModel}});
                }} else {{
                    viewer.removeSurface();
                }}
                viewer.render();
            }});
            
            document.getElementById('showCartoon').addEventListener('click', function() {{
                cartoonOn = !cartoonOn;
                if(cartoonOn) {{
                    viewer.setStyle({{model: receptorModel}}, {{cartoon: {{color: 'spectrum'}}}});
                }} else {{
                    viewer.setStyle({{model: receptorModel}}, {{cartoon: {{}}}});
                }}
                viewer.render();
            }});
            
            document.getElementById('showSticks').addEventListener('click', function() {{
                sticksOn = !sticksOn;
                if(sticksOn) {{
                    viewer.setStyle({{hetflag: true}}, {{
                        stick: {{
                            radius: 0.15,
                            colorscheme: 'defaultColor'
                        }},
                        sphere: {{
                            radius: 0.3,
                            colorscheme: 'defaultColor'
                        }}
                    }});
                }} else {{
                    viewer.setStyle({{hetflag: true}}, {{
                        line: {{colorscheme: 'defaultColor'}}
                    }});
                }}
                viewer.render();
            }});
            
            document.getElementById('colorByAtom').addEventListener('click', function() {{
                viewer.setColorByElement({{hetflag: true}});
                viewer.render();
            }});
            
            document.getElementById('resetView').addEventListener('click', function() {{
                viewer.zoomTo();
                viewer.render();
            }});
        }})();
    </script>
</body>
</html>
"""
            output_html_file = os.path.join(self.output_dir, '3dmol_viewer.html')
            with open(output_html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"🌐 3Dmol viewer generated: {output_html_file}")
            return output_html_file

        except Exception as e:
            print(f"❌ Error generating 3Dmol viewer: {e}")
            return None

    def run_complete_docking(self, center=None, box_size=(20.0, 20.0, 20.0), 
                           exhaustiveness=8, num_modes=9, energy_range=3):
        """运行完整的对接和可视化流程"""
        print("🎯 Starting complete molecular docking workflow")
        print("=" * 60)

        # 1. 运行对接
        docking_results_file, binding_energies, center, box_size = self.run_docking(
            center=center, box_size=box_size, exhaustiveness=exhaustiveness,
            num_modes=num_modes, energy_range=energy_range
        )

        results = {
            'success': False,
            'files': {},
            'plots': {},
            'binding_energies': binding_energies,
            'center': center,
            'box_size': box_size
        }

        if docking_results_file and binding_energies:
            results['success'] = True
            results['files']['docking_results'] = docking_results_file
            
            # 2. 分析结果
            best_result = self.analyze_results(binding_energies)
            results['best_result'] = best_result
            
            # 3. 可视化结合位点
            print("\n📊 Generating binding site visualization...")
            binding_site_plot = self.visualize_binding_site(center, box_size)
            results['plots']['binding_site'] = binding_site_plot
            
            # 4. 绘制结合能图
            print("📊 Generating binding energy plot...")
            energy_plot = self.plot_binding_energies(binding_energies)
            results['plots']['binding_energies'] = energy_plot
            
            # 5. 生成3Dmol HTML查看器
            print("🌐 Generating 3Dmol viewer...")
            viewer_html = self.generate_3dmol_viewer(self.receptor_file, docking_results_file)
            results['files']['3dmol_viewer'] = viewer_html
            
            print("\n🎉 Docking and visualization completed!")
        else:
            print("❌ Docking failed, cannot proceed with analysis")
            
            # 尝试查找错误日志
            error_log = os.path.join(self.output_dir, 'error_log.txt')
            if os.path.exists(error_log):
                with open(error_log, 'r') as f:
                    error_content = f.read()
                results['error'] = 'Docking calculation failed. Check error log for details.'
                results['error_log'] = error_content
            else:
                results['error'] = 'Docking calculation failed'
            
        return results


class DockingVisualizer:
    """PyMOL蛋白质对接可视化类"""
    
    def __init__(self, receptor_file, ligand_file, output_dir):
        """
        初始化可视化器
        
        参数:
            receptor_file: 受体蛋白文件路径 (.pdb, .pdbqt)
            ligand_file: 配体文件路径 (.pdb, .pdbqt, .sdf, .mol2)
            output_dir: 输出目录
        """
        self.receptor_file = receptor_file
        self.ligand_file = ligand_file
        self.output_dir = output_dir
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
    def run_visualization(self):
        """在无头模式下运行PyMOL可视化"""
        if not PYMOL_AVAILABLE:
            print("⚠️ PyMOL未安装，无法生成高级可视化")
            return None
            
        try:
            # 初始化PyMOL无头模式
            pymol.finish_launching(['pymol', '-c'])
            
            # 加载结构
            cmd.load(str(self.receptor_file), "receptor")
            cmd.load(str(self.ligand_file), "ligand")
            
            # 移除水分子和其他溶剂
            cmd.remove("solvent")
            
            # 设置背景为白色
            cmd.bg_color("white")
            
            # 受体蛋白设置
            cmd.hide("everything", "receptor")
            cmd.show("cartoon", "receptor")
            cmd.show("surface", "receptor")
            cmd.set("surface_color", "gray80", "receptor")
            cmd.set("transparency", 0.7, "receptor")
            cmd.color("slate", "receptor")
            
            # 配体设置
            cmd.hide("everything", "ligand")
            cmd.show("sticks", "ligand")
            cmd.show("spheres", "ligand")
            cmd.set("stick_radius", 0.15, "ligand")
            cmd.set("sphere_scale", 0.25, "ligand")
            
            # 配体着色
            cmd.color("orange", "ligand and elem C")
            cmd.color("blue", "ligand and elem N")
            cmd.color("red", "ligand and elem O")
            cmd.color("yellow", "ligand and elem S")
            cmd.color("white", "ligand and elem H")
            
            # 添加配体周围的网格
            cmd.show("mesh", "ligand")
            cmd.set("mesh_color", "orange", "ligand")
            cmd.set("mesh_width", 0.5)
            
            # 选择配体周围的残基
            cmd.select("binding_site", "receptor within 5 of ligand")
            
            # 显示结合位点的侧链
            cmd.show("sticks", "binding_site")
            cmd.show("lines", "binding_site")
            cmd.set("stick_radius", 0.1, "binding_site")
            cmd.color("cyan", "binding_site")
            
            # 创建氢键
            cmd.distance("hbonds", "ligand", "binding_site", 3.5, mode=2)
            cmd.hide("labels", "hbonds")
            cmd.color("yellow", "hbonds")
            cmd.set("dash_gap", 0.3, "hbonds")
            cmd.set("dash_length", 0.2, "hbonds")
            
            # 生成多个视角的图像
            views = [
                ("overview", "全景视图", None),
                ("ligand_focus", "配体聚焦", "ligand"),
                ("binding_site", "结合位点", "binding_site or ligand"),
                ("surface_view", "表面视图", None)
            ]
            
            image_files = []
            
            for view_name, description, selection in views:
                if selection:
                    cmd.zoom(selection, buffer=5)
                else:
                    cmd.zoom("all", buffer=2)
                
                # 特定视角的调整
                if view_name == "surface_view":
                    cmd.set("transparency", 0.3, "receptor")
                    cmd.hide("cartoon", "receptor")
                
                # 光线追踪渲染（高质量）
                output_file = os.path.join(self.output_dir, f"{view_name}.png")
                cmd.png(str(output_file), width=1200, height=800, dpi=150, ray=1)
                image_files.append(output_file)
                
                # 恢复设置
                if view_name == "surface_view":
                    cmd.set("transparency", 0.7, "receptor")
                    cmd.show("cartoon", "receptor")
            
            # 保存PyMOL会话文件
            session_file = os.path.join(self.output_dir, "docking_session.pse")
            cmd.save(str(session_file))
            
            # 清理PyMOL
            cmd.quit()
            
            return {
                'success': True,
                'images': image_files,
                'session': session_file
            }
            
        except Exception as e:
            print(f"❌ PyMOL visualization error: {e}")
            traceback.print_exc()
            
            # 确保PyMOL正常退出
            try:
                cmd.quit()
            except:
                pass
                
            return {
                'success': False,
                'error': str(e)
            }


# 工具函数
def allowed_file(filename, allowed_extensions=None):
    """检查文件类型是否允许"""
    if allowed_extensions is None:
        allowed_extensions = {'.pdbqt', '.pdb', '.mol2', '.sdf'}
    
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in allowed_extensions

def process_file_upload(files, file_key, destination_folder, allowed_extensions=None):
    """处理文件上传"""
    if file_key not in files:
        return {'success': False, 'error': f'No {file_key} file provided'}
    
    file = files[file_key]
    
    if file.filename == '':
        return {'success': False, 'error': f'No {file_key} file selected'}
    
    if not allowed_file(file.filename, allowed_extensions):
        return {'success': False, 'error': f'Invalid file type for {file_key}'}
    
    # 创建安全文件名
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    filepath = os.path.join(destination_folder, filename)
    
    try:
        # 保存文件
        file.save(filepath)
        return {
            'success': True,
            'filename': filename,
            'original_name': file.filename,
            'filepath': filepath
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_docking_task(task_id, receptor_file, ligand_file, params):
    """异步运行分子对接任务"""
    try:
        # 更新任务状态
        active_tasks[task_id]['status'] = 'running'
        active_tasks[task_id]['progress'] = 10
        active_tasks[task_id]['message'] = '分子对接任务已开始'
        
        # 创建任务工作目录
        work_dir = os.path.join(app.config['RESULTS_FOLDER'], task_id)
        os.makedirs(work_dir, exist_ok=True)
        
        # 创建Vina对接器
        docker = VinaDocker(app.config['VINA_EXECUTABLE'], work_dir)
        
        # 设置文件
        files_valid = docker.set_files(receptor_file, ligand_file)
        
        if not files_valid:
            active_tasks[task_id]['status'] = 'error'
            active_tasks[task_id]['message'] = '文件验证失败，请检查文件格式'
            # 检查是否为受体文件格式问题
            is_valid_receptor, receptor_error = FileValidator.validate_receptor_file(receptor_file)
            is_valid_ligand, ligand_error = FileValidator.validate_ligand_file(ligand_file)
            
            error_details = ""
            if not is_valid_receptor:
                error_details += f"受体文件错误: {receptor_error}\n"
            if not is_valid_ligand:
                error_details += f"配体文件错误: {ligand_error}\n"
                
            active_tasks[task_id]['error_details'] = error_details
            return
            
        active_tasks[task_id]['progress'] = 20
        active_tasks[task_id]['message'] = '文件已设置，准备运行对接'
        
        # 获取参数
        center = (
            float(params.get('center_x', 0)),
            float(params.get('center_y', 0)),
            float(params.get('center_z', 0))
        )
        
        box_size = (
            float(params.get('size_x', 20)),
            float(params.get('size_y', 20)),
            float(params.get('size_z', 20))
        )
        
        exhaustiveness = int(params.get('exhaustiveness', 8))
        num_modes = int(params.get('num_modes', 9))
        energy_range = int(params.get('energy_range', 3))
        
        # 运行完整对接流程
        active_tasks[task_id]['message'] = '运行分子对接中...'
        results = docker.run_complete_docking(
            center=center,
            box_size=box_size,
            exhaustiveness=exhaustiveness,
            num_modes=num_modes,
            energy_range=energy_range
        )
        
        active_tasks[task_id]['progress'] = 80
        
        if results['success']:
            active_tasks[task_id]['message'] = '对接完成，生成PyMOL可视化...'
            
            # 添加更多可视化（如果PyMOL可用）
            pymol_results = None
            if PYMOL_AVAILABLE:
                visualizer = DockingVisualizer(
                    receptor_file,
                    results['files']['docking_results'],
                    os.path.join(work_dir, 'pymol_vis')
                )
                pymol_results = visualizer.run_visualization()
                
                if pymol_results and pymol_results['success']:
                    results['pymol_visualization'] = pymol_results
        else:
            active_tasks[task_id]['message'] = '对接失败，详情请查看日志'
                
        # 完成任务
        active_tasks[task_id]['results'] = results
        active_tasks[task_id]['status'] = 'completed' if results['success'] else 'error'
        active_tasks[task_id]['progress'] = 100
        active_tasks[task_id]['message'] = '任务完成！' if results['success'] else f"对接失败: {results.get('error', '未知错误')}"
        active_tasks[task_id]['completed_at'] = datetime.now().isoformat()
        
        return results
        
    except Exception as e:
        print(f"Task {task_id} failed with error: {e}")
        traceback.print_exc()
        active_tasks[task_id]['status'] = 'error'
        active_tasks[task_id]['message'] = f'任务执行错误: {str(e)}'
        active_tasks[task_id]['error'] = str(e)


# Flask路由
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """处理文件上传"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # 处理受体文件上传
        receptor_result = process_file_upload(request.files, 'receptor', upload_dir)
        if not receptor_result['success']:
            return jsonify({'success': False, 'error': receptor_result['error']}), 400
            
        # 处理配体文件上传
        ligand_result = process_file_upload(request.files, 'ligand', upload_dir)
        if not ligand_result['success']:
            return jsonify({'success': False, 'error': ligand_result['error']}), 400
            
        # 检查文件格式
        is_valid_receptor, receptor_error = FileValidator.validate_receptor_file(receptor_result['filepath'])
        if not is_valid_receptor:
            return jsonify({
                'success': False, 
                'error': f'受体文件格式无效: {receptor_error}',
                'type': 'receptor_format'
            }), 400
            
        is_valid_ligand, ligand_error = FileValidator.validate_ligand_file(ligand_result['filepath'])
        if not is_valid_ligand:
            return jsonify({
                'success': False, 
                'error': f'配体文件格式无效: {ligand_error}',
                'type': 'ligand_format'
            }), 400
            
        # 获取对接参数
        params = {
            'center_x': request.form.get('center_x', '0'),
            'center_y': request.form.get('center_y', '0'),
            'center_z': request.form.get('center_z', '0'),
            'size_x': request.form.get('size_x', '20'),
            'size_y': request.form.get('size_y', '20'),
            'size_z': request.form.get('size_z', '20'),
            'exhaustiveness': request.form.get('exhaustiveness', '8'),
            'num_modes': request.form.get('num_modes', '9'),
            'energy_range': request.form.get('energy_range', '3')
        }
        
        # 创建任务
        active_tasks[task_id] = {
            'id': task_id,
            'status': 'queued',
            'progress': 0,
            'message': '任务已创建，等待处理',
            'created_at': datetime.now().isoformat(),
            'receptor_file': receptor_result['filepath'],
            'receptor_name': receptor_result['original_name'],
            'ligand_file': ligand_result['filepath'],
            'ligand_name': ligand_result['original_name'],
            'params': params
        }
        
        # 异步运行对接任务
        thread = threading.Thread(
            target=run_docking_task,
            args=(task_id, receptor_result['filepath'], ligand_result['filepath'], params)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '文件上传成功，对接任务已创建'
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in active_tasks:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
        
    task = active_tasks[task_id].copy()
    
    # 移除不需要返回的字段
    task.pop('receptor_file', None)
    task.pop('ligand_file', None)
    
    # 构建结果URL
    if task['status'] == 'completed':
        # 添加结果文件的URL
        task['result_urls'] = {}
        
        if 'results' in task and task['results'].get('success'):
            results = task['results']
            
            # 添加绘图URL
            if 'plots' in results:
                task['result_urls']['plots'] = {}
                for plot_name, plot_path in results['plots'].items():
                    if plot_path:
                        relative_path = os.path.relpath(plot_path, app.config['RESULTS_FOLDER'])
                        task['result_urls']['plots'][plot_name] = url_for('get_result_file', path=relative_path)
            
            # 添加3dmol查看器URL
            if 'files' in results and '3dmol_viewer' in results['files']:
                viewer_path = results['files']['3dmol_viewer']
                if viewer_path:
                    relative_path = os.path.relpath(viewer_path, app.config['RESULTS_FOLDER'])
                    task['result_urls']['viewer'] = url_for('get_result_file', path=relative_path)
            
            # 添加PyMOL可视化URL
            if 'pymol_visualization' in results and results['pymol_visualization'].get('success'):
                pymol_vis = results['pymol_visualization']
                task['result_urls']['pymol_images'] = []
                
                for image_path in pymol_vis.get('images', []):
                    relative_path = os.path.relpath(image_path, app.config['RESULTS_FOLDER'])
                    task['result_urls']['pymol_images'].append({
                        'url': url_for('get_result_file', path=relative_path),
                        'name': os.path.basename(image_path)
                    })
        
    return jsonify({'success': True, 'task': task})

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    tasks = []
    for task_id, task_data in active_tasks.items():
        # 只返回基本信息
        tasks.append({
            'id': task_id,
            'status': task_data['status'],
            'progress': task_data['progress'],
            'message': task_data['message'],
            'created_at': task_data['created_at'],
            'receptor_name': task_data.get('receptor_name', ''),
            'ligand_name': task_data.get('ligand_name', '')
        })
        
    return jsonify({'success': True, 'tasks': tasks})

@app.route('/results/<path:path>')
def get_result_file(path):
    """提供结果文件的访问"""
    return send_from_directory(app.config['RESULTS_FOLDER'], path)

@app.route('/task/<task_id>')
def view_task(task_id):
    """查看任务详情页面"""
    return render_template('task.html', task_id=task_id)

@app.route('/tasks')
def view_tasks():
    """查看所有任务页面"""
    return render_template('tasks.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)