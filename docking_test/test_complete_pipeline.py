#!/usr/bin/env python3
"""
完整管道测试脚本
测试从可视化到科学分析的完整流程
"""

import os
import sys
from pathlib import Path

def test_visualization_with_analysis():
    """测试带科学分析的可视化流程"""
    
    print("=== 测试完整可视化和科学分析流程 ===")
    
    # 输入文件
    protein_file = "./docking_results/protein_receptor.pdbqt"
    ligand_file = "./docking_results/docking_results.pdbqt"
    output_dir = "./test_output"
    
    # 检查输入文件
    if not os.path.exists(protein_file):
        print(f"❌ 蛋白质文件不存在: {protein_file}")
        return False
        
    if not os.path.exists(ligand_file):
        print(f"❌ 配体文件不存在: {ligand_file}")
        return False
    
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # 导入可视化模块
        from docking_visualization import visualize_docking_results
        
        print("\n1. 运行可视化和科学分析...")
        success = visualize_docking_results(
            protein_file=protein_file,
            ligand_file=ligand_file,
            output_dir=output_dir,
            use_pymol=True,
            use_web=True,
            interactive_pymol=False,
            create_movie=False
        )
        
        if not success:
            print("❌ 可视化流程失败")
            return False
        
        print("\n2. 验证生成的文件...")
        
        # 检查生成的文件
        expected_files = [
            "binding_energies.png",      # 科学分析图表
            "energy_decomposition.png",  # 能量分解图表
            "docking_analysis_report.txt",  # 科学报告
            "overview.png",              # PyMOL可视化
            "ligand_focus.png",
            "binding_site.png",
            "3dmol_docking_viewer.html"  # Web查看器
        ]
        
        missing_files = []
        for filename in expected_files:
            filepath = Path(output_dir) / filename
            if filepath.exists():
                print(f"✓ {filename} - 大小: {filepath.stat().st_size} bytes")
            else:
                missing_files.append(filename)
                print(f"❌ {filename} - 缺失")
        
        if missing_files:
            print(f"\n❌ {len(missing_files)} 个文件缺失: {missing_files}")
            return False
        
        print("\n3. 验证科学分析报告内容...")
        
        # 检查科学分析报告
        report_file = Path(output_dir) / "docking_analysis_report.txt"
        with open(report_file, 'r') as f:
            report_content = f.read()
            
        required_sections = [
            "DOCKING OVERVIEW",
            "BEST BINDING MODEL",
            "ENERGY DECOMPOSITION",
            "BINDING AFFINITY INTERPRETATION",
            "ALL MODEL RANKING"
        ]
        
        for section in required_sections:
            if section in report_content:
                print(f"✓ 包含 {section} 部分")
            else:
                print(f"❌ 缺少 {section} 部分")
                return False
        
        print("\n4. 显示科学分析摘要...")
        
        # 导入分析模块获取数据
        from docking_analysis import DockingAnalyzer
        analyzer = DockingAnalyzer(ligand_file)
        
        if analyzer.parse_docking_results():
            data = analyzer.get_binding_data_for_ui()
            if data:
                print(f"✓ 最佳结合能: {data['best_energy']:.3f} kcal/mol")
                print(f"✓ 平均结合能: {data['mean_energy']:.3f} ± {data['std_energy']:.3f} kcal/mol")
                print(f"✓ 总模型数: {data['total_models']}")
                print(f"✓ 最佳模型: Model {data['best_model']['model']}")
        
        print(f"\n✅ 完整测试成功! 所有结果保存在: {output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    print("ProteinDance 分子对接科学分析测试")
    print("=" * 50)
    
    if test_visualization_with_analysis():
        print("\n🎉 所有测试通过！")
        print("\n生成的文件类型:")
        print("📊 binding_energies.png - 结合能分析图表")
        print("⚡ energy_decomposition.png - 能量分解图表") 
        print("📋 docking_analysis_report.txt - 科学分析报告")
        print("🎨 overview.png, ligand_focus.png 等 - PyMOL可视化")
        print("🌐 3dmol_docking_viewer.html - 交互式Web查看器")
        
        print("\n💡 建议: 打开 ./test_output/3dmol_docking_viewer.html 查看交互式3D分子可视化")
        sys.exit(0)
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()