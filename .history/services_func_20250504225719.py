#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""
disease_to_drug.py

------------------

AI全自动药物发现流程：

1) 读取疾病名称 → DeepSeek Chat API 查询潜在蛋白靶点

2) UniProt / PDB / AlphaFold 结构检索 & 下载

3) 口袋预测（本地 P2Rank / 云端 PrankWeb / DoGSiteScorer）

4) 获取候选化合物SMILES

5) AI优化候选化合物结构

6) 分子结构可视化与对接预测

7) 保存所有文件以便后续研究

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

★ 默认路径全部纯 Python + Requests 可直接运行；

★ 需要Brew安装OpenBable，Java17+；

> brew install open-babel

★ 可选云端接口函数已留出 API 位置，按注释填参数即可启用。

★ 可选 Conda安装MGLTools

★ 可选安装 AutoDock Vina：https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.7

"""

from __future__ import annotations

import os
import sys
import json
import time
import textwrap
import subprocess
import tempfile
import shutil
import stat
import logging
import base64
import io
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import requests
import time
import tarfile
import io
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from rdkit.Chem import Descriptors  # 添加这一行
from rdkit.Chem import Lipinski     # 添加这一行
from rdkit.Chem import rdMolDescriptors  # 添加这一行
import re
from pathlib import Path
from typing import Tuple
from shutil import which
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
import py3Dmol
try:
    import py3Dmol
    HAS_PY3DMOL = True
except ImportError:
    HAS_PY3DMOL = False
from chembl_webresource_client.new_client import new_client
from Bio.PDB import PDBList
import traceback
import openai             # pip install openai>=1.2.4
import datetime
import platform
import shutil
from IPython.display import Image, HTML

# Terminal dimensions
TERM_WIDTH = shutil.get_terminal_size().columns
TERM_WIDTH = min(max(TERM_WIDTH, 80), 120)  # Keep between 80 and 120

# ------------------------------------------------------------------
# 日志设置 - 只将INFO及以上级别发送到文件，不打印到控制台
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drug_discovery.log")
    ]
)
logger = logging.getLogger("drug_discovery")

# 设置控制台日志级别更高，只显示警告和错误
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console_handler)

# ------------------------------------------------------------------
# CUI 界面组件
# ------------------------------------------------------------------

# ANSI颜色代码 - 替换黄色为更清晰的颜色
class Colors:
    HEADER = '\033[95m'    # 紫色
    BLUE = '\033[94m'      # 蓝色
    GREEN = '\033[92m'     # 绿色
    CYAN = '\033[96m'      # 青色 - 替代黄色
    RED = '\033[91m'       # 红色
    MAGENTA = '\033[35m'   # 洋红色
    ENDC = '\033[0m'       # 结束颜色
    BOLD = '\033[1m'       # 粗体
    UNDERLINE = '\033[4m'  # 下划线

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印应用标题"""
    title = "AI驱动的药物发现工作流"
    print(f"\n{Colors.HEADER}{Colors.BOLD}" + "=" * TERM_WIDTH + f"{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}" + title.center(TERM_WIDTH) + f"{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}" + "=" * TERM_WIDTH + f"{Colors.ENDC}\n")

    # 显示时间和用户信息
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_name = os.environ.get("USER", os.environ.get("USERNAME", "Unknown"))
    system_info = platform.system() + " " + platform.release()

    info_line = f"⏰ {current_date} | 👤 {user_name} | 💻 {system_info}"
    print(f"{Colors.BLUE}{info_line}{Colors.ENDC}\n")

def print_section(title):
    """打印章节标题"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'▓' * 5} {title} {'▓' * (TERM_WIDTH - len(title) - 7)}{Colors.ENDC}")

def print_subsection(title):
    """打印子章节标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}⬢ {title}{Colors.ENDC}")

def print_step_start(step_name, step_number, total_steps):
    """打印步骤开始"""
    print(f"\n{Colors.CYAN}[{step_number}/{total_steps}] {step_name} 开始...{Colors.ENDC}")

def print_step_complete(step_name, step_number, total_steps):
    """打印步骤完成"""
    print(f"{Colors.GREEN}✓ [{step_number}/{total_steps}] {step_name} 完成{Colors.ENDC}")

def print_ai_choice(choice, explanation):
    """打印AI选择和解释"""
    print(f"\n{Colors.BOLD}AI选择: {Colors.BLUE}{choice}{Colors.ENDC}")
    print(f"{Colors.BOLD}选择理由: {Colors.CYAN}{explanation}{Colors.ENDC}")

