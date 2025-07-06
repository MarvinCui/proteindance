"""
AI引擎 - 处理所有AI相关功能
"""
import re
import time
import logging
from typing import List, Tuple, Dict, Any, Optional

# 可选导入OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None

from ..core.config import settings
from ..models.exceptions import APIError, ProcessingError
from ..utils.display import print_info, print_ai_choice, print_warning, print_error, show_spinner
from ..utils.helpers import safe_execute

logger = logging.getLogger(__name__)


class AIEngine:
    """AI引擎类 - 负责所有AI相关操作"""
    
    def __init__(self):
        """初始化AI引擎"""
        if not HAS_OPENAI:
            logger.warning("OpenAI库未安装，AI功能将受限")
            self.client = None
            self.model = None
        else:
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            self.model = "deepseek-ai/DeepSeek-V3"
    
    def get_disease_targets(self, disease: str, innovation_level: int = 5, top_k: int = 10) -> List[str]:
        """
        获取疾病相关的药物靶点
        
        Args:
            disease: 疾病名称
            innovation_level: 创新度 (1-10)
            top_k: 返回靶点数量
        
        Returns:
            靶点基因符号列表
        """
        try:
            if not HAS_OPENAI or not self.client:
                logger.warning("OpenAI未配置，使用默认靶点")
                return self._get_default_targets(disease, top_k)

            print_info(f"正在分析疾病「{disease}」的潜在药物靶点...")

            # 根据创新度调整提示词
            if innovation_level <= 3:
                innovation_desc = "成熟可靠的经典靶点"
            elif innovation_level <= 7:
                innovation_desc = "平衡的靶点组合"
            else:
                innovation_desc = "新颖前沿的创新靶点"
            
            prompt = f"""列举与{disease}相关的药物靶点。靶点创新度为{innovation_level}/10。
            
创新度越低，返回的靶点越成熟可靠；创新度越高，返回的靶点越新颖前沿。
当前要求：{innovation_desc}

请返回最合适的蛋白基因符号列表（如EGFR, TP53等），每行一个。禁止把多个叠在一起。
返回{top_k}个以内的靶点。"""
            
            # 调用AI API
            with show_spinner("AI分析中..."):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2 + (innovation_level * 0.05)
                )
            
            text = response.choices[0].message.content.strip()
            
            # 解析靶点列表
            targets = self._parse_targets_from_text(text, top_k)
            
            if not targets:
                logger.warning("AI未返回有效靶点，使用默认靶点")
                targets = self._get_default_targets(disease, top_k)
            
            logger.info(f"获取到{len(targets)}个靶点: {', '.join(targets)}")
            return targets
            
        except Exception as e:
            logger.error(f"获取疾病靶点失败: {str(e)}")
            raise APIError(f"获取疾病靶点失败: {str(e)}")
    
    def ai_make_decision(self, options: List[str], context: str, question: str) -> Tuple[int, str]:
        """
        使用AI进行决策选择
        
        Args:
            options: 选项列表
            context: 上下文信息
            question: 问题描述
        
        Returns:
            (选择的索引, 解释)
        """
        try:
            if not HAS_OPENAI or not self.client:
                logger.warning("OpenAI未配置，返回第一个选项")
                return 0, "OpenAI未配置，默认选择第一个选项"

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
原因: [解释]"""
            
            # 调用AI API
            with show_spinner("AI思考中..."):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
            
            text = response.choices[0].message.content.strip()
            
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

    def ai_select_best_compound(self, smiles_list: List[str], disease: str,
                               protein: str, pocket_center: Optional[Tuple] = None) -> Tuple[str, str, str]:
        """
        AI选择并优化最佳化合物

        Args:
            smiles_list: SMILES列表
            disease: 疾病名称
            protein: 蛋白质名称
            pocket_center: 口袋中心坐标

        Returns:
            (选择的SMILES, 优化的SMILES, 解释)
        """
        try:
            if not HAS_OPENAI or not self.client:
                logger.warning("OpenAI未配置，返回第一个化合物")
                return smiles_list[0], smiles_list[0], "OpenAI未配置，返回第一个化合物"

            print_info(f"正在为{protein}靶点选择最佳先导化合物...")

            # 构建化合物选择提示
            compounds_text = "\n".join([f"{i+1}. {smiles}" for i, smiles in enumerate(smiles_list)])

            prompt = f"""作为药物化学专家，请从以下候选化合物中选择最适合治疗{disease}的先导化合物，靶点蛋白为{protein}。

