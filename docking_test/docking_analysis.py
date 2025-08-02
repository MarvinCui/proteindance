#!/usr/bin/env python3
"""
分子对接结果分析模块
提取结合能、相互作用数据并生成科学可视化
"""

import os
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path
import pandas as pd

class DockingAnalyzer:
    """分子对接结果分析器"""
    
    def __init__(self, docking_results_file):
        self.docking_file = docking_results_file
        self.binding_data = []
        self.models_data = []
        
    def parse_docking_results(self):
        """解析对接结果文件，提取所有科学数据"""
        print(f"正在分析对接结果: {self.docking_file}")
        
        if not os.path.exists(self.docking_file):
            print(f"错误：找不到对接结果文件 {self.docking_file}")
            return False
            
        try:
            with open(self.docking_file, 'r') as f:
                content = f.read()
            
            # 提取模型数据
            models = re.findall(r'MODEL\s+(\d+)(.*?)ENDMDL', content, re.DOTALL)
            
            for model_num, model_content in models:
                model_data = self._parse_model(int(model_num), model_content)
                if model_data:
                    self.models_data.append(model_data)
                    
            # 排序按结合能
            self.models_data.sort(key=lambda x: x['binding_energy'])
            
            print(f"✓ 成功解析 {len(self.models_data)} 个对接模型")
            return True
            
        except Exception as e:
            print(f"解析对接结果时出错: {e}")
            return False
    
    def _parse_model(self, model_num, model_content):
        """解析单个模型的数据"""
        # 提取VINA结果行
        vina_match = re.search(r'REMARK VINA RESULT:\s*([-+]?\d*\.?\d+)\s*([-+]?\d*\.?\d+)\s*([-+]?\d*\.?\d+)', model_content)
        if not vina_match:
            return None
            
        binding_energy = float(vina_match.group(1))
        rmsd_lb = float(vina_match.group(2))
        rmsd_ub = float(vina_match.group(3))
        
        # 提取其他能量项
        inter_intra_match = re.search(r'REMARK INTER \+ INTRA:\s*([-+]?\d*\.?\d+)', model_content)
        inter_match = re.search(r'REMARK INTER:\s*([-+]?\d*\.?\d+)', model_content)
        intra_match = re.search(r'REMARK INTRA:\s*([-+]?\d*\.?\d+)', model_content)
        unbound_match = re.search(r'REMARK UNBOUND:\s*([-+]?\d*\.?\d+)', model_content)
        
        # 统计原子数量
        atom_lines = re.findall(r'^ATOM\s+\d+', model_content, re.MULTILINE)
        atom_count = len(atom_lines)
        
        # 统计可旋转键数量
        torsion_match = re.search(r'REMARK\s+(\d+)\s+active torsions:', model_content)
        active_torsions = int(torsion_match.group(1)) if torsion_match else 0
        
        return {
            'model': model_num,
            'binding_energy': binding_energy,
            'rmsd_lb': rmsd_lb,
            'rmsd_ub': rmsd_ub,
            'inter_intra': float(inter_intra_match.group(1)) if inter_intra_match else None,
            'inter': float(inter_match.group(1)) if inter_match else None,
            'intra': float(intra_match.group(1)) if intra_match else None,
            'unbound': float(unbound_match.group(1)) if unbound_match else None,
            'atom_count': atom_count,
            'active_torsions': active_torsions
        }
    
    def generate_binding_energy_chart(self, output_file=None):
        """生成结合能柱状图"""
        if not self.models_data:
            print("错误：没有模型数据可供分析")
            return None
            
        if output_file is None:
            output_file = "binding_energies.png"
            
        # 设置matplotlib中文字体和样式
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.style.use('default')
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Molecular Docking Results Analysis', fontsize=16, fontweight='bold')
        
        # 子图1：结合能分析
        models = [data['model'] for data in self.models_data]
        energies = [data['binding_energy'] for data in self.models_data]
        
        # 使用渐变色彩
        colors = plt.cm.RdYlBu_r(np.linspace(0.2, 0.8, len(models)))
        bars1 = ax1.bar(models, energies, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax1.set_xlabel('Docking Model', fontsize=12)
        ax1.set_ylabel('Binding Energy (kcal/mol)', fontsize=12)
        ax1.set_title('Binding Energy by Docking Model', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, energy in zip(bars1, energies):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{energy:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 高亮最佳结合能
        if energies:
            best_idx = energies.index(min(energies))
            bars1[best_idx].set_color('#FF6B6B')
            bars1[best_idx].set_alpha(1.0)
            bars1[best_idx].set_linewidth(2)
        
        # 子图2：RMSD分析
        rmsd_lb = [data['rmsd_lb'] for data in self.models_data]
        rmsd_ub = [data['rmsd_ub'] for data in self.models_data]
        
        x_pos = np.arange(len(models))
        width = 0.35
        
        bars2a = ax2.bar(x_pos - width/2, rmsd_lb, width, label='RMSD Lower Bound', 
                        color='#4ECDC4', alpha=0.8, edgecolor='black', linewidth=0.5)
        bars2b = ax2.bar(x_pos + width/2, rmsd_ub, width, label='RMSD Upper Bound', 
                        color='#45B7D1', alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax2.set_xlabel('Docking Model', fontsize=12)
        ax2.set_ylabel('RMSD (Å)', fontsize=12)
        ax2.set_title('Root Mean Square Deviation Analysis', fontsize=14, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(models)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 添加统计信息文本框
        stats_text = self._generate_statistics_text()
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 结合能分析图表已保存: {output_file}")
        
        return output_file
    
    def generate_energy_decomposition_chart(self, output_file=None):
        """生成能量分解分析图"""
        if not self.models_data:
            return None
            
        if output_file is None:
            output_file = "energy_decomposition.png"
        
        # 筛选有完整能量数据的模型
        complete_models = [model for model in self.models_data 
                          if all(model.get(key) is not None for key in ['inter', 'intra', 'unbound'])]
        
        if not complete_models:
            print("警告：没有完整的能量分解数据")
            return None
        
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        models = [model['model'] for model in complete_models]
        inter_energies = [model['inter'] for model in complete_models]
        intra_energies = [model['intra'] for model in complete_models]
        
        x_pos = np.arange(len(models))
        width = 0.35
        
        bars1 = ax.bar(x_pos - width/2, inter_energies, width, label='Intermolecular Energy', 
                      color='#FF9999', alpha=0.8, edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x_pos + width/2, intra_energies, width, label='Intramolecular Energy', 
                      color='#66B2FF', alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax.set_xlabel('Docking Model', fontsize=12)
        ax.set_ylabel('Energy (kcal/mol)', fontsize=12)
        ax.set_title('Energy Decomposition Analysis', fontsize=16, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(models)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ 能量分解分析图表已保存: {output_file}")
        
        return output_file
    
    def generate_summary_report(self, output_file=None):
        """生成科学分析报告"""
        if not self.models_data:
            return None
            
        if output_file is None:
            output_file = "docking_summary.txt"
        
        best_model = self.models_data[0]  # 已按结合能排序
        
        report = f"""
=== MOLECULAR DOCKING ANALYSIS REPORT ===

1. DOCKING OVERVIEW:
   Total Models Generated: {len(self.models_data)}
   Best Binding Energy: {best_model['binding_energy']:.3f} kcal/mol (Model {best_model['model']})
   Energy Range: {min(m['binding_energy'] for m in self.models_data):.3f} to {max(m['binding_energy'] for m in self.models_data):.3f} kcal/mol

2. BEST BINDING MODEL (Model {best_model['model']}):
   Binding Energy: {best_model['binding_energy']:.3f} kcal/mol
   RMSD Lower Bound: {best_model['rmsd_lb']:.3f} Å
   RMSD Upper Bound: {best_model['rmsd_ub']:.3f} Å
   Active Torsions: {best_model['active_torsions']}
   Atom Count: {best_model['atom_count']}

3. ENERGY DECOMPOSITION (if available):
"""
        
        if best_model.get('inter') is not None:
            report += f"   Intermolecular Energy: {best_model['inter']:.3f} kcal/mol\n"
            report += f"   Intramolecular Energy: {best_model['intra']:.3f} kcal/mol\n"
            report += f"   Unbound Energy: {best_model['unbound']:.3f} kcal/mol\n"
        else:
            report += "   Energy decomposition data not available\n"
        
        report += f"""
4. BINDING AFFINITY INTERPRETATION:
"""
        
        energy = best_model['binding_energy']
        if energy < -8.0:
            affinity = "Very Strong (IC50 < 1 μM)"
        elif energy < -6.0:
            affinity = "Strong (IC50 ~ 1-10 μM)"
        elif energy < -4.0:
            affinity = "Moderate (IC50 ~ 10-100 μM)"
        else:
            affinity = "Weak (IC50 > 100 μM)"
            
        report += f"   Predicted Binding Affinity: {affinity}\n"
        report += f"   Ki estimate: {np.exp(energy * 1000 / (1.987 * 298.15)):.2e} M\n"
        
        report += f"""
5. ALL MODEL RANKING:
   Rank | Model | Binding Energy | RMSD_LB | RMSD_UB
   -----|-------|----------------|---------|--------
"""
        
        for i, model in enumerate(self.models_data, 1):
            report += f"   {i:2d}   |  {model['model']:2d}   |   {model['binding_energy']:8.3f}   |  {model['rmsd_lb']:5.2f}  |  {model['rmsd_ub']:5.2f}\n"
        
        report += f"""
6. STATISTICAL SUMMARY:
   Mean Binding Energy: {np.mean([m['binding_energy'] for m in self.models_data]):.3f} ± {np.std([m['binding_energy'] for m in self.models_data]):.3f} kcal/mol
   Median Binding Energy: {np.median([m['binding_energy'] for m in self.models_data]):.3f} kcal/mol
   
Analysis generated by ProteinDance Docking Pipeline
Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(output_file, 'w') as f:
            f.write(report)
            
        print(f"✓ 科学分析报告已保存: {output_file}")
        return output_file
    
    def _generate_statistics_text(self):
        """生成统计信息文本"""
        if not self.models_data:
            return ""
            
        energies = [m['binding_energy'] for m in self.models_data]
        best_energy = min(energies)
        mean_energy = np.mean(energies)
        std_energy = np.std(energies)
        
        return f"""Statistics:
Best: {best_energy:.2f} kcal/mol
Mean: {mean_energy:.2f} ± {std_energy:.2f}
Models: {len(self.models_data)}"""

    def get_binding_data_for_ui(self):
        """返回用于UI显示的结合数据"""
        if not self.models_data:
            return None
            
        return {
            'best_energy': min(m['binding_energy'] for m in self.models_data),
            'mean_energy': np.mean([m['binding_energy'] for m in self.models_data]),
            'std_energy': np.std([m['binding_energy'] for m in self.models_data]),
            'total_models': len(self.models_data),
            'best_model': self.models_data[0],
            'all_models': self.models_data
        }

def analyze_docking_results(docking_file, output_dir="./analysis_results"):
    """完整的对接结果分析流程"""
    
    print("=== 分子对接结果分析 ===")
    
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    # 初始化分析器
    analyzer = DockingAnalyzer(docking_file)
    
    # 解析结果
    if not analyzer.parse_docking_results():
        return False
    
    # 生成图表
    binding_chart = analyzer.generate_binding_energy_chart(
        os.path.join(output_dir, "binding_energies.png")
    )
    
    energy_decomp_chart = analyzer.generate_energy_decomposition_chart(
        os.path.join(output_dir, "energy_decomposition.png")
    )
    
    # 生成报告
    report_file = analyzer.generate_summary_report(
        os.path.join(output_dir, "docking_analysis_report.txt")
    )
    
    print(f"\n✓ 分析完成！结果保存在: {output_dir}")
    
    return {
        'binding_chart': binding_chart,
        'energy_chart': energy_decomp_chart,
        'report': report_file,
        'data': analyzer.get_binding_data_for_ui()
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python docking_analysis.py <docking_results.pdbqt> [output_dir]")
        sys.exit(1)
    
    docking_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./analysis_results"
    
    result = analyze_docking_results(docking_file, output_dir)
    if result:
        print("\n分析完成!")
    else:
        print("\n分析失败!")