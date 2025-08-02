# PyMOL 3D可视化指南

## 方法1: 使用生成的脚本（推荐）

### 步骤1: 进入结果目录
```bash
cd /Users/wenzhenxiong/Documents/DevProj/proteindance/docking_test/docking_results
```

### 步骤2: 启动PyMOL并运行脚本
```bash
# 启动PyMOL（如果已安装）
pymol

# 在PyMOL命令行中运行脚本
run pymol_visualization.py
```

### 或者直接从命令行运行：
```bash
pymol -c pymol_visualization.py
```

## 方法2: 手动加载和可视化

### 步骤1: 启动PyMOL
```bash
pymol
```

### 步骤2: 在PyMOL中手动输入命令
```python
# 加载蛋白质结构
load ../protein_receptor.pdbqt, receptor

# 加载对接结果
load docking_results.pdbqt, docking_results

# 设置蛋白质显示
show cartoon, receptor
color lightblue, receptor

# 设置配体显示
show sticks, docking_results
color by_element, docking_results

# 设置背景
bg_color white

# 显示结合位点表面
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

# 添加结合中心标记
pseudoatom center, pos=[0.32, -0.11, 0.11]
show spheres, center
color red, center

# 保存会话
save docking_session.pse
```

## 方法3: 使用PyMOL图形界面

### 步骤1: 启动PyMOL GUI
```bash
pymol
```

### 步骤2: 通过菜单加载文件
1. **File → Open** → 选择 `../protein_receptor.pdbqt`
2. **File → Open** → 选择 `docking_results.pdbqt`

### 步骤3: 调整显示样式
- 在右侧对象列表中：
  - 点击 **receptor** 旁的 **S** → **cartoon**
  - 点击 **docking_results** 旁的 **S** → **sticks**

### 步骤4: 设置颜色
- 点击 **receptor** 旁的 **C** → **by chain** → **lightblue**
- 点击 **docking_results** 旁的 **C** → **by element**

## 生成的可视化内容

脚本会创建以下可视化效果：

1. **蛋白质结构**: 以卡通模型显示，浅蓝色
2. **配体分子**: 以棍状模型显示，按元素着色
3. **结合位点**: 以半透明黄色表面显示
4. **氢键**: 以虚线显示蛋白质-配体相互作用
5. **结合中心**: 红色球体标记

## 交互操作

### 鼠标操作：
- **左键拖拽**: 旋转分子
- **右键拖拽**: 缩放
- **中键拖拽**: 平移
- **滚轮**: 缩放

### 有用的PyMOL命令：
```python
# 显示不同的结合模式
show sticks, docking_results and model 1  # 显示第1个模式
show sticks, docking_results and model 2  # 显示第2个模式

# 隐藏特定模式
hide everything, docking_results and model 3

# 创建高质量图像
ray 1920, 1080
png high_quality_image.png

# 创建动画
movie.roll 1, 360, 1  # 360度旋转动画
```

## 故障排除

### 问题1: PyMOL未安装
```bash
# macOS
brew install pymol

# 或使用conda
conda install -c conda-forge pymol-open-source
```

### 问题2: 文件路径错误
确保在正确的目录中运行PyMOL：
```bash
cd /Users/wenzhenxiong/Documents/DevProj/proteindance/docking_test/docking_results
```

### 问题3: 文件格式问题
如果PDBQT文件有问题，可以尝试：
```python
# 在PyMOL中
load ../protein_receptor.pdbqt, receptor, format=pdb
```

## 高级可视化选项

### 显示表面静电势：
```python
# 计算表面静电势
util.protein_vacuum_esp(receptor, mode=2)
```

### 创建动画：
```python
# 创建结合模式之间的变换动画
intra_fit docking_results
```

### 保存高质量图像：
```python
# 设置光线追踪
ray 2400, 1800
png publication_quality.png, dpi=300
```

## 预期结果

运行脚本后，您应该看到：
- 蛋白质的3D结构（浅蓝色卡通模型）
- 配体的最佳结合姿态（彩色棍状模型）
- 结合位点的表面（半透明黄色）
- 蛋白质-配体相互作用的氢键（虚线）
- 结合中心的标记（红色球体）

所有9种结合模式都会加载，您可以选择性地显示或隐藏不同的模式进行比较。