候选化合物SMILES:
{compounds_text}

请考虑以下因素:
1. 分子大小和复杂度
2. 药物相似性(Lipinski规则)
3. 与靶点的潜在结合能力
4. 合成可行性
5. 毒性风险

请回答:
1. 选择的化合物编号
2. 优化后的SMILES结构(如果需要优化)
3. 详细的选择和优化理由

格式:
选择: [编号]
优化SMILES: [SMILES结构]
理由: [详细解释]"""

            # 调用AI API
            with show_spinner("AI分析化合物..."):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )

            text = response.choices[0].message.content.strip()

            # 解析AI回答
            selection_match = re.search(r'选择:\s*(\d+)', text, re.IGNORECASE)
            optimized_match = re.search(r'优化SMILES:\s*([^\n]+)', text, re.IGNORECASE)
            reason_match = re.search(r'理由:\s*(.*?)(?:\n\n|$)', text, re.DOTALL | re.IGNORECASE)

            # 获取选择的化合物
            if selection_match:
                selection_idx = int(selection_match.group(1)) - 1
                if 0 <= selection_idx < len(smiles_list):
                    selected_smiles = smiles_list[selection_idx]
                else:
                    selected_smiles = smiles_list[0]
            else:
                selected_smiles = smiles_list[0]

            # 获取优化的SMILES
            if optimized_match:
                optimized_smiles = optimized_match.group(1).strip()
                # 验证SMILES有效性
                if not self._validate_smiles(optimized_smiles):
                    optimized_smiles = selected_smiles
            else:
                optimized_smiles = selected_smiles

            # 获取解释
            explanation = "AI选择了最适合的化合物"
            if reason_match:
                explanation = reason_match.group(1).strip()

            logger.info(f"AI选择化合物: {selected_smiles}")
            logger.info(f"优化后化合物: {optimized_smiles}")

            return selected_smiles, optimized_smiles, explanation

        except Exception as e:
            logger.error(f"AI选择化合物失败: {str(e)}")
            # 返回第一个化合物作为默认选择
            return smiles_list[0], smiles_list[0], f"选择失败: {str(e)}"

    def generate_ligand_smiles(self, protein_target: str, disease_context: str, num_smiles: int = 10) -> List[str]:
        """
        使用AI生成潜在的配体SMILES

        Args:
            protein_target: 靶点蛋白名称
            disease_context: 疾病背景
            num_smiles: 希望生成的SMILES数量

        Returns:
            SMILES字符串列表
        """
        try:
            if not HAS_OPENAI or not self.client:
                logger.warning("OpenAI未配置，无法生成SMILES")
                return []

            print_info(f"正在为靶点「{protein_target}」生成新的配体分子...")

            prompt = f"""
            作为一名药物化学家，请为靶点蛋白 {protein_target}（在 {disease_context} 疾病中）设计 {num_smiles} 个新颖的、具有潜在活性的、符合Lipinski药物相似性规则的类药小分子。

            请直接返回SMILES字符串列表，每行一个，不要包含任何其��文字、标题或序号。

            示例:
            CCOc1ccccc1C(=O)O
            CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc12
            """

            # 调用AI API
            with show_spinner("AI正在设计分子..."):
                response = self.client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V3",  # 使用指定的模型
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,  # 提高一点创造性
                    max_tokens=1500
                )

            text = response.choices[0].message.content.strip()
            
            # 解析SMILES列表
            smiles_list = [line.strip() for line in text.split('\n') if self._validate_smiles(line.strip())]

            if not smiles_list:
                logger.warning("AI未能生成有效的SMILES")
                return []

            logger.info(f"AI成功生成 {len(smiles_list)} 个SMILES")
            return smiles_list[:num_smiles]

        except Exception as e:
            logger.error(f"AI生成SMILES失败: {str(e)}")
            raise APIError(f"AI生成SMILES失败: {str(e)}")

    def ai_explain_results(self, workflow_data: Dict[str, Any]) -> str:
        """
        生成工作流结果的AI解释

        Args:
            workflow_data: 工作流数据

        Returns:
            科学解释文本
        """
        try:
            if not workflow_data.get("disease") or not workflow_data.get("gene_symbol"):
                return "无足够信息生成解释"

            if not HAS_OPENAI or not self.client:
                return f"针对{workflow_data['disease']}的{workflow_data['gene_symbol']}靶点药物发现已完成。由于AI服务未配置，无法生成详细科学解释。"

            print_info("正在生成科学解释...")

            prompt = f"""
