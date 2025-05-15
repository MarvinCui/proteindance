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
import openai
from openai import OpenAI

client = OpenAI(
    api_key="sk-kiuwnsdtlpclsjguvgajhuqdgowypqhmgozbxhhnenucutdp",
    base_url="https://api.siliconflow.cn/v1"
)

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


# ------------------------------------------------------------------
# 全局配置
# ------------------------------------------------------------------

# 在每次运行前清理临时目录，防止历史数据污染
TMP_DIR = Path(tempfile.gettempdir()) / "drug_flow"
if TMP_DIR.exists():
    shutil.rmtree(TMP_DIR)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# DeepSeek API设置（OLD）
# OPENAI_API_BASE = "https://api.siliconflow.cn/v1"   # DeepSeek Chat 兼容 OpenAI
# OPENAI_API_KEY  = "sk-kiuwnsdtlpclsjguvgajhuqdgowypqhmgozbxhhnenucutdp"  # TODO: ←← 在此填入 DeepSeek API Key

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
        rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2)

        text = rsp.choices[0].message.content.strip()

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


def ai_select_best_compound(smiles_list: List[str], disease: str, protein: str, pocket_center: tuple = None) -> Tuple[
    str, str, str]:
    """
让AI从候选化合物中选择最好的先导化合物，并进行分子优化

Args:
smiles_list: 候选化合物SMILES列表
disease: 疾病名称
protein: 蛋白质名称
pocket_center: 可选的口袋中心坐标

Returns:
Tuple[最佳SMILES, 优化后的SMILES, 解释]
    """
    try:
        print_info("AI正在分析候选化合物并选择最佳先导化合物...")

        pocket_info = f"结合口袋位于坐标 {pocket_center}" if pocket_center else "未知口袋位置"

        # 构建提示语 - 增加药物化学约束
        prompt = f"""作为药物化学专家，请分析以下候选化合物，为针对{disease}疾病的{protein}靶点选择最佳先导化合物。
            {pocket_info}

候选SMILES列表:
            {chr(10).join([f"{i + 1}. {smi}" for i, smi in enumerate(smiles_list)])}

请执行以下任务:
1. 选择一个最佳先导化合物（注意不要选择SMILES中同时有两个分子的（即通过点号分隔的药物），然后给出SMILES和编号）
2. 解释为什么选择该化合物（考虑结构特点、药效团、药物化学性质等）
3. 对该化合物进行结构优化，生成一个新的改进版SMILES
4. 解释你做的修饰如何提高其作为药物的潜力

优化时必须严格遵守以下药物化学约束:
- 分子量不超过500道尔顿
- 氢键供体数量不超过5个
- 氢键接受体不超过10个
- 脂水分配系数(LogP)不超过5
- 只做少量、精确的结构修饰（1-3处修改）
- 不要添加复杂或大型的官能团
- 避免引入复杂环系统或长链结构
-尽量避免毒性
-使得化合物能够顺利达到位点，不被提前分解

请确保修改后的SMILES代表一个合理的、小分子药物大小的化合物。检查优化后的SMILES是否有任何语法错误，并确认分子结构的合理性。
            """

        # 调用AI API
        show_spinner(4, "AI分析分子结构中")
        rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000)
        # rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-R1",
        # messages=[{"role": "user", "content": prompt}],
        # temperature=0.3,
        # max_tokens=1000)

        text = rsp.choices[0].message.content.strip()

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

        # 强化SMILES验证和优化
        for _ in range(3):  # 最多尝试3次验证和修正
            # 验证SMILES有效性
            mol = Chem.MolFromSmiles(optimized_smiles)
            if not mol:
                print_warning(f"AI生成的优化SMILES无效，尝试修复...")

                # 调用AI再次修复SMILES
                repair_prompt = f"""
以下SMILES字符串有语法错误，无法被RDKit解析。请修复它，保持分子的基本结构不变:

无效SMILES: {optimized_smiles}

原始正确SMILES: {selected_smiles}

请提供修复后的有效SMILES，不要添加任何解释，只返回修复的SMILES字符串。确保修复后的SMILES保持原分子的主要特性和官能团。
                """

                repair_response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V3",
                    messages=[{"role": "user", "content": repair_prompt}],
                    temperature=0.2,
                    max_tokens=200
                )

                fixed_smiles = repair_response.choices[0].message.content.strip()

                # 检查修复的SMILES是否有效
                fixed_mol = Chem.MolFromSmiles(fixed_smiles)
                if fixed_mol:
                    print_success(f"SMILES已修复")
                    optimized_smiles = fixed_smiles
                    mol = fixed_mol
                else:
                    print_warning(f"无法修复SMILES，将使用原始选择的SMILES")
                    optimized_smiles = selected_smiles
                    break

            # 检查药物化学属性
            property_issues = []

            # 分子量检查
            mw = Descriptors.MolWt(mol)
            if mw > 500:
                property_issues.append(f"分子量过高 (MW = {mw:.1f} > 500)")

            # LogP检查
            log_p = Descriptors.MolLogP(mol)
            if log_p > 5.0:
                property_issues.append(f"LogP过高 (LogP = {log_p:.1f} > 5.0)")

            # 氢键供体检查
            hbd = Lipinski.NumHDonors(mol)
            if hbd > 5:
                property_issues.append(f"氢键供体过多 (HBD = {hbd} > 5)")

            # 氢键受体检查
            hba = Lipinski.NumHAcceptors(mol)
            if hba > 10:
                property_issues.append(f"氢键受体过多 (HBA = {hba} > 10)")

            # 原子数量检查
            if mol.GetNumAtoms() > 50:
                property_issues.append(f"原子数过多 (Atoms = {mol.GetNumAtoms()} > 50)")

            # 如果存在问题，尝试修复
            if property_issues:
                issues_text = ", ".join(property_issues)
                print_warning(f"优化的分子存在药物化学问题: {issues_text}，尝试修复...")

                # 调用AI修复药物化学属性
                fix_props_prompt = f"""
我优化的分子存在以下药物化学问题:
                    {issues_text}

                    原始SMILES: {selected_smiles}
                    有问题的SMILES: {optimized_smiles}

请修改分子结构，解决上述问题，同时保持分子的核心骨架和关键官能团。必须严格遵守:
- 分子量不超过500道尔顿
- LogP不超过5.0
- 氢键受体不超过10个
- 氢键供体不超过5个
- 不添加复杂环系统
- 如果SMILES是两个分子（即中间用点号 . 分隔），那么保留是真实药物分子的那一条，剩余的舍去
- 尽量简化结构

只返回修复后的SMILES，不要添加任何解释。
                    """

                fix_response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1",
                    messages=[{"role": "user", "content": fix_props_prompt}],
                    temperature=0.2,
                    max_tokens=200
                )

                fixed_props_smiles = fix_response.choices[0].message.content.strip()

                # 验证修复后的SMILES
                fixed_props_mol = Chem.MolFromSmiles(fixed_props_smiles)
                if fixed_props_mol:
                    # 再次检查药物化学性质
                    new_mw = Descriptors.MolWt(fixed_props_mol)
                    new_logp = Descriptors.MolLogP(fixed_props_mol)
                    new_hbd = Lipinski.NumHDonors(fixed_props_mol)
                    new_hba = Lipinski.NumHAcceptors(fixed_props_mol)

                    if (new_mw <= 500 and new_logp <= 5.0 and new_hbd <= 5 and new_hba <= 10):
                        print_success(f"药物化学性质已修复 (MW: {new_mw:.1f}, LogP: {new_logp:.1f}, HBD: {new_hbd}, HBA: {new_hba})")
                        optimized_smiles = fixed_props_smiles

                        # 更新优化解释
                        optimization_explanation += f"\n\n改进了药物化学性质 (MW: {new_mw:.1f}, LogP: {new_logp:.1f}, HBD: {new_hbd}, HBA: {new_hba})，增加了药物可能性。"
                        break
                    else:
                        print_warning(f"修复后仍有药物化学问题，将再次尝试")
                        optimized_smiles = fixed_props_smiles  # 继续循环尝试修复
                else:
                    print_warning(f"修复后的SMILES无效，将使用原始选择的SMILES")
                    optimized_smiles = selected_smiles
                    break
            else:
                # 没有问题，退出循环
                print_success(f"优化的分子符合所有药物化学要求")
                break

        # 组合解释
        explanation = f"选择理由: {reason}\n\n优化解释: {optimization_explanation}"

        print_success(f"AI已选择并优化了化合物结构")

        return selected_smiles, optimized_smiles, explanation

    except Exception as e:
        logger.error(f"AI选择化合物失败: {str(e)}")
        print_error(f"AI选择化合物失败，使用第一个化合物: {smiles_list[0]}")
        return smiles_list[0], smiles_list[0], f"选择失败: {str(e)}"


