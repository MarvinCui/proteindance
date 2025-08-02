#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyMOL蛋白质对接可视化脚本
用于可视化蛋白质受体和对接配体的相互作用
支持GUI模式和无头模式（后台运行）
"""

import os
import sys
import argparse
from pathlib import Path
import tempfile

# 尝试导入PyMOL
try:
    import pymol
    from pymol import cmd
except ImportError:
    print("错误：未找到PyMOL模块。请确保已安装PyMOL。")
    print("安装方法：conda install -c conda-forge pymol-open-source")
    sys.exit(1)

def calculate_protein_center(protein_file):
    """计算蛋白质几何中心坐标"""
    x_coords, y_coords, z_coords = [], [], []
    
    with open(protein_file, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip()) 
                    z = float(line[46:54].strip())
                    x_coords.append(x)
                    y_coords.append(y)
                    z_coords.append(z)
                except:
                    continue
    
    if not x_coords:
        return None
        
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    center_z = sum(z_coords) / len(z_coords)
    
    return center_x, center_y, center_z

def fix_ligand_coordinates(ligand_file, protein_file, output_file=None):
    """
    修复配体坐标，将其移动到蛋白质几何中心附近
    如果配体已经在蛋白质附近（距离<50Å），则不进行修复
    """
    if output_file is None:
        # 创建临时文件
        fd, output_file = tempfile.mkstemp(suffix='.pdbqt', prefix='ligand_fixed_')
        os.close(fd)
    
    # 计算蛋白质中心
    protein_center = calculate_protein_center(protein_file)
    if not protein_center:
        print("警告：无法计算蛋白质中心，使用原始配体文件")
        return ligand_file
    
    # 计算配体中心
    ligand_coords = []
    with open(ligand_file, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip()) 
                    z = float(line[46:54].strip())
                    ligand_coords.append((x, y, z))
                except:
                    continue
    
    if not ligand_coords:
        print("警告：配体文件中没有原子坐标")
        return ligand_file
        
    ligand_center = (
        sum(coord[0] for coord in ligand_coords) / len(ligand_coords),
        sum(coord[1] for coord in ligand_coords) / len(ligand_coords),
        sum(coord[2] for coord in ligand_coords) / len(ligand_coords)
    )
    
    # 计算距离
    distance = ((ligand_center[0] - protein_center[0])**2 + 
                (ligand_center[1] - protein_center[1])**2 + 
                (ligand_center[2] - protein_center[2])**2)**0.5
    
    print(f"蛋白质中心: ({protein_center[0]:.1f}, {protein_center[1]:.1f}, {protein_center[2]:.1f})")
    print(f"配体中心: ({ligand_center[0]:.1f}, {ligand_center[1]:.1f}, {ligand_center[2]:.1f})")
    print(f"距离: {distance:.1f} Å")
    
    # 如果距离太远（>50Å），则进行修复
    if distance > 50:
        print(f"配体距离蛋白质太远 ({distance:.1f} Å > 50 Å)，正在修复坐标...")
        
        # 计算平移向量
        translation = (
            protein_center[0] - ligand_center[0],
            protein_center[1] - ligand_center[1], 
            protein_center[2] - ligand_center[2]
        )
        
        # 应用平移
        with open(ligand_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    try:
                        prefix = line[:30]
                        x = float(line[30:38].strip()) + translation[0]
                        y = float(line[38:46].strip()) + translation[1]
                        z = float(line[46:54].strip()) + translation[2]
                        suffix = line[54:]
                        
                        new_line = f"{prefix}{x:8.3f}{y:8.3f}{z:8.3f}{suffix}"
                        outfile.write(new_line)
                    except:
                        outfile.write(line)
                else:
                    outfile.write(line)
        
        print(f"✓ 配体坐标已修复，保存到: {output_file}")
        return output_file
    else:
        print("配体位置正常，无需修复")
        return ligand_file

class DockingVisualizer:
    """蛋白质对接可视化类 - 基于pymol_final.py的优化实现"""
    
    def __init__(self, receptor_file, ligand_file, output_dir="pymol_outputs", gui=False):
        """
        初始化可视化器
        
        参数:
            receptor_file: 受体蛋白文件路径 (.pdb, .pdbqt)
            ligand_file: 配体文件路径 (.pdb, .pdbqt, .sdf, .mol2)
            output_dir: 输出目录
            gui: 是否显示GUI界面
        """
        self.receptor_file = Path(receptor_file)
        self.ligand_file = Path(ligand_file)
        self.output_dir = Path(output_dir)
        self.gui = gui
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化PyMOL
        if not gui:
            # 无头模式，不显示GUI
            pymol.finish_launching(['pymol', '-c'])
        else:
            # GUI模式
            pymol.finish_launching()
    
    def load_structures(self):
        """加载蛋白质和配体结构"""
        print(f"加载受体蛋白: {self.receptor_file}")
        cmd.load(str(self.receptor_file), "receptor")
        
        print(f"加载配体分子: {self.ligand_file}")
        cmd.load(str(self.ligand_file), "ligand")
        
        # 移除水分子和其他溶剂
        cmd.remove("solvent")
        
    def setup_visualization(self):
        """设置可视化样式"""
        # 设置背景为白色
        cmd.bg_color("white")
        
        # 受体蛋白设置
        cmd.hide("everything", "receptor")
        cmd.show("cartoon", "receptor")
        cmd.show("surface", "receptor")
        cmd.set("surface_color", "gray80", "receptor")
        cmd.set("transparency", 0.7, "receptor")
        
        # 设置蛋白质卡通颜色
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
        
    def create_binding_site_view(self):
        """创建结合位点视图"""
        # 选择配体周围的残基
        cmd.select("binding_site", "receptor within 5 of ligand")
        
        # 显示结合位点的侧链
        cmd.show("sticks", "binding_site")
        cmd.show("lines", "binding_site")
        cmd.set("stick_radius", 0.1, "binding_site")
        
        # 着色结合位点
        cmd.color("cyan", "binding_site")
        
        # 创建氢键
        cmd.distance("hbonds", "ligand", "binding_site", 3.5, mode=2)
        cmd.hide("labels", "hbonds")
        cmd.color("yellow", "hbonds")
        cmd.set("dash_gap", 0.3, "hbonds")
        cmd.set("dash_length", 0.2, "hbonds")
        
    def generate_images(self):
        """生成多个视角的图像"""
        views = [
            ("overview", "全景视图", None),
            ("ligand_focus", "配体聚焦", "ligand"),
            ("binding_site", "结合位点", "binding_site or ligand"),
            ("surface_view", "表面视图", None),
            ("rotated_90", "旋转90度", None),
            ("top_view", "俯视图", None)
        ]
        
        for view_name, description, selection in views:
            print(f"生成{description}...")
            
            if selection:
                cmd.zoom(selection, buffer=5)
            else:
                cmd.zoom("all", buffer=2)
            
            # 特定视角的调整
            if view_name == "rotated_90":
                cmd.rotate("y", 90)
            elif view_name == "top_view":
                cmd.rotate("x", 90)
            elif view_name == "surface_view":
                cmd.set("transparency", 0.3, "receptor")
                cmd.hide("cartoon", "receptor")
            
            # 光线追踪渲染（高质量）- 使用1920x1080分辨率和300 DPI
            output_file = self.output_dir / f"{view_name}.png"
            cmd.png(str(output_file), width=1920, height=1080, dpi=300, ray=1)
            
            # 恢复设置
            if view_name == "surface_view":
                cmd.set("transparency", 0.7, "receptor")
                cmd.show("cartoon", "receptor")
            
            # 重置视角
            if view_name in ["rotated_90", "top_view"]:
                cmd.orient()
        
        print(f"所有图像已保存到: {self.output_dir}")
    
    def save_session(self):
        """保存PyMOL会话文件"""
        session_file = self.output_dir / "docking_session.pse"
        cmd.save(str(session_file))
        print(f"PyMOL会话已保存到: {session_file}")
    
    def create_movie(self, frames=360):
        """创建旋转动画"""
        print("生成旋转动画...")
        
        # 设置电影长度
        cmd.mset(f"1 x{frames}")
        
        # 创建旋转
        cmd.util.mroll(1, frames, 1)
        
        # 保存为GIF或单独的帧
        movie_dir = self.output_dir / "movie_frames"
        movie_dir.mkdir(exist_ok=True)
        
        for i in range(0, frames, 10):  # 每10帧保存一张
            cmd.frame(i + 1)
            frame_file = movie_dir / f"frame_{i:04d}.png"
            cmd.png(str(frame_file), width=800, height=600, ray=0)
        
        print(f"动画帧已保存到: {movie_dir}")
    
    def run(self, create_movie=False):
        """运行完整的可视化流程"""
        try:
            # 加载结构
            self.load_structures()
            
            # 设置可视化
            self.setup_visualization()
            
            # 创建结合位点视图
            self.create_binding_site_view()
            
            # 生成图像
            self.generate_images()
            
            # 保存会话
            self.save_session()
            
            # 创建动画（可选）
            if create_movie:
                self.create_movie()
            
            # 如果是GUI模式，保持窗口打开
            if self.gui:
                print("PyMOL GUI已打开，您可以手动调整视图")
                print("完成后请关闭PyMOL窗口")
                cmd.zoom()
            else:
                # 无头模式，自动退出
                cmd.quit()
            
            return True
                
        except Exception as e:
            print(f"错误: {e}")
            cmd.quit()
            return False

class WebVisualizer:
    """Web-based 3DMol visualization"""
    
    def __init__(self):
        self.protein_file = None
        self.ligand_file = None
        self.output_dir = "."
    
    def set_files(self, protein_file, ligand_file, output_dir="."):
        """Set input files and output directory"""
        self.protein_file = protein_file
        self.ligand_file = ligand_file
        self.output_dir = output_dir
    
    def generate_web_viewer(self):
        """Generate HTML file with 3DMol.js viewer"""
        
        output_file = Path(self.output_dir) / "3dmol_docking_viewer.html"
        
        # Get relative paths for HTML
        protein_rel_path = os.path.relpath(self.protein_file, self.output_dir)
        ligand_rel_path = os.path.relpath(self.ligand_file, self.output_dir)
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Docking Results - 3DMol Viewer</title>
    <script src="https://3dmol.csb.pitt.edu/build/3Dmol-min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f0f0f0;
        }}
        #viewer {{
            width: 100%;
            height: 600px;
            border: 2px solid #ccc;
            border-radius: 5px;
            background: black;
        }}
        .controls {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .controls button {{
            padding: 8px 16px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        .controls button:hover {{
            background: #45a049;
        }}
        .controls button.secondary {{
            background: #2196F3;
        }}
        .controls button.secondary:hover {{
            background: #1976D2;
        }}
        .info {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>Molecular Docking Results</h1>
    
    <div class="info">
        <h3>Visualization Controls:</h3>
        <ul>
            <li><strong>Protein:</strong> Rainbow cartoon representation</li>
            <li><strong>Ligands:</strong> Stick + sphere representation</li>
            <li><strong>Models:</strong> Cyan (Model 1), Yellow (Model 2), Magenta (Model 3)</li>
        </ul>
    </div>
    
    <div class="controls">
        <button type="button" onclick="toggleProtein()">Toggle Protein</button>
        <button type="button" onclick="toggleLigand()">Toggle Ligands</button>
        <button type="button" onclick="resetView()">Reset View</button>
        <button type="button" class="secondary" onclick="focusLigand()">Focus Ligand</button>
        <button type="button" class="secondary" onclick="showAllModels()">Show All Models</button>
        <button type="button" class="secondary" onclick="showModel(1)">Model 1</button>
        <button type="button" class="secondary" onclick="showModel(2)">Model 2</button>
        <button type="button" class="secondary" onclick="showModel(3)">Model 3</button>
    </div>
    
    <div id="viewer"></div>

    <script>
        let viewer;
        let proteinVisible = true;
        let ligandVisible = true;

        async function initViewer() {{
            // Initialize 3DMol viewer
            viewer = $3Dmol.createViewer("viewer", {{
                defaultcolors: $3Dmol.rasmolElementColors
            }});

            try {{
                // Load protein receptor
                const proteinResponse = await fetch('{protein_rel_path}');
                const proteinData = await proteinResponse.text();
                
                viewer.addModel(proteinData, 'pdbqt');
                viewer.setStyle({{model: 0}}, {{
                    cartoon: {{
                        color: 'spectrum'
                    }}
                }});

                // Load docking results - parse all models
                const ligandResponse = await fetch('{ligand_rel_path}');
                const ligandData = await ligandResponse.text();
                
                // Parse individual models from PDBQT format
                const modelRegex = /MODEL\s+(\d+)([\s\S]*?)ENDMDL/g;
                const colors = ['cyan', 'yellow', 'magenta'];
                let modelIndex = 1;
                let match;
                
                while ((match = modelRegex.exec(ligandData)) !== null) {{
                    const modelNumber = parseInt(match[1]);
                    const modelData = match[2];
                    
                    if (modelData.trim()) {{
                        // Add complete model data
                        const completeModelData = `MODEL ${{modelNumber}}
${{modelData}}
ENDMDL`;
                        viewer.addModel(completeModelData, 'pdbqt');
                        
                        // Style each ligand model
                        const colorIndex = (modelNumber - 1) % colors.length;
                        viewer.setStyle({{model: modelIndex}}, {{
                            stick: {{
                                colorscheme: colors[colorIndex],
                                radius: 0.2
                            }},
                            sphere: {{
                                colorscheme: colors[colorIndex],
                                radius: 0.3,
                                alpha: 0.8
                            }}
                        }});
                        
                        console.log(`Loaded MODEL ${{modelNumber}} with ${{colors[colorIndex]}} color`);
                        modelIndex++;
                    }}
                }}

                // Focus and render
                viewer.zoomTo();
                viewer.zoom(1.2);
                viewer.render();
                
                console.log("Visualization loaded successfully");
                
            }} catch (error) {{
                console.error("Error loading structures:", error);
                document.getElementById("viewer").innerHTML = 
                    "<div style='color: white; text-align: center; padding: 50px;'>" +
                    "Error loading molecular structures. Check file paths and formats.</div>";
            }}
        }}

        function toggleProtein() {{
            proteinVisible = !proteinVisible;
            viewer.setStyle({{model: 0}}, proteinVisible ? {{
                cartoon: {{
                    color: 'spectrum'
                }}
            }} : {{}});
            viewer.render();
        }}

        function toggleLigand() {{
            ligandVisible = !ligandVisible;
            
            const colors = ['cyan', 'yellow', 'magenta'];
            for (let i = 1; i < 10; i++) {{
                viewer.setStyle({{model: i}}, ligandVisible ? {{
                    stick: {{
                        colorscheme: colors[(i-1) % colors.length],
                        radius: 0.2
                    }},
                    sphere: {{
                        colorscheme: colors[(i-1) % colors.length],
                        radius: 0.3,
                        alpha: 0.8
                    }}
                }} : {{}});
            }}
            viewer.render();
        }}

        function resetView() {{
            viewer.zoomTo();
            viewer.zoom(1.2);
            viewer.render();
        }}

        function focusLigand() {{
            viewer.zoomTo({{model: [1,2,3]}});
            viewer.zoom(2.0);
            viewer.render();
        }}

        function showAllModels() {{
            const colors = ['cyan', 'yellow', 'magenta'];
            for (let i = 1; i < 10; i++) {{
                viewer.setStyle({{model: i}}, {{
                    stick: {{
                        colorscheme: colors[(i-1) % colors.length],
                        radius: 0.2
                    }},
                    sphere: {{
                        colorscheme: colors[(i-1) % colors.length],
                        radius: 0.3,
                        alpha: 0.8
                    }}
                }});
            }}
            viewer.render();
        }}

        function showModel(modelNumber) {{
            // Hide all ligand models first
            for (let i = 1; i < 10; i++) {{
                viewer.setStyle({{model: i}}, {{}});
            }}
            
            // Show only the selected model
            const colors = ['cyan', 'yellow', 'magenta'];
            const colorIndex = (modelNumber - 1) % colors.length;
            viewer.setStyle({{model: modelNumber}}, {{
                stick: {{
                    colorscheme: colors[colorIndex],
                    radius: 0.2
                }},
                sphere: {{
                    colorscheme: colors[colorIndex],
                    radius: 0.3,
                    alpha: 0.8
                }}
            }});
            
            viewer.zoomTo({{model: modelNumber}});
            viewer.zoom(1.5);
            viewer.render();
            
            console.log(`Showing only MODEL ${{modelNumber}} with ${{colors[colorIndex]}} color`);
        }}

        // Initialize when page loads
        window.onload = initViewer;
    </script>
</body>
</html>'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Generated web viewer: {output_file}")
        return output_file

def visualize_docking_results(protein_file, ligand_file, output_dir="./docking_results", 
                            use_pymol=True, use_web=True, interactive_pymol=False, create_movie=False):
    """Complete visualization pipeline (API wrapper)"""
    
    print("=== Docking Results Visualization (API) ===")
    Path(output_dir).mkdir(exist_ok=True)
    success = True
    
    # 智能修复配体坐标（如果需要）
    print("\n0. 检查配体坐标...")
    fixed_ligand_file = fix_ligand_coordinates(ligand_file, protein_file)
    if fixed_ligand_file != ligand_file:
        print(f"使用修复后的配体文件: {fixed_ligand_file}")
    else:
        print("配体坐标正常，使用原始文件")
    
    # PyMOL visualization
    if use_pymol:
        print("\n1. PyMOL Visualization...")
        try:
            visualizer = DockingVisualizer(
                receptor_file=protein_file,
                ligand_file=fixed_ligand_file,  # 使用修复后的文件
                output_dir=output_dir,
                gui=interactive_pymol
            )
            pymol_result = visualizer.run(create_movie=create_movie)
            if not pymol_result:
                success = False
                print("ERROR: PyMOL visualization failed")
        except Exception as e:
            print(f"ERROR: Exception in PyMOL visualization: {e}")
            import traceback
            print(f"ERROR: Traceback: {traceback.format_exc()}")
            success = False
    
    # Web visualization
    if use_web:
        print("\n2. Web Visualization...")
        try:
            web_viz = WebVisualizer()
            web_viz.set_files(protein_file, fixed_ligand_file, output_dir)  # 使用修复后的文件
            web_viz.generate_web_viewer()
        except Exception as e:
            print(f"ERROR: Exception in web visualization: {e}")
            import traceback
            print(f"ERROR: Traceback: {traceback.format_exc()}")
            success = False
    
    # Scientific data analysis (NEW)
    print("\n3. Scientific Data Analysis...")
    try:
        # Import the analysis module
        from docking_analysis import analyze_docking_results
        
        # Run binding energy analysis
        analysis_result = analyze_docking_results(ligand_file, output_dir)
        
        if analysis_result:
            print("✓ 科学数据分析完成！生成了结合能图表和报告")
        else:
            print("⚠️ 科学数据分析失败，但可视化仍然完成")
            
    except Exception as e:
        print(f"⚠️ 科学数据分析出错: {e}")
        print("可视化仍然完成，但缺少科学分析数据")
            
    if success:
        print(f"\n✓ Complete analysis and visualization finished! Results in: {output_dir}")
    else:
        print(f"\n✗ Visualization completed with errors! Check: {output_dir}")
        
    return success

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PyMOL蛋白质对接可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 无GUI模式（后台运行）
  python docking_visualization.py protein_receptor.pdbqt docking_results.pdbqt
  
  # GUI模式
  python docking_visualization.py protein_receptor.pdbqt docking_results.pdbqt --gui
  
  # 生成动画
  python docking_visualization.py protein_receptor.pdbqt docking_results.pdbqt --movie
  
  # 指定输出目录
  python docking_visualization.py protein_receptor.pdbqt docking_results.pdbqt -o my_output
        """
    )
    
    parser.add_argument("receptor", help="受体蛋白文件 (.pdb, .pdbqt)")
    parser.add_argument("ligand", help="配体文件 (.pdb, .pdbqt, .sdf, .mol2)")
    parser.add_argument("-o", "--output", default="pymol_outputs", 
                       help="输出目录 (默认: pymol_outputs)")
    parser.add_argument("--gui", action="store_true", 
                       help="显示PyMOL GUI界面")
    parser.add_argument("--movie", action="store_true", 
                       help="生成旋转动画")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.receptor):
        print(f"错误：找不到受体文件: {args.receptor}")
        sys.exit(1)
    
    if not os.path.exists(args.ligand):
        print(f"错误：找不到配体文件: {args.ligand}")
        sys.exit(1)
    
    # Use the API function to run the visualization
    visualize_docking_results(
        protein_file=args.receptor,
        ligand_file=args.ligand,
        output_dir=args.output,
        interactive_pymol=args.gui,
        create_movie=args.movie
    )

if __name__ == "__main__":
    main()