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

# 尝试导入PyMOL
try:
    import pymol
    from pymol import cmd
except ImportError:
    print("错误：未找到PyMOL模块。请确保已安装PyMOL。")
    print("安装方法：conda install -c conda-forge pymol-open-source")
    sys.exit(1)

class DockingVisualizer:
    """蛋白质对接可视化类"""
    
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
            
            # 光线追踪渲染（高质量）
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
                pymol.cmd._cmd.pygame.display.update()
                cmd.zoom()
            else:
                # 无头模式，自动退出
                cmd.quit()
                
        except Exception as e:
            print(f"错误: {e}")
            cmd.quit()
            sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PyMOL蛋白质对接可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 无GUI模式（后台运行）
  python pymol_docking_viz.py protein_receptor.pdbqt docking_results.pdbqt
  
  # GUI模式
  python pymol_docking_viz.py protein_receptor.pdbqt docking_results.pdbqt --gui
  
  # 生成动画
  python pymol_docking_viz.py protein_receptor.pdbqt docking_results.pdbqt --movie
  
  # 指定输出目录
  python pymol_docking_viz.py protein_receptor.pdbqt docking_results.pdbqt -o my_output
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
    
    # 创建可视化器并运行
    visualizer = DockingVisualizer(
        args.receptor, 
        args.ligand, 
        args.output,
        args.gui
    )
    
    visualizer.run(create_movie=args.movie)

if __name__ == "__main__":
    main()