def ai_explain_results(workflow_state: Dict[str, Any]) -> str:
    """生成对结果的AI解释 - 无Markdown格式"""
    try:
        if not workflow_state.get("disease") or not workflow_state.get("gene_symbol"):
            return "无足够信息生成解释"

        print_info("正在生成科学解释...")

        prompt = f"""
请对以下药物发现过程给出专业的科学解释:

            - 目标疾病: {workflow_state['disease']}
            - 选定靶点蛋白: {workflow_state['gene_symbol']}
            - UniProt ID: {workflow_state.get('uniprot_acc', '未知')}
            - 蛋白质结构来源: {'AlphaFold预测' if str(workflow_state.get('structure_path', '')).endswith('_AF.pdb') else 'PDB实验结构'}
            - 识别到的口袋坐标: {workflow_state.get('pocket_center', '未知')}
            - 候选化合物数量: {len(workflow_state.get('smiles_list', [])) if workflow_state.get('smiles_list') else '未知'}
            - 优化后的化合物SMILES: {workflow_state.get('optimized_smiles', '未知')}

请提供:
1. 该蛋白在疾病中的作用机制简介
2. 这个蛋白质结构的特点及其与药物设计的关系
3. 对于识别到的蛋白口袋的药物化学评价
4. 对优化后的化合物及其作用机制的评价
5. 后续药物开发的科学建议

用中文回答，专业但通俗易懂，不要使用Markdown格式，300-500字。
            """

        show_spinner(3, "生成科学解释中")
        rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
                                             messages=[{"role": "user", "content": prompt}],
                                             temperature=0.7,
                                             max_tokens=1024)

        explanation = rsp.choices[0].message.content.strip()
        # 移除可能的Markdown语法
        explanation = explanation.replace('#', '').replace('*', '').replace('_', '')
        return explanation

    except Exception as e:
        logger.error(f"生成AI解释失败: {str(e)}")
        return "无法生成AI解释，请检查网络连接或API密钥设置。"

def natural_language_input(prompt: str, default_value: str = None, validator: Callable = None) -> str:
    """
处理自然语言输入，支持默认值和输入验证

Args:
prompt: 提示语
default_value: 默认值，如果用户输入为空
validator: 验证函数，返回True表示有效输入

Returns:
用户输入或默认值
    """
    full_prompt = f"{Colors.BOLD}{prompt}{Colors.ENDC} " + (f"[{Colors.BLUE}默认: {default_value}{Colors.ENDC}]" if default_value else "")
    while True:
        user_input = input(full_prompt + ": ").strip()

        if not user_input and default_value:
            return default_value

        if not validator or validator(user_input):
            return user_input

        print_warning("输入无效，请重新输入。")

# ------------------------------------------------------------------
# 错误恢复与状态管理
# ------------------------------------------------------------------

class WorkflowError(Exception):
    """工作流错误基类，支持恢复"""
    def __init__(self, message, step=None, recoverable=True):
        super().__init__(message)
        self.step = step
        self.recoverable = recoverable

def should_prompt_user() -> bool:
    """判断是否应该提示用户干预"""
    # 连续错误超过2次时提示用户干预
    return workflow_state["consecutive_errors"] >= 2

def safe_execute(func, error_msg, step_name=None, recoverable=True, max_retries=2):
    """安全执行函数，处理错误并支持恢复"""
    retry_count = 0

    while retry_count <= max_retries:
        try:
            result = func()
            workflow_state["last_successful_step"] = step_name
            workflow_state["consecutive_errors"] = 0  # 重置连续错误计数
            return result

        except Exception as e:
            retry_count += 1
            workflow_state["error_count"] += 1
            workflow_state["consecutive_errors"] += 1

            logger.error(f"{error_msg} (尝试 {retry_count}/{max_retries+1}): {str(e)}")
            logger.debug(traceback.format_exc())

            if retry_count > max_retries:
                if should_prompt_user() and recoverable:
                    print_error(f"\n连续遇到错误，需要您的帮助: {error_msg}")
                    if input("是否继续尝试? [Y/n]: ").lower().startswith('n'):
                        raise WorkflowError(str(e), step_name, False)
                    workflow_state["consecutive_errors"] = 0  # 重置计数
                    return None  # 让调用者决定下一步操作
                elif not recoverable:
                    raise WorkflowError(str(e), step_name, False)
                else:
                    print_warning(f"自动跳过错误步骤: {error_msg}")
                    return None

            # 重试前等待
            wait_time = retry_count * 2  # 递增等待时间
            print_warning(f"发生错误: {str(e)[:100]}... 将在{wait_time}秒后重试")
            time.sleep(wait_time)

# ------------------------------------------------------------------
# 1. DeepSeek Chat 获得疾病→蛋白靶点
# ------------------------------------------------------------------