请对以下药物发现过程给出专业的科学解释:

- 目标疾病: {workflow_data['disease']}
- 选定靶点蛋白: {workflow_data['gene_symbol']}
- UniProt ID: {workflow_data.get('uniprot_acc', '未知')}
- 蛋白质结构来源: {'AlphaFold预测' if str(workflow_data.get('structure_path', '')).endswith('_AF.pdb') else 'PDB实验结构'}
- 识别到的口袋坐标: {workflow_data.get('pocket_center', '未知')}
- 候选化合物数量: {len(workflow_data.get('smiles_list', [])) if workflow_data.get('smiles_list') else '未知'}
- 优化后的化合物SMILES: {workflow_data.get('optimized_smiles', '未知')}

请从以下角度进行分析:
1. 靶点选择的科学依据
2. 结构信息的重要性
3. 口袋预测的意义
4. 化合物优化的策略
5. 整体药物发现策略的合理性

要求:
- 使用专业的药物化学和分子生物学术语
- 解释要准确、简洁、有逻辑性
- 字数控制在300-500字
- 不要使用Markdown格式
- 重点突出科学原理和方法学意义"""

            with show_spinner("生成科学分析..."):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=800
                )

            explanation = response.choices[0].message.content.strip()
            logger.info("AI科学解释生成完成")
            return explanation

        except Exception as e:
            logger.error(f"生成AI解释失败: {str(e)}")
            return f"生成科学解释时发生错误: {str(e)}"

    def generate_target_explanation(self, gene_symbol: str, disease: str) -> str:
        """
        生成靶点的详细解释

        Args:
            gene_symbol: 基因符号
            disease: 疾病名称

        Returns:
            靶点解释文本
        """
        try:
            if not HAS_OPENAI or not self.client:
                return f"{gene_symbol}是{disease}的重要药物靶点"

            prompt = f"请简要介绍{gene_symbol}蛋白在{disease}疾病中的作用机制，包括它的功能和为什么是有价值的药物靶点（80-120字）"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"生成靶点解释失败: {str(e)}")
            return f"{gene_symbol}是{disease}的重要药物靶点"

    def _parse_targets_from_text(self, text: str, max_targets: int) -> List[str]:
        """从AI回答中解析靶点列表"""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        targets = []

        for line in lines:
            # 提取可能的蛋白/基因名
            parts = line.split(None, 1)
            if not parts:
                continue

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
                targets.append(token.upper())

        # 验证结果 - 确保不是纯数字且符合基因命名规范
        valid_targets = [t for t in targets if not t.isdigit() and re.match(r'^[A-Z][A-Z0-9_-]*$', t)]

        return valid_targets[:max_targets]

    def _get_default_targets(self, disease: str, max_targets: int) -> List[str]:
        """获取默认靶点列表"""
        # 常见的药物靶点
        default_targets = [
            "EGFR", "TP53", "BRAF", "HER2", "VEGF",
            "TNF", "IL6", "ACE2", "PARP1", "KRAS",
            "PIK3CA", "MTOR", "CDK4", "HDAC1", "BCL2"
        ]

        logger.warning(f"使用默认靶点列表用于疾病: {disease}")
        return default_targets[:max_targets]

    def _validate_smiles(self, smiles: str) -> bool:
        """验证SMILES字符串的有效性"""
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except ImportError:
            # 如果没有rdkit，进行简单验证
            return bool(smiles and len(smiles.strip()) > 0 and not smiles.isspace())