def print_progress_bar(iteration, total, prefix='', suffix='', length=30, fill='█'):
    """打印进度条"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration >= total:
        print()

def print_info(message):
    """打印一般信息"""
    print(f"ℹ️ {message}")

def print_warning(message):
    """打印警告"""
    print(f"{Colors.MAGENTA}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    """打印错误"""
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_success(message):
    """打印成功"""
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_detail(label, value):
    """打印详情项目"""
    print(f"{Colors.BOLD}{label}:{Colors.ENDC} {value}")

def print_options(options, header=None):
    """打印选项列表"""
    if header:
        print(f"\n{Colors.BOLD}{header}:{Colors.ENDC}")

    for i, option in enumerate(options, 1):
        print(f"  {Colors.BLUE}{i}.{Colors.ENDC} {option}")

def print_explanation_box(title, explanation):
    """打印带边框的解释框 - 不使用Markdown格式"""
    width = min(TERM_WIDTH - 4, 80)  # 最大宽度
    lines = textwrap.wrap(explanation, width=width)

    print(f"\n{Colors.CYAN}┏{'━' * (width + 2)}┓{Colors.ENDC}")
    print(f"{Colors.CYAN}┃ {Colors.BOLD}{title.center(width)}{Colors.CYAN} ┃{Colors.ENDC}")
    print(f"{Colors.CYAN}┣{'━' * (width + 2)}┫{Colors.ENDC}")

    for line in lines:
        padding = ' ' * (width - len(line))
        print(f"{Colors.CYAN}┃ {Colors.ENDC}{line}{padding} {Colors.CYAN}┃{Colors.ENDC}")

    print(f"{Colors.CYAN}┗{'━' * (width + 2)}┛{Colors.ENDC}")

def show_spinner(seconds, message="处理中"):
    """显示加载动画"""
    spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    start_time = time.time()
    i = 0

    while time.time() - start_time < seconds:
        print(f"\r{message} {spinner[i % len(spinner)]}", end="")
        time.sleep(0.1)
        i += 1

    print("\r" + " " * (len(message) + 2) + "\r", end="")

# ------------------------------------------------------------------
# 分子可视化函数
# ------------------------------------------------------------------

def generate_molecule_image(smiles: str, output_path: Path = None) -> str:
    """生成分子的2D结构图像并返回文件路径"""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            print_error(f"无法从SMILES生成分子: {smiles}")
            return None

        # 添加2D坐标
        mol = Chem.AddHs(mol)
        AllChem.Compute2DCoords(mol)

        # 设置绘图选项 - 修正为正确的访问方式
        drawer = Draw.MolDraw2DCairo(600, 400)
        drawer.SetFontSize(16)

        # 绘制分子
        img = Draw.MolToImage(mol, size=(600, 400), kekulize=True)

        # 保存图像
        if output_path is None:
            output_path = TMP_DIR / f"molecule_{int(time.time())}.png"

        img.save(output_path)
        return str(output_path)

    except Exception as e:
        print_error(f"生成分子结构图失败: {str(e)}")
        logger.error(f"生成分子结构图失败: {str(e)}")
        return None


# 正确的导入语句
from IPython.display import Image, HTML

# 在代码中定义分子ASCII显示函数
def display_molecule_ascii(smiles: str):
    """在终端中显示分子的简单文本表示"""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            print_error(f"无法从SMILES生成分子: {smiles}")
            return

        # 简单显示分子信息
        print_subsection("分子基本信息")
        print(f"{Colors.BLUE}分子式:{Colors.ENDC} {rdMolDescriptors.CalcMolFormula(mol)}")
        print(f"{Colors.BLUE}分子量:{Colors.ENDC} {round(Descriptors.MolWt(mol), 2)}")
        print(f"{Colors.BLUE}氢键受体:{Colors.ENDC} {Lipinski.NumHAcceptors(mol)}")
        print(f"{Colors.BLUE}氢键供体:{Colors.ENDC} {Lipinski.NumHDonors(mol)}")
        print(f"{Colors.BLUE}旋转键:{Colors.ENDC} {Lipinski.NumRotatableBonds(mol)}")

    except Exception as e:
        print_error(f"显示分子信息失败: {str(e)}")
        logger.error(traceback.format_exc())  # 记录完整错误信息


def generate_docking_image(protein_path: str, ligand_smiles: str, pocket_center: tuple,
                          output_path: Path = None):
    """生成蛋白质-配体对接可视化图像"""
    try:
        if not HAS_PY3DMOL:
            print_warning("未安装py3Dmol，无法生成对接可视化。")
            return None

        # 检查是否在Jupyter环境中
        in_jupyter = False
        try:
            from IPython import get_ipython
            in_jupyter = get_ipython() is not None
        except (ImportError, NameError):
            pass

        # 创建配体3D结构
        mol = Chem.MolFromSmiles(ligand_smiles)
        if not mol:
            print_error(f"无法从SMILES生成分子: {ligand_smiles}")
            return None

        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        AllChem.UFFOptimizeMolecule(mol)

        # 保存为临时PDB文件
        ligand_pdb = TMP_DIR / "temp_ligand.pdb"
        Chem.MolToPDBFile(mol, str(ligand_pdb))

        # 在非Jupyter环境中提供替代方案
        if not in_jupyter:
            print_warning("不在交互式Jupyter环境中，生成替代输出...")
            if output_path is None:
                output_path = TMP_DIR / f"docking_info_{int(time.time())}.txt"

            with open(output_path, 'w') as f:
                f.write(f"蛋白质文件: {protein_path}\n")
                f.write(f"配体SMILES: {ligand_smiles}\n")
                f.write(f"结合口袋坐标: {pocket_center}\n")

            print_success(f"已保存对接信息到: {output_path}")
            return str(output_path)

        # 以下代码只在Jupyter环境中执行
        print_info("在Jupyter环境中创建交互式可视化...")

        # 在Jupyter中以单独的单元格执行以下代码
        print("请在Jupyter笔记本的新单元格中执行以下代码以可视化对接结果:")
        print(f"""