def get_targets_from_deepseek(disease_chinese: str, top_k=10, max_attempts=3) -> List[str]:
    """调用 DeepSeek Chat，返回蛋白候选名列表，增强型错误处理版本"""

    attempt = 0
    valid_proteins = []

    while attempt < max_attempts and not valid_proteins:
        attempt += 1

        if attempt == 1:
            prompt = f"列举与{disease_chinese}相关、可作为药物靶点的蛋白基因符号（仅返回{top_k}个以内，不要解释）。"
        else:
            prompt = f"""之前未能获取到有效的蛋白基因符号。请重新列举与{disease_chinese}相关的蛋白基因符号。

要求:
1. 严格使用标准蛋白质/基因命名规范（如EGFR, TP53, BRAF等）
2. 每行一个基因符号
3. 不要包含数字作为单独的条目
                4. 返回{top_k}个最相关的靶点
5. 确保每个符号是真实的蛋白质或基因
6. 不要添加解释，只返回基因符号列表
                """

        print_info(f"正在尝试获取蛋白靶点（尝试 {attempt}/{max_attempts}）...")

        try:
            rsp = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            text = rsp.choices[0].message.content

            # 解析出蛋白列表
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            candidates = []

            for l in lines:
                # 提取可能的蛋白/基因名
                # 先尝试获取行首的词（可能有序号）
                parts = l.split(None, 1)
                token = parts[0]

                # 去除序号如 "1." 或 "1)"
                if re.match(r'^\d+[.)]', token):
                    if len(parts) > 1:
                        token = parts[1].split()[0]
                    else:
                        continue

                # 清理标点符号，只保留字母、数字和特定标点
                token = re.sub(r"[^A-Za-z0-9_-]", "", token)

                # 验证格式 - 至少有一个字母，长度在合理范围内
                if re.search(r'[A-Za-z]', token) and 2 <= len(token) <= 12:
                    candidates.append(token.upper())

            # 验证结果 - 确保不是纯数字且符合基因命名规范
            valid_proteins = [p for p in candidates if not p.isdigit() and re.match(r'^[A-Z][A-Z0-9_-]*$', p)]

            # 如果获取到有效结果，返回
            if valid_proteins:
                if attempt > 1:
                    print_success(f"在第{attempt}次尝试后成功获取有效的蛋白靶点")
                return valid_proteins[:top_k]
            else:
                print_warning(f"获取到的结果无效，将重试（{attempt}/{max_attempts}）")

        except Exception as e:
            logger.error(f"获取靶点失败 (尝试 {attempt}/{max_attempts}): {str(e)}")
            print_warning(f"API调用出现错误: {str(e)[:100]}...")
            time.sleep(2)  # 短暂延迟后重试

    # 如果多次尝试后仍无有效结果，返回一些常见靶点作为备选
    if not valid_proteins:
        print_warning("无法获取有效的蛋白靶点，使用常见靶点作为备选")
        default_proteins = ["EGFR", "TP53", "BRAF", "HER2", "VEGF", "TNF", "IL6", "ACE2", "PARP1", "KRAS"]
        return default_proteins[:top_k]

    return valid_proteins[:top_k]


# ------------------------------------------------------------------
# 2. UniProt → 获取 Accession + 结构条目
# ------------------------------------------------------------------

def search_uniprot(gene_symbol: str, organism_id="9606") -> List[Dict]:
    """返回 [{'acc': 'P31645', 'name': 'Sodium‑dependent serotonin transporter'}, ...]"""
    url = (UNIPROT_REST +
           f"/uniprotkb/search?query=(gene_exact:{gene_symbol}+AND+organism_id:{organism_id})"
           "&fields=accession,protein_name&format=json&size=10")

    res = requests.get(url, timeout=30)
    res.raise_for_status()

    data = res.json().get("results", [])
    hits = []

    for d in res.json().get("results", []):
        acc = d["primaryAccession"]
        desc = d.get("proteinDescription", {})

        if "recommendedName" in desc:
            name = desc["recommendedName"]["fullName"]["value"]
        elif "submissionNames" in desc and desc["submissionNames"]:
            name = desc["submissionNames"][0]["fullName"]["value"]
        elif "alternativeNames" in desc and desc["alternativeNames"]:
            name = desc["alternativeNames"][0]["fullName"]["value"]
        else:
            name = "(no name)"

        hits.append({"acc": acc, "name": name})

    return hits

def get_pdb_ids_for_uniprot(accession: str, max_ids=10) -> List[str]:
    """使用 RCSB Search API 通过 UniProtID 找 PDB 代码。"""
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute":
                    "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": accession,
            },
        },
        "return_type": "entry",
        "request_options": {"return_all_hits": True},
    }

    url = "https://search.rcsb.org/rcsbsearch/v2/query"
    res = requests.post(url, headers=HEADERS_JSON, data=json.dumps(query), timeout=30)
    res.raise_for_status()

    ids = [it["identifier"] for it in res.json().get("result_set", [])]
    return ids[:max_ids]

def download_pdb(pdb_id: str, dest_dir=TMP_DIR) -> Path:
    pdb_list = PDBList()
    fname = pdb_list.retrieve_pdb_file(pdb_id, file_format="pdb", pdir=str(dest_dir))

    # Biopython 会存 gz → 解压
    if fname.endswith(".gz"):
        import gzip, shutil as sh
        out = dest_dir / f"{pdb_id}.pdb"
        with gzip.open(fname, "rb") as fin, open(out, "wb") as fout:
            sh.copyfileobj(fin, fout)
        return out

    return Path(fname)

