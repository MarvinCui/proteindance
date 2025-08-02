#!/usr/bin/env python3
"""
使用现有PDBQT文件进行AutoDock Vina分子对接
"""

import os
import subprocess
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


class VinaDockerWithFiles:
    def __init__(self, vina_executable="./vina"):
        """
        初始化对接器

        Args:
            vina_executable (str): vina可执行文件路径
        """
        self.vina_executable = vina_executable
        self.receptor_file = "protein_structure.pdbqt"
        self.ligand_file = "original_ligand.pdbqt"
        self.output_dir = "./docking_results"

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 检查文件是否存在
        self._check_files()

    def _check_files(self):
        """检查必要的文件是否存在"""
        print("🔍 检查文件...")

        if not os.path.exists(self.receptor_file):
            print(f"❌ 受体文件不存在: {self.receptor_file}")
            return False

        if not os.path.exists(self.ligand_file):
            print(f"❌ 配体文件不存在: {self.ligand_file}")
            return False

        if not os.path.exists(self.vina_executable):
            print(f"❌ Vina可执行文件不存在: {self.vina_executable}")
            return False

        print(f"✅ 受体文件: {self.receptor_file}")
        print(f"✅ 配体文件: {self.ligand_file}")
        print(f"✅ Vina程序: {self.vina_executable}")
        return True

    def create_config_file(self, center, box_size, config_filename="docking_config.txt"):
        """
        创建Vina配置文件

        Args:
            center (tuple): 结合口袋中心坐标 (x, y, z)
            box_size (tuple): 搜索盒子大小 (x, y, z)
            config_filename (str): 配置文件名
        """
        config_path = os.path.join(self.output_dir, config_filename)

        config_content = f"""# AutoDock Vina配置文件
# 受体文件
receptor = {self.receptor_file}

# 配体文件
ligand = {self.ligand_file}

# 搜索空间中心坐标
center_x = {center[0]}
center_y = {center[1]}
center_z = {center[2]}

# 搜索空间大小
size_x = {box_size[0]}
size_y = {box_size[1]}
size_z = {box_size[2]}

# 输出文件
out = {os.path.join(self.output_dir, 'docking_results.pdbqt')}

# 搜索参数
exhaustiveness = 32
num_modes = 9
energy_range = 3
"""

        with open(config_path, 'w') as f:
            f.write(config_content)

        print(f"✅ 创建配置文件: {config_path}")
        print(f"📍 结合口袋中心: {center}")
        print(f"📦 搜索盒子大小: {box_size}")

        return config_path

    def run_docking(self, center=(1.78, 12.68, -0.91), box_size=(20.0, 20.0, 20.0)):
        """
        运行分子对接

        Args:
            center (tuple): 结合口袋中心坐标
            box_size (tuple): 搜索盒子大小
        """
        print("🚀 开始分子对接...")
        print("=" * 60)

        # 创建配置文件
        config_file = self.create_config_file(center, box_size)

        # 构建vina命令
        output_file = os.path.join(self.output_dir, 'docking_results.pdbqt')

        cmd = f"{self.vina_executable} --config {config_file}"

        print(f"🔄 执行命令: {cmd}")
        print("⏳ 对接计算进行中（这可能需要几分钟）...")

        try:
            # 运行对接
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ 对接计算完成!")
                print("\n📊 Vina输出:")
                print(result.stdout)

                # 解析结果
                binding_energies = self._parse_results(result.stdout)

                if os.path.exists(output_file):
                    print(f"✅ 结果文件已保存: {output_file}")
                    return output_file, binding_energies
                else:
                    print("❌ 结果文件未生成")
                    return None, []
            else:
                print("❌ 对接计算失败!")
                print(f"错误信息: {result.stderr}")
                return None, []

        except Exception as e:
            print(f"❌ 执行过程中出错: {e}")
            return None, []

    def _parse_results(self, vina_output):
        """解析Vina输出中的结合能信息"""
        binding_energies = []

        lines = vina_output.split('\n')
        in_results = False

        for line in lines:
            if "mode |   affinity | dist from best mode" in line:
                in_results = True
                continue
            elif in_results and "-----+" in line:
                continue
            elif in_results and line.strip():
                parts = line.split()
                if len(parts) >= 3 and parts[0].isdigit():
                    try:
                        mode = int(parts[0])
                        affinity = float(parts[2])
                        rmsd_lb = float(parts[4]) if len(parts) > 4 else 0.0
                        rmsd_ub = float(parts[5]) if len(parts) > 5 else 0.0
                        binding_energies.append({
                            'mode': mode,
                            'affinity': affinity,
                            'rmsd_lb': rmsd_lb,
                            'rmsd_ub': rmsd_ub
                        })
                    except (ValueError, IndexError):
                        continue
            elif in_results and not line.strip():
                break

        return binding_energies

    def analyze_results(self, binding_energies):
        """分析对接结果"""
        if not binding_energies:
            print("❌ 没有可分析的结果")
            return

        print("\n" + "=" * 60)
        print("📊 对接结果分析")
        print("=" * 60)

        print(f"{'模式':<6} {'结合亲和力':<12} {'RMSD l.b.':<10} {'RMSD u.b.':<10}")
        print("-" * 50)

        for result in binding_energies:
            print(
                f"{result['mode']:<6} {result['affinity']:<12.2f} {result['rmsd_lb']:<10.2f} {result['rmsd_ub']:<10.2f}")

        # 最佳结果分析
        best_result = binding_energies[0]
        best_energy = best_result['affinity']

        print(f"\n🏆 最佳结合姿态:")
        print(f"   模式: {best_result['mode']}")
        print(f"   结合亲和力: {best_energy:.2f} kcal/mol")

        if best_energy < -8.0:
            print("✅ 非常好的结合亲和力!")
        elif best_energy < -7.0:
            print("✅ 较好的结合亲和力!")
        elif best_energy < -5.0:
            print("⚠️  中等结合亲和力")
        else:
            print("❌ 较弱的结合亲和力")

    def visualize_binding_site(self, center=(1.78, 12.68, -0.91), box_size=(20.0, 20.0, 20.0)):
        """可视化结合位点和搜索空间"""
        fig = plt.figure(figsize=(12, 10))

        # 3D图
        ax1 = fig.add_subplot(221, projection='3d')

        # 绘制搜索盒子
        x_min, x_max = center[0] - box_size[0] / 2, center[0] + box_size[0] / 2
        y_min, y_max = center[1] - box_size[1] / 2, center[1] + box_size[1] / 2
        z_min, z_max = center[2] - box_size[2] / 2, center[2] + box_size[2] / 2

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
                    c='red', s=100, marker='*', label='结合口袋中心')

        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        ax1.set_zlabel('Z (Å)')
        ax1.set_title('3D搜索空间可视化')
        ax1.legend()

        # 2D投影 - XY平面
        ax2 = fig.add_subplot(222)
        rect_xy = plt.Rectangle((x_min, y_min), box_size[0], box_size[1],
                                fill=False, edgecolor='blue', linewidth=2)
        ax2.add_patch(rect_xy)
        ax2.plot(center[0], center[1], 'r*', markersize=15, label='结合中心')
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Y (Å)')
        ax2.set_title('XY平面投影')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.axis('equal')

        # 2D投影 - XZ平面
        ax3 = fig.add_subplot(223)
        rect_xz = plt.Rectangle((x_min, z_min), box_size[0], box_size[2],
                                fill=False, edgecolor='blue', linewidth=2)
        ax3.add_patch(rect_xz)
        ax3.plot(center[0], center[2], 'r*', markersize=15, label='结合中心')
        ax3.set_xlabel('X (Å)')
        ax3.set_ylabel('Z (Å)')
        ax3.set_title('XZ平面投影')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.axis('equal')

        # 2D投影 - YZ平面
        ax4 = fig.add_subplot(224)
        rect_yz = plt.Rectangle((y_min, z_min), box_size[1], box_size[2],
                                fill=False, edgecolor='blue', linewidth=2)
        ax4.add_patch(rect_yz)
        ax4.plot(center[1], center[2], 'r*', markersize=15, label='结合中心')
        ax4.set_xlabel('Y (Å)')
        ax4.set_ylabel('Z (Å)')
        ax4.set_title('YZ平面投影')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        ax4.axis('equal')

        plt.tight_layout()

        # 保存图片
        plot_file = os.path.join(self.output_dir, 'binding_site_visualization.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 可视化图已保存: {plot_file}")

        plt.show()

    def plot_binding_energies(self, binding_energies):
        """绘制结合能分布图"""
        if not binding_energies:
            print("❌ 没有结合能数据可绘制")
            return

        modes = [result['mode'] for result in binding_energies]
        affinities = [result['affinity'] for result in binding_energies]

        plt.figure(figsize=(10, 6))

        # 柱状图
        bars = plt.bar(modes, affinities, color='skyblue', edgecolor='navy', alpha=0.7)

        # 标记最佳结果
        best_idx = 0
        bars[best_idx].set_color('gold')
        bars[best_idx].set_edgecolor('darkorange')

        plt.xlabel('结合模式')
        plt.ylabel('结合亲和力 (kcal/mol)')
        plt.title('分子对接结合亲和力分布')
        plt.grid(True, alpha=0.3)

        # 添加数值标签
        for i, (mode, affinity) in enumerate(zip(modes, affinities)):
            plt.text(mode, affinity + 0.1, f'{affinity:.1f}',
                     ha='center', va='bottom', fontweight='bold' if i == 0 else 'normal')

        # 添加基准线
        plt.axhline(y=-7.0, color='green', linestyle='--', alpha=0.7, label='良好阈值 (-7.0)')
        plt.axhline(y=-5.0, color='orange', linestyle='--', alpha=0.7, label='中等阈值 (-5.0)')

        plt.legend()
        plt.tight_layout()

        # 保存图片
        plot_file = os.path.join(self.output_dir, 'binding_energies.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 结合能图已保存: {plot_file}")

        plt.show()

    def generate_pymol_script(self, docking_results_file):
        """生成PyMOL可视化脚本"""
        pymol_script = f"""# PyMOL可视化脚本
# 加载受体结构
load {self.receptor_file}, receptor

# 加载对接结果
load {docking_results_file}, docking_results

# 显示受体为卡通模型
show cartoon, receptor
color lightblue, receptor

# 显示配体为棍状模型
show sticks, docking_results
color by_element, docking_results

# 设置背景为白色
bg_color white

# 显示结合口袋表面
select binding_site, receptor within 5 of docking_results
show surface, binding_site
set transparency, 0.3, binding_site
color yellow, binding_site

# 调整视角
center docking_results
zoom docking_results, 10

# 显示氢键
distance hbonds, receptor, docking_results, 3.5, mode=2
hide labels, hbonds

# 保存会话
save docking_session.pse
"""

        script_file = os.path.join(self.output_dir, 'pymol_visualization.py')
        with open(script_file, 'w') as f:
            f.write(pymol_script)

        print(f"📝 PyMOL脚本已生成: {script_file}")
        print("💡 使用方法: 在PyMOL中运行 'run pymol_visualization.py'")

    def run_complete_docking(self):
        """运行完整的对接和可视化流程"""
        print("🎯 开始完整的分子对接和可视化流程")
        print("=" * 60)

        # 指定的结合口袋坐标
        center = (1.78, 12.68, -0.91)
        box_size = (20.0, 20.0, 20.0)

        # 1. 可视化结合位点
        print("📊 生成结合位点可视化...")
        self.visualize_binding_site(center, box_size)

        # 2. 运行对接
        docking_results_file, binding_energies = self.run_docking(center, box_size)

        if docking_results_file and binding_energies:
            # 3. 分析结果
            self.analyze_results(binding_energies)

            # 4. 绘制结合能图
            self.plot_binding_energies(binding_energies)

            # 5. 生成PyMOL脚本
            self.generate_pymol_script(docking_results_file)

            print("\n🎉 对接和可视化完成!")
            print(f"📁 所有结果保存在: {self.output_dir}")
            print("\n📋 生成的文件:")
            for file in os.listdir(self.output_dir):
                print(f"   - {file}")

        else:
            print("❌ 对接失败，无法进行后续分析")


if __name__ == "__main__":
    # 创建对接器实例
    docker = VinaDockerWithFiles("./vina")

    # 运行完整流程
    docker.run_complete_docking()