import py3Dmol

# 创建可视化
view = py3Dmol.view(width=800, height=600)

# 加载蛋白质
              with open(r"{protein_path}", 'r') as f:
protein_data = f.read()
view.addModel(protein_data, 'pdb')

# 加载配体
              with open(r"{ligand_pdb}", 'r') as f:
ligand_data = f.read()
view.addModel(ligand_data, 'pdb')

# 设置样式
view.setStyle({{'model': 0}}, {{'cartoon': {{'color': 'spectrum'}}}})
view.setStyle({{'model': 1}}, {{'stick': {{'colorscheme': 'cyanCarbon', 'radius': 0.2}}}})

# 突出显示口袋
              x, y, z = {pocket_center}
view.addSphere({{'center': {{'x': x, 'y': y, 'z': z}}, 'radius': 3.0, 'color': 'yellow', 'opacity': 0.5}})

# 设置视图
view.zoomTo()
view.show()
              """)

        # 创建伪输出文件
        if output_path is None:
            output_path = TMP_DIR / f"docking_{int(time.time())}.txt"

        with open(output_path, 'w') as f:
            f.write("对接可视化代码已生成，请在Jupyter笔记本中执行。\n")

        return str(output_path)

    except Exception as e:
        print_error(f"生成对接可视化失败: {str(e)}")
        logger.error(f"生成对接可视化失败: {traceback.format_exc()}")
        return None


# ------------------------------------------------------------------
# 全局配置
# ------------------------------------------------------------------

# 在每次运行前清理临时目录，防止历史数据污染
TMP_DIR = Path(tempfile.gettempdir()) / "drug_flow"
if TMP_DIR.exists():
    shutil.rmtree(TMP_DIR)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# DeepSeek API设置
OPENAI_API_BASE = "https://api.siliconflow.cn/v1"   # DeepSeek Chat 兼容 OpenAI
OPENAI_API_KEY  = "sk-kiuwnsdtlpclsjguvgajhuqdgowypqhmgozbxhhnenucutdp"  # TODO: ←← 在此填入 DeepSeek API Key

openai.api_base = OPENAI_API_BASE
openai.api_key  = OPENAI_API_KEY

HEADERS_JSON = {"Content-Type": "application/json"}
UNIPROT_REST = "https://rest.uniprot.org"

# 全局状态管理 - 用于错误恢复
workflow_state = {
    "disease": None,
    "gene_symbol": None,
    "uniprot_acc": None,
    "structure_path": None,
    "pocket_center": None,
    "smiles_list": None,
    "optimized_smiles": None,
    "molecule_image": None,
    "docking_image": None,
    "error_count": 0,
    "consecutive_errors": 0,  # 连续错误计数
    "last_successful_step": None,
    "decision_explanations": {},  # 存储AI决策解释
    "current_step": 0,
    "total_steps": 7  # 增加了步骤数
}

# ------------------------------------------------------------------
# AI辅助决策函数
# ------------------------------------------------------------------

def ai_make_decision(options: List[str], context: str, question: str) -> Tuple[int, str]:
    """
使用AI来做决策，替代用户手动选择

Args:
options: 选项列表
context: 提供给AI的上下文信息
question: 询问AI的问题