def download_alphafold(uniprot_acc: str, dest_dir=TMP_DIR) -> Path | None:
    # 确保写入目录存在
    dest_dir.mkdir(parents=True, exist_ok=True)

    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_acc}-F1-model_v4.pdb"
    out = dest_dir / f"{uniprot_acc}_AF.pdb"

    r = requests.get(url, stream=True)
    if r.status_code == 200 and int(r.headers.get("Content-Length", 0)) > 1000:
        with open(out, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return out

    return None


def get_pdb_ids_for_gene(gene_symbol: str, max_ids=10):
    query = {
        "query": {
            "type":"terminal","service":"text",
            "parameters":{"value":gene_symbol,"attribute":"rcsb_entity_source_organism.ncbi_gene_name.value"}
        },
        "return_type":"entry","request_options":{"return_all_hits":True}
    }

    res = requests.post("https://search.rcsb.org/rcsbsearch/v2/query",
                        headers=HEADERS_JSON, data=json.dumps(query), timeout=30)
    res.raise_for_status()

    return [x["identifier"] for x in res.json().get("result_set", [])][:max_ids]

# ------------------------------------------------------------------
# 3. 口袋预测（默认本地 P2Rank；可选云端 PrankWeb）
# ------------------------------------------------------------------

def run_p2rank(pdb_path: Path, prank_bin: str | None = None) -> List[Dict]:
    """
调用 P2Rank >=2.4 二进制 prank 预测口袋。

支持：
1. candidates 列表中自动查找项目目录下的 p2rank/prank 或用户主目录下的 p2rank/prank
2. $P2RANK_BIN 环境变量
3. PATH 中 which("prank")
4. prank_bin 参数

返回 [{'center': (x,y,z), 'score': s}, ...]，按 score 降序。
    """
    print_subsection("P2Rank 本地口袋预测")

    # 1) 优先在项目目录或 HOME 下找 p2rank/prank
    candidates = [Path.cwd() / "p2rank/prank", Path.home() / "p2rank/prank"]
    bin_path = None

    for c in candidates:
        if c.exists() and c.is_file():
            bin_path = c
            break

    # 2) 再试环境变量
    if not bin_path:
        env = os.getenv("P2RANK_BIN")
        if env and Path(env).exists():
            bin_path = Path(env)

    # 3) 再试 which
    if not bin_path:
        w = which("prank")
        if w:
            bin_path = Path(w)

    # 4) 最后用传入的 prank_bin
    if not bin_path and prank_bin:
        cand = Path(prank_bin).expanduser()
        if cand.exists():
            bin_path = cand

    if not bin_path:
        raise FileNotFoundError(
            f"未找到 P2Rank 可执行文件。候选路径：{candidates}，"
            "环境变量 P2RANK_BIN，或 PATH 中的 prank。"
        )

    # 5) 执行预测
    out_dir = TMP_DIR / f"{pdb_path.stem}_p2rank"
    cmd = [str(bin_path), "predict", "-f", str(pdb_path), "-o", str(out_dir)]

    print_info("正在进行结构分析和口袋预测...")

    # 使用subprocess.DEVNULL来隐藏命令行输出
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True
    )

    # 展示处理进度动画
    while process.poll() is None:
        show_spinner(0.5, "结构分析中")

    # 检查执行结果
    if process.returncode != 0:
        stderr = process.stderr.read()
        raise RuntimeError(f"P2Rank执行失败: {stderr}")

    # 6) 读取 CSV 并规范化列名
    csv_file = next(out_dir.glob("*_predictions.csv"))
    df = pd.read_csv(csv_file)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"\s+", "_", regex=True)
        .str.lower()
    )

    # 7) 提取 pockets
    pockets: List[Dict] = []
    for _, row in df.iterrows():
        x = row["center_x"]
        y = row["center_y"]
        z = row["center_z"]

        # 有些版本列名叫 score，有些叫 ligandability_score
        score = row.get("score", row.get("ligandability_score"))

        pockets.append({"center": (float(x), float(y), float(z)),
                        "score": float(score)})

    # 8) 返回按 score 降序排列的口袋
    sorted_pockets = sorted(pockets, key=lambda p: p["score"], reverse=True)

    print_success(f"成功预测出 {len(sorted_pockets)} 个潜在药物结合口袋")
    return sorted_pockets

def run_dogsite_api(pdb_path: Path) -> List[Dict]:
    """
调 ProteinsPlus REST，返回 [{'center': (x,y,z), 'score': druggability}, ...]
文档: https://proteins.plus/api/v2/docs
    """
    print_subsection("DoGSiteScorer 在线口袋预测")

    url_job = "https://proteins.plus/api/v2/dogsite/start/"
    files = {"file": open(pdb_path, "rb")}

    r = requests.post(url_job, files=files, timeout=60)
    r.raise_for_status()

    job_id = r.json()["job_id"]
    print_info(f"作业已提交，ID: {job_id}")

    # 轮询
    url_stat = f"https://proteins.plus/api/v2/dogsite/status/{job_id}/"
    url_res  = f"https://proteins.plus/api/v2/dogsite/result/{job_id}/"

    print_info("等待在线服务器计算结果...")
    for i in range(60):
        if i > 0 and i % 6 == 0:
            elapsed_time = i * 5
            print_info(f"仍在计算中...已等待 {elapsed_time} 秒")

        status_resp = requests.get(url_stat)
        status = status_resp.json()["status"]

        if status == "FINISHED":
            print_success("计算完成，获取结果...")
            data = requests.get(url_res).json()

            pockets = []
            for p in data["pockets"]:
                x, y, z = p["center"]
                pockets.append({"center": (x, y, z),
                                "score": p["druggability_score"]})

            # 分数高→更可成药；排序后返回
            sorted_pockets = sorted(pockets, key=lambda x: x["score"], reverse=True)
            print_success(f"成功预测出 {len(sorted_pockets)} 个潜在药物结合口袋")
            return sorted_pockets

        elif status == "FAILED":
            error_msg = status_resp.json().get("error_msg", "未知错误")
            raise RuntimeError(f"DoGSite计算失败: {error_msg}")

        elif status == "RUNNING":
            print_progress_bar(i % 10, 10, prefix="计算中", suffix="请耐心等待", length=20)

        time.sleep(5)

    raise RuntimeError("DoGSite 预测超时，服务器可能繁忙，请稍后再试")

# ------------------------------------------------------------------
# 4. 虚拟筛选（获取SMILES部分）
# ------------------------------------------------------------------

def fetch_chembl_smiles(uniprot_acc: str, max_hits: int = 10) -> List[str]:
    """
通过 ChEMBL REST API 拉取该 UniProt 蛋白的 IC50 抑制化合物 SMILES，
直接访问 /activity 而不是 /activity.json。
    """
    print_info(f"正在从ChEMBL数据库查询与UniProt:{uniprot_acc}相关的活性化合物...")

    # 1) 先用 chembl_webresource_client 或 requests 获取 target_chembl_id
    # （假设你保留原来的 new_client 调用，这里只示例 activity 部分）
    from chembl_webresource_client.new_client import new_client
    res = new_client.target.filter(
        target_components__accession=uniprot_acc
    ).only(["target_chembl_id"])
    if not res:
        print_warning(f"ChEMBL 中未找到 UniProt {uniprot_acc} 对应的蛋白靶点记录")
        return []
    chembl_id = res[0]["target_chembl_id"]
    print_info(f"找到ChEMBL靶点: {chembl_id}")

    # 2) 用 requests 调用 /activity 接口
    print_info("正在检索IC50活性数据 (通过 /activity 接口)...")
    show_spinner(2, "检索活性数据")
    url = "https://www.ebi.ac.uk/chembl/api/data/activity"
    params = {
        "format": "json",
        "target_chembl_id": chembl_id,
        "standard_type": "IC50",
        "order_by": "standard_value",
        "limit": max_hits,
        "offset": 0,
    }
    headers = {"Accept": "application/json"}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # 3) 提取 SMILES
    smiles = []
    for rec in data.get("activities", []):
        smi = rec.get("canonical_smiles")
        if smi:
            smiles.append(smi)
    smiles = list(dict.fromkeys(smiles))  # 去重但保留顺序

    if smiles:
        print_success(f"成功获取 {len(smiles)} 条活性化合物SMILES")
    else:
        print_warning("未找到活性数据")

    return smiles

