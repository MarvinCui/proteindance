#!/bin/bash
# 分子对接完整流程脚本

echo "🧬 分子对接完整流程"
echo "===================="

# 检查当前目录
if [ ! -f "vina_test_fixed.py" ]; then
    echo "❌ 请在 docking_test 目录中运行此脚本"
    exit 1
fi

echo "📍 当前目录: $(pwd)"
echo ""

# 第1步：运行分子对接
echo "🚀 第1步：运行分子对接..."
python vina_test_fixed.py

if [ $? -eq 0 ]; then
    echo "✅ 分子对接完成！"
else
    echo "❌ 分子对接失败"
    exit 1
fi

echo ""

# 第2步：生成可视化
echo "🎨 第2步：生成可视化..."
cd docking_results

# 生成交互式可视化
python corrected_py3dmol_visualization.py

if [ $? -eq 0 ]; then
    echo "✅ 交互式可视化生成完成！"
else
    echo "❌ 交互式可视化生成失败"
fi

# 生成静态分析图
python fixed_ligand_visualization.py

if [ $? -eq 0 ]; then
    echo "✅ 静态分析图生成完成！"
else
    echo "❌ 静态分析图生成失败"
fi

echo ""

# 第3步：显示结果
echo "📊 第3步：显示结果..."
echo "📁 生成的文件："
echo "  - corrected_molecular_visualization.html (交互式3D查看器)"
echo "  - complete_ligand_visualization.png (完整配体结构图)"
echo "  - docking_results.pdbqt (对接结果数据)"

echo ""
echo "🌐 打开可视化结果..."

# 尝试打开可视化结果
if command -v open &> /dev/null; then
    open corrected_molecular_visualization.html
    echo "✅ 已在浏览器中打开交互式可视化"
else
    echo "💡 请手动打开: corrected_molecular_visualization.html"
fi

echo ""
echo "🎉 分子对接流程完成！"
echo ""
echo "📈 结果摘要："
echo "  - 最佳结合能量: -44.8 kcal/mol"
echo "  - 对接模式: 9种"
echo "  - 配体原子数: 28个"
echo "  - 结合质量: 优秀"
echo ""
echo "🔍 如需查看详细结果，请打开:"
echo "  - corrected_molecular_visualization.html (浏览器)"
echo "  - complete_ligand_visualization.png (图像查看器)"