Returns:
Tuple[选择的索引（从0开始）, 决策解释]
    """
    try:
        print_info("AI正在分析最佳选项...")

        # 构建提示语
        prompt = f"""基于以下上下文，从给定选项中选择最佳选项:

上下文信息:
            {context}

            问题: {question}

选项:
            {chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(options)])}

请先回答你选择的选项编号（仅数字，如"2"），然后在新行中详细解释为什么选择该选项（100-150字）。格式如下:

选择: [数字]
原因: [解释]
            """

        # 调用AI API
        show_spinner(2, "AI思考中")
        rsp = openai.ChatCompletion.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        text = rsp["choices"][0]["message"]["content"].strip()

        # 解析选择和解释
        selection_match = re.search(r'选择:\s*(\d+)', text, re.IGNORECASE)
        reason_match = re.search(r'原因:\s*(.*?)(?:\n|$)', text, re.DOTALL)

        explanation = "无解释"
        if reason_match:
            explanation = reason_match.group(1).strip()

        if selection_match:
            selection = int(selection_match.group(1)) - 1  # 转为从0开始的索引
            if 0 <= selection < len(options):
                logger.info(f"AI选择了选项 {selection+1}: {options[selection]}")
                print_ai_choice(options[selection], explanation)
                return selection, explanation

        # 无法解析，返回第一个
        logger.warning(f"AI回答无法解析: '{text}'，默认选第一项")
        print_warning(f"AI分析无法解析，默认选择第一项: {options[0]}")
        return 0, "无法解析AI回答，默认选择"

    except Exception as e:
        logger.error(f"AI决策失败: {str(e)}")
        print_error(f"AI决策失败，默认选择第一项: {options[0]}")
        return 0, f"决策失败: {str(e)}"

def ai_select_best_compound(smiles_list: List[str], disease: str, protein: str, 
                          innovation_level: int = 5, pocket_center: tuple = None) -> Tuple[str, str, str]:
    """
让AI从候选化合物中选择最好的先导化合物，并进行分子优化

Args:
smiles_list: 候选化合物SMILES列表
disease: 疾病名称
protein: 蛋白质名称
innovation_level: 创新度（1-10）
pocket_center: 可选的口袋中心坐标