def smiles_to_pdbqt(smiles: str, name="lig") -> Path:
    """RDKit SMILES → 3D 结构 → PDBQT (用 openbabel obabel 命令)."""
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError(f"无效的SMILES: {smiles}")

    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())
    AllChem.UFFOptimizeMolecule(mol)

    sdf = TMP_DIR / f"{name}.sdf"
    Chem.MolToMolFile(mol, str(sdf))

    pdbqt = TMP_DIR / f"{name}.pdbqt"
    # 隐藏命令行输出
    subprocess.run(["obabel", str(sdf), "-O", str(pdbqt)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return pdbqt

# ------------------------------------------------------------------
# API接口
# ------------------------------------------------------------------

class DrugDiscoveryAPI:
    """为前端提供API接口"""

    @staticmethod
    def get_disease_targets(disease: str, innovation_level: int = 5) -> Dict:
        """获取疾病相关靶点"""
        try:
            # 创建提示词，根据用户指定的创新度进行调整
            prompt = f"""列举与{disease}相关的药物靶点。靶点创新度为{innovation_level}/10。
            
创新度越低，返回的靶点越成熟可靠；创新度越高，返回的靶点越新颖前沿。
            
请返回最合适的蛋白基因符号列表（如EGFR, TP53等），每行一个。"""
            
            # 使用自定义提示词调用DeepSeek API
            rsp = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2 + (innovation_level * 0.05)  # 创新度越高，温度也相应调高一些
            )
            
            text = rsp.choices[0].message.content
            
            # 解析蛋白列表
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            candidates = []
            
            for l in lines:
                # 提取可能的蛋白/基因名
                parts = l.split(None, 1)
                token = parts[0]
                
                # 去除序号如 "1." 或 "1)"
                if re.match(r'^\d+[.)]', token):
                    if len(parts) > 1:
                        token = parts[1].split()[0]
                    else:
                        continue
                
                # 清理标点符号，只保留字母、数字和特定标点
                token = re.sub(r"[^A-Za-z0-9_-]", "", token)
                
                # 验证格式 - 至少有一个字母，长度在合理范围内
                if re.search(r'[A-Za-z]', token) and 2 <= len(token) <= 12:
                    candidates.append(token.upper())
            
            valid_proteins = [p for p in candidates if not p.isdigit() and re.match(r'^[A-Z][A-Z0-9_-]*$', p)]
            
            # 如果没有有效结果，提供一些常见靶点
            if not valid_proteins:
                default_proteins = ["EGFR", "TP53", "BRAF", "HER2", "VEGF", "TNF", "IL6", "ACE2", "PARP1", "KRAS"]
                return {
                    "success": True,
                    "targets": default_proteins[:10]
                }
            
            return {
                "success": True,
                "targets": valid_proteins[:10]
            }
        except Exception as e:
            logger.error(f"获取疾病靶点失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_uniprot_entries(gene_symbol: str) -> Dict:
        """获取UniProt条目"""
        try:
            entries = search_uniprot(gene_symbol)
            return {
                "success": True,
                "entries": entries
            }
        except Exception as e:
            logger.error(f"获取UniProt条目失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_structure_sources(uniprot_acc: str) -> Dict:
        """获取结构来源"""
        try:
            # 获取PDB结构
            pdb_ids = get_pdb_ids_for_uniprot(uniprot_acc)

            # 只有当没有PDB结构时才检查AlphaFold是否可用
            af_available = False
            if not pdb_ids:
                # 检查AlphaFold是否可用
                af_available = download_alphafold(uniprot_acc, dest_dir=TMP_DIR / "temp_check") is not None

            return {
                "success": True,
                "alphafold_available": af_available,
                "pdb_ids": pdb_ids
            }
        except Exception as e:
            logger.error(f"获取结构来源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def predict_pockets(structure_path: str) -> Dict:
        """预测口袋"""
        try:
            pockets = run_p2rank(Path(structure_path))
            return {
                "success": True,
                "pockets": [{"center": p["center"], "score": p["score"]} for p in pockets]
            }
        except Exception as e:
            logger.error(f"预测口袋失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_ligands(uniprot_acc: str, custom_smiles: List[str] = None) -> Dict:
        """获取配体SMILES"""
        try:
            results = {}

            if custom_smiles:
                results["custom_smiles"] = custom_smiles

            # 尝试从ChEMBL获取
            chembl_smiles = fetch_chembl_smiles(uniprot_acc)
            if chembl_smiles:
                results["chembl_smiles"] = chembl_smiles

            if not results:
                return {
                    "success": False,
                    "error": "未找到任何配体"
                }

            return {
                "success": True,
                **results
            }
        except Exception as e:
            logger.error(f"获取配体失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def ai_make_decision(options: List[str], context: str, question: str) -> Dict:
        """AI做决策的API接口"""
        try:
            idx, explanation = ai_make_decision(options, context, question)
            return {
                "success": True,
                "selected_index": idx,
                "selected_option": options[idx],
                "explanation": explanation
            }
        except Exception as e:
            logger.error(f"AI决策失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def select_best_compound(smiles_list: List[str], disease: str, protein: str, pocket_center: tuple = None) -> Dict:
        """AI选择并优化化合物"""
        try:
            selected, optimized, explanation = ai_select_best_compound(smiles_list, disease, protein, pocket_center)
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

    @staticmethod
    def generate_molecule_image(smiles: str) -> Dict:
        """生成分子结构图"""
        try:
            image_path = generate_molecule_image(smiles)

            # 转换为base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            return {
                "success": True,
                "image_path": image_path,
                "image_data": image_data
            }
        except Exception as e:
            logger.error(f"生成分子结构图失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_decision_explanations() -> Dict:
        """获取所有决策的解释"""
        return {
            "success": True,
            "explanations": workflow_state.get("decision_explanations", {})
        }

# ------------------------------------------------------------------
# 自动化工作流
# ------------------------------------------------------------------

def automated_workflow(disease: str, selected_targets: List[str] = None) -> Dict:
    """
全自动执行药物发现工作流

Args:
disease: 疾病名称
selected_targets: 可选的预选靶点列表

Returns:
工作流执行结果
    """
    # 重置决策解释
    workflow_state["decision_explanations"] = {}
    workflow_state["disease"] = disease
    workflow_state["current_step"] = 0
    workflow_state["total_steps"] = 7  # 增加了分子优化和可视化步骤

    # 1. 获取蛋白靶点
    workflow_state["current_step"] = 1
    print_step_start("蛋白靶点识别", workflow_state["current_step"], workflow_state["total_steps"])

    if not selected_targets:

        print_info(f"正在分析疾病「{disease}」的潜在药物靶点...")
        proteins = safe_execute(
            lambda: get_targets_from_deepseek(disease),
            "获取蛋白靶点失败",
            "get_targets",
            recoverable=False
        )

        if not proteins:
            raise WorkflowError("无法获取蛋白靶点", "get_targets", False)

        # 检查获取的蛋白靶点是否有效
        invalid_proteins = [p for p in proteins if p.isdigit() or len(p) < 2]
        if invalid_proteins:
            print_warning(f"检测到可能无效的蛋白靶点: {', '.join(invalid_proteins)}")
            print_info("正在重新获取更准确的靶点信息...")

            # 手动干预选项
            print_subsection("选择操作")
            print_options(["尝试重新获取靶点", "手动输入靶点", "继续使用当前结果"], "请选择操作:")
            choice = input("请输入选项编号 [1-3]: ").strip()

            if choice == "1" or not choice:
                # 重新获取，指定要进行多次尝试
                proteins = get_targets_from_deepseek(disease, top_k=10, max_attempts=3)
            elif choice == "2":
                # 手动输入
                manual_input = input("请输入靶点基因符号（多个用逗号分隔）: ").strip()
                proteins = [p.strip().upper() for p in manual_input.split(",") if p.strip()]
                if not proteins:
                    raise WorkflowError("未提供有效的蛋白靶点", "get_targets", False)
            # 默认为选项3，继续使用当前结果

        # 打印靶点列表供参考
        print_subsection("潜在靶点列表")
        print_options(proteins, "系统找到以下与疾病相关的蛋白靶点")


        context = f"我们正在为疾病'{disease}'寻找最佳药物靶点。理想的靶点应该在该疾病的发病机制中扮演关键角色，并且能够被药物作用。"
        idx, explanation = ai_make_decision(proteins, context, "哪个蛋白靶点最适合作为药物开发目标?")
        gene_symbol = proteins[idx]

        # 生成额外的靶点解释
        prompt = f"请简要介绍{gene_symbol}蛋白在{disease}疾病中的作用机制，包括它的功能和为什么是有价值的药物靶点（80-120字）"
        try:
            rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
                                                 messages=[{"role": "user", "content": prompt}],
                                                 temperature=0.3,
                                                 max_tokens=300)
            target_explanation = rsp.choices[0].message.content.strip()
            print_explanation_box(f"关于 {gene_symbol} 靶点", target_explanation)
        except Exception as e:
            logger.error(f"获取额外靶点解释失败: {str(e)}")

        # 保存决策解释
        workflow_state["decision_explanations"]["target_selection"] = {
            "context": context,
            "question": "哪个蛋白靶点最适合作为药物开发目标?",
            "options": proteins,
            "selected": gene_symbol,
            "explanation": explanation
        }
    else:
        # 使用用户预选的靶点
        gene_symbol = selected_targets[0]
        print_info(f"使用预选靶点: {gene_symbol}")

    workflow_state["gene_symbol"] = gene_symbol
    logger.info(f"选定蛋白靶点: {gene_symbol}")
    print_step_complete("蛋白靶点识别", workflow_state["current_step"], workflow_state["total_steps"])

    # 2. 获取UniProt信息
    workflow_state["current_step"] = 2
    print_step_start("蛋白质结构获取", workflow_state["current_step"], workflow_state["total_steps"])

    print_info(f"正在搜索 {gene_symbol} 的蛋白质数据...")
    uniprot_hits = safe_execute(
        lambda: search_uniprot(gene_symbol),
        "UniProt查询失败",
        "search_uniprot"
    )

    if not uniprot_hits:
        # 尝试直接搜索PDB
        print_warning(f"UniProt未找到{gene_symbol}，尝试直接检索PDB数据库...")
        pdb_ids = safe_execute(
            lambda: get_pdb_ids_for_gene(gene_symbol),
            "PDB搜索失败",
            "search_pdb"
        )
        if not pdb_ids:
            raise WorkflowError("未找到蛋白结构信息", "get_structure", False)

        # 我们选择第一个PDB ID
        print_success(f"直接从PDB获取结构: {', '.join(pdb_ids[:3])}{' 等' if len(pdb_ids) > 3 else ''}")
        print_info(f"自动选择第一个PDB结构: {pdb_ids[0]}")

        print_info(f"正在下载PDB结构 {pdb_ids[0]}...")
        struct_path = safe_execute(
            lambda: download_pdb(pdb_ids[0]),
            f"PDB {pdb_ids[0]}下载失败",
            "download_pdb",
            recoverable=False
        )

        workflow_state["structure_path"] = struct_path
        logger.info(f"结构文件已下载: {struct_path}")
        print_success(f"成功获取结构: {struct_path.name}")

        # 继续到口袋预测步骤
    else:
        # 打印UniProt条目供参考
        entries = [f'{h["acc"]} — {h["name"]}' for h in uniprot_hits]
        print_subsection("UniProt数据库条目")
        print_options(entries, "查询到以下蛋白质记录")

        # 让AI选择最合适的UniProt条目
        context = f"我们需要为基因{gene_symbol}选择合适的蛋白质信息。理想的选择应该是人源蛋白，与疾病相关，且结构完整。"
        idx, explanation = ai_make_decision(entries, context, "哪个UniProt条目最适合作为药物靶点?")
        acc = uniprot_hits[idx]["acc"]

        # 保存决策解释
        workflow_state["decision_explanations"]["uniprot_selection"] = {
            "context": context,
            "question": "哪个UniProt条目最适合作为药物靶点?",
            "options": entries,
            "selected": entries[idx],
            "explanation": explanation
        }

        workflow_state["uniprot_acc"] = acc
        logger.info(f"选定UniProt ID: {acc}")

        # 3. 获取结构
        # 先尝试获取PDB实验结构 (优先使用PDB数据库文件而非AlphaFold预测文件)
        print_info(f"优先获取PDB实验结构...")
        pdb_ids = safe_execute(
            lambda: get_pdb_ids_for_uniprot(acc),
            "获取PDB ID失败",
            "get_pdb_ids"
        )

        if pdb_ids:
            print_subsection("可用PDB结构")
            print_options(pdb_ids[:5], "找到以下PDB实验结构")

            # 让AI选择最合适的PDB结构
            context = f"我们需要为UniProt {acc}选择最适合药物设计的PDB结构。理想的选择应该是分辨率高、有配体结合信息、或者是晶体结构。"
            pdb_idx, explanation = ai_make_decision(pdb_ids, context, "哪个PDB结构最适合作为药物设计的起点?")

            # 保存决策解释
            workflow_state["decision_explanations"]["pdb_selection"] = {
                "context": context,
                "question": "哪个PDB结构最适合作为药物设计的起点?",
                "options": pdb_ids,
                "selected": pdb_ids[pdb_idx],
                "explanation": explanation
            }

            print_info(f"正在下载PDB结构 {pdb_ids[pdb_idx]}...")
            struct_path = safe_execute(
                lambda: download_pdb(pdb_ids[pdb_idx]),
                f"PDB {pdb_ids[pdb_idx]}下载失败",
                "download_pdb",
                recoverable=False
            )
            print_success(f"成功获取PDB实验结构: {struct_path.name}")
        else:
            # 只有在没有PDB结构时才尝试AlphaFold
            print_warning("未找到PDB实验结构，尝试获取AlphaFold预测结构...")
            struct_path = safe_execute(
                lambda: download_alphafold(acc),
                "AlphaFold下载失败",
                "download_alphafold",
                recoverable=False
            )

            if not struct_path:
                raise WorkflowError("无可用蛋白质结构", "get_structure", False)

            print_success(f"成功获取AlphaFold预测结构: {struct_path.name}")

        workflow_state["structure_path"] = struct_path
        logger.info(f"结构文件已下载: {struct_path}")

    print_step_complete("蛋白质结构获取", workflow_state["current_step"], workflow_state["total_steps"])

    # 3. 口袋预测
    workflow_state["current_step"] = 3
    print_step_start("药物结合口袋预测", workflow_state["current_step"], workflow_state["total_steps"])

    pockets = safe_execute(
        lambda: run_p2rank(struct_path),
        "P2Rank口袋预测失败",
        "predict_pockets"
    )

    if not pockets:
        # 尝试云端预测
        print_warning("本地口袋预测失败，尝试云端服务...")
        pockets = safe_execute(
            lambda: run_dogsite_api(struct_path),
            "DoGSite口袋预测失败",
            "predict_pockets_dogsite",
            recoverable=False
        )

    if not pockets:
        raise WorkflowError("口袋预测失败", "predict_pockets", False)

    # 打印口袋信息供参考
    print_subsection("预测口袋")
    pk_choices = [f"Score={p['score']:.2f}, Center={tuple(round(x,2) for x in p['center'])}"
                  for p in pockets[:5]]  # 只显示前5个

    print_options(pk_choices, "系统预测出以下潜在药物结合口袋")

    # 让AI选择最佳口袋
    context = f"我们需要为蛋白{gene_symbol} (UniProt: {workflow_state.get('uniprot_acc', 'Unknown')})选择最适合药物结合的口袋。理想的选择应该是得分高、在蛋白活性区域且可及性好的位点。"
    pk_idx, explanation = ai_make_decision(pk_choices, context, "哪个蛋白口袋最适合作为药物结合位点?")

    # 保存决策解释
    workflow_state["decision_explanations"]["pocket_selection"] = {
        "context": context,
        "question": "哪个蛋白口袋最适合作为药物结合位点?",
        "options": pk_choices,
        "selected": pk_choices[pk_idx],
        "explanation": explanation
    }

    pocket_center = pockets[pk_idx]["center"]
    workflow_state["pocket_center"] = pocket_center
    logger.info(f"选定口袋中心坐标: {pocket_center}")

    # 生成口袋性质解释
    prompt = f"""
        分析以下蛋白{gene_symbol}的药物结合口袋的药物化学特性:
        口袋坐标: {pocket_center}
        口袋得分: {pockets[pk_idx]['score']}

请简要分析此口袋的:
1. 可能的结合性质(疏水/亲水)
2. 适合结合的药物类型
3. 作为药物靶点的优势

用中文回答，80-120字。
        """

    try:
        rsp = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
                                             messages=[{"role": "user", "content": prompt}],
                                             temperature=0.3,
                                             max_tokens=300)
        pocket_explanation = rsp.choices[0].message.content.strip()
        print_explanation_box("口袋药物化学分析", pocket_explanation)
    except Exception as e:
        logger.error(f"获取口袋解释失败: {str(e)}")

    print_step_complete("药物结合口袋预测", workflow_state["current_step"], workflow_state["total_steps"])

    # 4. 获取候选配体SMILES
    workflow_state["current_step"] = 4
    print_step_start("候选药物分子获取", workflow_state["current_step"], workflow_state["total_steps"])

    uniprot_acc = workflow_state.get("uniprot_acc")

    # 自动获取SMILES
    smiles_list = []
    if uniprot_acc:
        smiles_list = safe_execute(
            lambda: fetch_chembl_smiles(uniprot_acc, max_hits=10),
            "获取ChEMBL SMILES失败",
            "fetch_smiles"
        )

    if not smiles_list:
        # 如果无法获取，创建一些基础SMILES作为示例
        logger.warning("无法获取ChEMBL SMILES，使用示例SMILES")
        print_warning("无法从数据库获取活性化合物，使用预设示例分子...")

        # 药物名称和SMILES的映射
        example_drugs = {
            "阿司匹林": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "咖啡因": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
            "苯海拉明": "C1=CC=C(C=C1)C(=O)OCCN(C)C",
            "普萘洛尔": "CC(C)NCC(O)COC1=CC=CC2=C1C=CC=C2",
            "利多卡因": "CCN(CC)CC(=O)NC1=CC=C(C=C1)OC"
        }

        smiles_list = list(example_drugs.values())

        # 打印药物名称和SMILES
        print_subsection("示例药物分子")
        for drug_name, smiles in example_drugs.items():
            print(f"  {Colors.BLUE}•{Colors.ENDC} {drug_name}: {Colors.CYAN}{smiles[:30]}...{Colors.ENDC}")
    else:
        # 尝试用AI给每个SMILES标注可能的药物类别
        print_subsection("获取的活性化合物")
        for i, smiles in enumerate(smiles_list[:5], 1):  # 只显示前5个
            print(f"  {Colors.BLUE}{i}.{Colors.ENDC} {Colors.CYAN}{smiles[:50]}...{Colors.ENDC}")

        if len(smiles_list) > 5:
            print(f"  {Colors.BLUE}...{Colors.ENDC} 共{len(smiles_list)}个化合物")

    workflow_state["smiles_list"] = smiles_list

    print_step_complete("候选药物分子获取", workflow_state["current_step"], workflow_state["total_steps"])

    # 5. 化合物选择与优化
    workflow_state["current_step"] = 5
    print_step_start("AI药物分子优化", workflow_state["current_step"], workflow_state["total_steps"])

    # 让AI选择最佳化合物并优化
    print_info(f"正在分析为{gene_symbol}靶点选择最佳先导化合物...")

    selected_smiles, optimized_smiles, compound_explanation = safe_execute(
        lambda: ai_select_best_compound(smiles_list, disease, gene_symbol, pocket_center),
        "AI选择和优化化合物失败",
        "optimize_compound",
        recoverable=False
    )

    if not selected_smiles or not optimized_smiles:
        raise WorkflowError("无法选择或优化化合物", "optimize_compound", False)

    print_success(f"AI已选择并优化了化合物")
    print_subsection("药物分子优化结果")
    print_detail("原始SMILES", f"{Colors.CYAN}{selected_smiles[:60]}...{Colors.ENDC}" if len(selected_smiles) > 60 else selected_smiles)
    print_detail("优化后SMILES", f"{Colors.CYAN}{optimized_smiles[:60]}...{Colors.ENDC}" if len(optimized_smiles) > 60 else optimized_smiles)

    # 显示优化解释
    print_explanation_box("分子优化分析", compound_explanation)

    # 保存优化的SMILES到工作流状态
    workflow_state["optimized_smiles"] = optimized_smiles
    logger.info(f"优化后的SMILES: {optimized_smiles}")

    print_step_complete("AI药物分子优化", workflow_state["current_step"], workflow_state["total_steps"])

    # 6. 生成分子结构可视化 (只保留分子结构图的部分)
    workflow_state["current_step"] = 6
    print_step_start("分子结构可视化", workflow_state["current_step"], workflow_state["total_steps"])

    # 生成ASCII分子结构用于命令行显示
    print_info("生成ASCII分子结构...")
    display_molecule_ascii(optimized_smiles)

    # 生成分子结构图
    print_info("生成高质量分子结构图...")
    molecule_image = safe_execute(
        lambda: generate_molecule_image(optimized_smiles),
        "生成分子结构图失败",
        "molecule_image",
        recoverable=True
    )

    workflow_state["molecule_image"] = molecule_image
    if molecule_image:
        print_success(f"分子结构图已保存至 {molecule_image}")
    else:
        print_warning("无法生成分子结构图，继续执行...")

    print_step_complete("分子结构可视化", workflow_state["current_step"], workflow_state["total_steps"])

    # 7. 保存结果文件
    workflow_state["current_step"] = 7
    print_step_start("保存结果文件", workflow_state["current_step"], workflow_state["total_steps"])

    # 保存结果文件
    results_file = TMP_DIR / "docking_input.txt"
    with open(results_file, "w") as f:
        f.write(f"疾病: {disease}\n")
        f.write(f"蛋白: {gene_symbol} (UniProt: {workflow_state.get('uniprot_acc', 'Unknown')})\n")
        f.write(f"结构文件: {struct_path}\n")
        f.write(f"口袋中心坐标: {pocket_center}\n\n")
        f.write(f"优化前的SMILES: {selected_smiles}\n")
        f.write(f"优化后的SMILES: {optimized_smiles}\n\n")
        f.write("原始SMILES列表:\n")
        for i, smi in enumerate(smiles_list, 1):
            f.write(f"{i}. {smi}\n")

    # 保存配体SDF文件
    print_info("为优化后的分子生成3D结构...")

    try:
        # 生成优化后分子的3D结构
        mol = Chem.MolFromSmiles(optimized_smiles)
        if mol:
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())
            AllChem.UFFOptimizeMolecule(mol)
            sdf_file = TMP_DIR / "optimized_ligand.sdf"
            pdbqt_file = TMP_DIR / "optimized_ligand.pdbqt"

            Chem.MolToMolFile(mol, str(sdf_file))
            print_success(f"已保存优化后分子的SDF文件: {sdf_file}")

            # 尝试转换为PDBQT格式
            try:
                subprocess.run(["obabel", str(sdf_file), "-O", str(pdbqt_file)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print_success(f"已保存优化后分子的PDBQT文件: {pdbqt_file}")
            except Exception as e:
                logger.error(f"SDF转PDBQT失败: {str(e)}")
                print_warning("无法转换为PDBQT格式，可能需要安装OpenBabel")
    except Exception as e:
        logger.error(f"生成优化后分子3D结构失败: {str(e)}")
        print_warning("无法生成优化后分子的3D结构文件")

    print_step_complete("保存结果文件", workflow_state["current_step"], workflow_state["total_steps"])

    # 生成AI科学解释
    print_section("科学解释与分析")
    print_info("AI正在生成科学分析报告...")

    explanation = ai_explain_results(workflow_state)

    # 打印完整的解释（不使用Markdown格式）
    width = min(TERM_WIDTH - 4, 80)
    lines = textwrap.wrap(explanation, width=width)

    print_subsection("靶点药物发现科学分析")
    for line in lines:
        print(f"{Colors.GREEN}│{Colors.ENDC} {line}")
    print()

    # 输出结果摘要
    print_section("工作流完成")
    print_success("药物发现工作流已成功完成!")

    summary_box = f"""
        {Colors.BLUE}┏{'━' * (TERM_WIDTH - 2)}┓{Colors.ENDC}
        {Colors.BLUE}┃{Colors.ENDC} {Colors.BOLD}疾病{Colors.ENDC}: {disease}{' ' * (TERM_WIDTH - len(disease) - 12)}{Colors.BLUE}┃{Colors.ENDC}
        {Colors.BLUE}┃{Colors.ENDC} {Colors.BOLD}靶点{Colors.ENDC}: {gene_symbol}{' ' * (TERM_WIDTH - len(gene_symbol) - 10)}{Colors.BLUE}┃{Colors.ENDC}
        {Colors.BLUE}┃{Colors.ENDC} {Colors.BOLD}口袋坐标{Colors.ENDC}: {str(pocket_center)}{' ' * (TERM_WIDTH - len(str(pocket_center)) - 14)}{Colors.BLUE}┃{Colors.ENDC}
        {Colors.BLUE}┃{Colors.ENDC} {Colors.BOLD}优化后分子{Colors.ENDC}: {optimized_smiles[:40]}...{' ' * (TERM_WIDTH - 48 - 14)}{Colors.BLUE}┃{Colors.ENDC}
        {Colors.BLUE}┃{Colors.ENDC} {Colors.BOLD}输出目录{Colors.ENDC}: {str(TMP_DIR)[:40]}...{' ' * (TERM_WIDTH - min(40, len(str(TMP_DIR))) - 49)}{Colors.BLUE}┃{Colors.ENDC}
        {Colors.BLUE}┗{'━' * (TERM_WIDTH - 2)}┛{Colors.ENDC}
        """
    print(summary_box)

    # 返回执行结果
    return {
        "disease": disease,
        "gene_symbol": gene_symbol,
        "uniprot_acc": workflow_state.get("uniprot_acc"),
        "structure_path": str(struct_path),
        "pocket_center": pocket_center,
        "smiles_list": smiles_list,
        "selected_smiles": selected_smiles,
        "optimized_smiles": optimized_smiles,
        "molecule_image": workflow_state.get("molecule_image"),
        "results_file": str(results_file),
        "output_dir": str(TMP_DIR),
        "explanation": explanation,
        "decision_explanations": workflow_state["decision_explanations"]
    }

# ------------------------------------------------------------------
# 主流程
# ------------------------------------------------------------------

def main():
    try:
        # 清屏并显示欢迎信息
        clear_screen()
        print_header()

        # 1. 疾病输入 - 使用自然语言输入
        disease = natural_language_input("请输入您关注的疾病名称（中文或英文均可）")

        # 2. 执行自动化工作流
        result = automated_workflow(disease)

    except WorkflowError as e:
        print_error(f"工作流错误: {str(e)}")
        if e.recoverable:
            print_info("您可以尝试修复问题后重新运行。")
        else:
            print_warning("无法继续执行，请检查输入或环境配置。")
    except KeyboardInterrupt:
        print_warning("\n用户终止。")
    except Exception as e:
        print_error(f"未预期的错误: {str(e)}")
        logger.error(f"未捕获异常: {traceback.format_exc()}")
        print_info("请查看日志文件了解更多详情。")
    finally:
        # 显示结束信息
        print(f"\n{Colors.BLUE}{'='*TERM_WIDTH}{Colors.ENDC}")
        print(f"{Colors.BLUE}会话结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print(f"{Colors.BLUE}{'='*TERM_WIDTH}{Colors.ENDC}")

if __name__ == "__main__":
    main()