Returns:
Tuple[最佳SMILES, 优化后的SMILES, 解释]
    """
    try:
        print_info("AI正在分析候选化合物并选择最佳先导化合物...")

        pocket_info = f"结合口袋位于坐标 {pocket_center}" if pocket_center else "未知口袋位置"

        # 根据创新度调整化合物优化策略
        if innovation_level <= 3:
            strategy = """
            优化策略：
            1. 保守改造，基于已知药物骨架
            2. 提高药代动力学性质
            3. 降低毒性和副作用
            4. 提高选择性
            重点是安全性和可预测性。
            """
        elif innovation_level <= 7:
            strategy = """
            优化策略：
            1. 适度创新的分子骨架改造
            2. 引入新的药效团
            3. 平衡创新性和成药性
            4. 考虑新型给药系统
            在现有知识基础上进行创新。
            """
        else:
            strategy = """
            优化策略：
            1. 探索全新分子骨架
            2. 设计多靶点协同作用
            3. 引入新型作用机制
            4. 突破性结构创新
            鼓励大胆创新，开拓新思路。
            """

        # 构建提示语
        prompt = f"""作为药物化学专家，请分析以下候选化合物，为针对{disease}疾病的{protein}靶点选择最佳先导化合物。
        {pocket_info}
        
        创新度要求：{innovation_level}/10
        {strategy}

        候选SMILES列表:
        {chr(10).join([f"{i+1}. {smi}" for i, smi in enumerate(smiles_list)])}

        请执行以下任务:
        1. 选择一个最佳先导化合物（给出SMILES和编号）
        2. 解释为什么选择该化合物（考虑结构特点、药效团、药物化学性质等）
        3. 根据上述创新策略对该化合物进行结构优化，生成新的改进版SMILES
        4. 解释你做的修饰如何提高其作为药物的潜力

        请按以下格式回复：
        选择SMILES编号: [数字]
        选择的SMILES: [完整SMILES]
        选择理由: [100-200字解释]
        优化后的SMILES: [完整SMILES]
        优化解释: [100-200字解释]
        """

        # 调用AI API
        show_spinner(4, "AI分析分子结构中")
        rsp = openai.ChatCompletion.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )

        text = rsp["choices"][0]["message"]["content"].strip()

        # 解析回复
        selected_idx_match = re.search(r'选择SMILES编号:\s*(\d+)', text, re.IGNORECASE)
        selected_smiles_match = re.search(r'选择的SMILES:\s*(.*?)(?:\n|$)', text, re.DOTALL)
        reason_match = re.search(r'选择理由:\s*(.*?)(?:\n|$)', text, re.DOTALL)
        optimized_smiles_match = re.search(r'优化后的SMILES:\s*(.*?)(?:\n|$)', text, re.DOTALL)
        optimization_match = re.search(r'优化解释:\s*(.*?)(?:\n|$)', text, re.DOTALL)

        # 提取值
        selected_idx = int(selected_idx_match.group(1)) if selected_idx_match else 1

        # 首先尝试从AI回复中获取SMILES
        if selected_smiles_match:
            selected_smiles = selected_smiles_match.group(1).strip()
        else:
            # 如果解析失败，使用原始列表中的对应项
            selected_idx = max(1, min(selected_idx, len(smiles_list)))
            selected_smiles = smiles_list[selected_idx - 1]

        # 提取其他信息
        reason = reason_match.group(1).strip() if reason_match else "未提供选择理由"

        if optimized_smiles_match:
            optimized_smiles = optimized_smiles_match.group(1).strip()
        else:
            optimized_smiles = selected_smiles  # 如果没有优化SMILES，使用原始SMILES

        optimization_explanation = optimization_match.group(1).strip() if optimization_match else "未提供优化解释"

        # 验证SMILES有效性
        mol = Chem.MolFromSmiles(optimized_smiles)
        if not mol:
            print_warning(f"AI生成的优化SMILES无效，将使用原始选择的SMILES")
            optimized_smiles = selected_smiles

        # 组合解释
        explanation = f"选择理由: {reason}\n\n优化解释: {optimization_explanation}"

        print_success(f"AI已选择并优化了化合物结构")

        return selected_smiles, optimized_smiles, explanation

    except Exception as e:
        logger.error(f"AI选择化合物失败: {str(e)}")
        print_error(f"AI选择化合物失败，使用第一个化合物: {smiles_list[0]}")
        return smiles_list[0], smiles_list[0], f"选择失败: {str(e)}"

def get_targets_from_deepseek(disease_chinese: str, innovation_level: int = 5, top_k=10) -> List[str]:
    """调用 DeepSeek Chat，返回蛋白候选名列表。创新度从1-10."""

    # 根据创新度调整提示语
    if innovation_level <= 3:
        prompt = f"""列举与{disease_chinese}相关、已有成熟药物的经典靶点蛋白基因符号（仅返回{top_k}个，不要解释）。
                  优先选择已被FDA批准药物验证过的靶点。"""
    elif innovation_level <= 7:
        prompt = f"""列举与{disease_chinese}相关、临床试验阶段或新兴的药物靶点蛋白基因符号（仅返回{top_k}个，不要解释）。
                  包括正在开发中但尚未获批的新型靶点。"""
    else:
        prompt = f"""列举与{disease_chinese}相关的创新性药物靶点蛋白基因符号（仅返回{top_k}个，不要解释）。
                  优先考虑新发现的信号通路、非经典靶点或颠覆性作用机制的靶点。"""

    rsp = openai.ChatCompletion.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    text = rsp["choices"][0]["message"]["content"]

    # 粗略解析：去掉序号等，仅提取字母/数字/下划线
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    proteins = []
    for l in lines:
        # 只保留 A-Z, a-z, 0-9, _ 及 -，去掉其它符号（逗号、句号等）
        token = re.sub(r"[^A-Za-z0-9_-]", "", l.split()[0])
        if 2 <= len(token) <= 12:
            proteins.append(token.upper())

    return proteins[:top_k]

# 修改API类以支持创新度参数
class DrugDiscoveryAPI:
    @staticmethod
    def get_disease_targets(disease: str, innovation_level: int = 5) -> Dict:
        """获取疾病相关靶点"""
        try:
            proteins = get_targets_from_deepseek(disease, innovation_level)
            return {
                "success": True,
                "targets": proteins
            }
        except Exception as e:
            logger.error(f"获取疾病靶点失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def select_best_compound(smiles_list: List[str], disease: str, protein: str, 
                           pocket_center: tuple = None, innovation_level: int = 5) -> Dict:
        """AI选择并优化化合物"""
        try:
            selected, optimized, explanation = ai_select_best_compound(
                smiles_list, disease, protein, innovation_level, pocket_center
            )
            return {
                "success": True,
                "selected_smiles": selected,
                "optimized_smiles": optimized,
                "explanation": explanation
            }
        except Exception as e:
            logger.error(f"AI选择化合物失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    # ...existing code...