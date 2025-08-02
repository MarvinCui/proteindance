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
import torch
import sys
import argparse
import torch
import warnings
import os

# 在导入transformers之前设置环境变量，防止tokenizers并行化死锁
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# 可选导入transformers
try:
    from transformers import GPT2LMHeadModel, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    GPT2LMHeadModel = None
    AutoTokenizer = None

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AIEngine:
    """AI引擎类 - 负责所有AI相关操作"""

    def __init__(self):
        """初始化AI引擎"""
        if not HAS_OPENAI:
            logger.warning("OpenAI库未安装，AI功能将受限")
            self.client = None
            self.openai_model = None
        else:
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            self.openai_model = "deepseek-ai/DeepSeek-V3"

        import os
        # 使用绝对路径来避免HuggingFace路径验证问题
        try:
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            self.model_path = os.path.join(current_dir, "backend", "services", "aimodels", "first model")
        except (NameError, TypeError):
            # 备用方案：使用当前工作目录
            self.model_path = os.path.abspath(os.path.join("backend", "services", "aimodels", "first model"))
        self.optimizer_model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._model_loaded = False

    def load_optimizer_model(self):
        """加载模型和分词器"""
        if self._model_loaded:
            return
            
        try:
            print(f"正在加载模型从路径: {self.model_path}")
            print(f"使用设备: {self.device}")

            # 检查transformers可用性
            if not HAS_TRANSFORMERS:
                raise ImportError("transformers库未安装，无法加载本地模型")
                
            # 检查模型路径是否存在
            import os
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"模型路径不存在: {self.model_path}")

            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)

            # 加载模型
            self.optimizer_model = GPT2LMHeadModel.from_pretrained(self.model_path, local_files_only=True)
            self.optimizer_model.to(self.device)
            self.optimizer_model.eval()

            self._model_loaded = True
            print("✓ 模型加载成功")
            print(f"✓ 词汇表大小: {self.tokenizer.vocab_size}")
            print(f"✓ 模型参数量: {sum(p.numel() for p in self.optimizer_model.parameters()):,}")

        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise RuntimeError(f"模型加载失败: {e}")

    def generate_optimized_smiles(self,
                                  input_smiles: str,
                                  max_length: int = 84,
                                  num_return_sequences: int = 1,
                                  temperature: float = 0.8,
                                  top_p: float = 0.9,
                                  do_sample: bool = True) -> List[str]:
        """
        生成优化后的SMILES字符串

        Args:
            input_smiles: 输入的SMILES字符串
            max_length: 最大生成长度
            num_return_sequences: 返回序列数量
            temperature: 温度参数，控制随机性
            top_p: nucleus sampling参数
            do_sample: 是否使用采样

        Returns:
            生成的SMILES字符串列表
        """
        # 检查模型是否可用
        if not HAS_TRANSFORMERS:
            logger.warning("transformers不可用，使用备用SMILES生成方法")
            return [input_smiles]  # 返回原始SMILES作为备选方案
            
        self.load_optimizer_model()
        try:
            # 分词输入
            input_ids = self.tokenize_smiles(input_smiles)

            print(f"输入SMILES: {input_smiles}")
            print(f"输入长度: {input_ids.shape[1]} tokens")

            # 检查输入长度
            if input_ids.shape[1] >= max_length:
                print(f"⚠️ 输入长度 ({input_ids.shape[1]}) 超过最大长度 ({max_length})")
                return [input_smiles]

            # 生成文本
            with torch.no_grad():
                outputs = self.optimizer_model.generate(
                    input_ids,
                    max_length=max_length,
                    num_return_sequences=num_return_sequences,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=True
                )

            # 解码生成的序列
            generated_smiles = []
            for i, output in enumerate(outputs):
                generated_text = self.tokenizer.decode(output, skip_special_tokens=True)
                generated_smiles.append(generated_text)
                print(f"生成序列 {i + 1}: {generated_text}")

            return generated_smiles

        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return [input_smiles]

    def tokenize_smiles(self, smiles: str) -> torch.Tensor:
        """
        对SMILES字符串进行分词

        Args:
            smiles: SMILES化学式字符串

        Returns:
            分词后的tensor
        """
        if not HAS_TRANSFORMERS or self.tokenizer is None:
            raise RuntimeError("tokenizer未初始化或transformers不可用")
            
        # 编码SMILES字符串
        encoded = self.tokenizer.encode(smiles, return_tensors='pt')
        return encoded.to(self.device)

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

            # 调用AI API，带重试机制
            targets = self._call_ai_with_retry(prompt, innovation_level, top_k)

            if not targets:
                logger.warning("AI未返回有效靶点，使用默认靶点")
                targets = self._get_default_targets(disease, top_k)

            logger.info(f"获取到{len(targets)}个靶点: {', '.join(targets)}")
            return targets

        except Exception as e:
            logger.error(f"获取疾病靶点失败: {str(e)}")
            # 在失败时返回默认靶点而不是抛出异常
            logger.warning("使用默认靶点作为备选")
            return self._get_default_targets(disease, top_k)

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
{chr(10).join([f"{i + 1}. {opt}" for i, opt in enumerate(options)])}

请先回答你选择的选项编号（仅数字，如"2"），然后在新行中详细解释为什么选择该选项（100-150字）。格式如下:

选择: [数字]
原因: [解释]"""

            # 调用AI API
            with show_spinner("AI思考中..."):
                response = self.client.chat.completions.create(
                    model=self.openai_model,
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
                    logger.info(f"AI选择了选项 {selection + 1}: {options[selection]}")
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
            compounds_text = "\n".join([f"{i + 1}. {smiles}" for i, smiles in enumerate(smiles_list)])

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
3. 详细的选择理由

格式:
选择: [编号]
优化SMILES: [SMILES结构]
理由: [详细解释]"""

            # 调用AI API
            with show_spinner("AI分析化合物..."):
                response = self.client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )

            text = response.choices[0].message.content.strip()

            # 解析AI回答
            selection_match = re.search(r'选择:\s*(\d+)', text, re.IGNORECASE)
            # optimized_match = re.search(r'优化SMILES:\s*([^\n]+)', text, re.IGNORECASE)
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

            optimized_match = self.generate_optimized_smiles(
                selected_smiles, 
                num_return_sequences=3,  # 生成3个候选
                temperature=1.0,         # 增加多样性
                max_length=100          # 增加最大长度
            )
            logger.info("优化之前:"+selected_smiles+"  优化之后:"+str(optimized_match))

            # 获取优化的SMILES
            if optimized_match:
                # 尝试找到第一个有效的SMILES
                optimized_smiles = selected_smiles  # 默认使用原始SMILES
                for candidate in optimized_match:
                    if self._validate_smiles(candidate) and candidate != selected_smiles:
                        optimized_smiles = candidate
                        logger.info(f"找到有效的优化SMILES: {candidate}")
                        break
                else:
                    logger.warning("GPT2模型未生成有效的优化SMILES，尝试简单化学修饰")
                    # 简单化学修饰策略作为备用
                    optimized_smiles = self._simple_chemical_modification(selected_smiles)
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

            # 构建分子对接结果描述
            docking_info = ""
            if workflow_data.get('docking_result') and workflow_data.get('docking_score'):
                docking_score = workflow_data['docking_score']
                num_poses = len(workflow_data['docking_result'].get('poses', []))
                docking_info = f"""
- 分子对接结果: 最佳结合分数 {docking_score:.2f} kcal/mol，获得 {num_poses} 个构象
- 对接评价: {'优秀结合亲和力' if docking_score < -7.0 else '良好结合亲和力' if docking_score < -5.0 else '需要进一步优化'}"""
            
            prompt = f"""
请对以下药物发现过程给出专业的科学解释:

- 目标疾病: {workflow_data['disease']}
- 选定靶点蛋白: {workflow_data['gene_symbol']}
- UniProt ID: {workflow_data.get('uniprot_acc', '未知')}
- 蛋白质结构来源: {'AlphaFold预测' if str(workflow_data.get('structure_path', '')).endswith('_AF.pdb') else 'PDB实验结构'}
- 识别到的口袋坐标: {workflow_data.get('pocket_center', '未知')}
- 候选化合物数量: {len(workflow_data.get('smiles_list', [])) if workflow_data.get('smiles_list') else '未知'}
- 优化后的化合物SMILES: {workflow_data.get('optimized_smiles', '未知')}{docking_info}

请从以下角度进行分析:
1. 靶点选择的科学依据
2. 结构信息的重要性
3. 口袋预测的意义
4. 化合物优化的策略
5. 分子对接结果的意义（如果有）
6. 整体药物发现策略的合理性

要求:
- 使用专业的药物化学和分子生物学术语
- 解释要准确、简洁、有逻辑性
- 字数控制在350-600字
- 不要使用Markdown格式
- 重点突出科学原理和方法学意义"""

            with show_spinner("生成科学分析..."):
                response = self.client.chat.completions.create(
                    model=self.openai_model,
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
                model=self.openai_model,
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
        if not smiles or not smiles.strip():
            return False
            
        try:
            from rdkit import Chem
            from rdkit.Chem import rdMolDescriptors
            mol = Chem.MolFromSmiles(smiles.strip())
            if mol is None:
                return False
            # 进一步验证：检查分子量是否合理
            mw = rdMolDescriptors.CalcExactMolWt(mol)
            return 50 <= mw <= 1000  # 合理的分子量范围
        except ImportError:
            # 如果没有rdkit，进行简单验证
            cleaned = smiles.strip()
            # 检查基本SMILES语法
            if not cleaned or len(cleaned) < 3:
                return False
            # 检查括号是否匹配
            paren_count = cleaned.count('(') - cleaned.count(')')
            bracket_count = cleaned.count('[') - cleaned.count(']')
            return paren_count == 0 and bracket_count == 0
        except Exception:
            return False

    def _simple_chemical_modification(self, smiles: str) -> str:
        """简单的化学修饰策略作为GPT2模型的备用方案"""
        try:
            from rdkit import Chem
            from rdkit.Chem import rdMolDescriptors
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return smiles
            
            # 尝试简单的化学修饰
            modifications = [
                "C",      # 添加甲基
                "CC",     # 添加乙基
                "O",      # 添加羟基
                "N",      # 添加氨基
                "F",      # 添加氟原子
            ]
            
            for mod in modifications:
                try:
                    # 简单的字符串连接修饰（这是一个基础示例）
                    modified_smiles = smiles + mod
                    if self._validate_smiles(modified_smiles):
                        logger.info(f"使用简单修饰生成: {modified_smiles}")
                        return modified_smiles
                except:
                    continue
            
            # 如果所有修饰都失败，返回原始SMILES
            return smiles
            
        except ImportError:
            # 没有rdkit时的简单修饰
            return smiles + "C"  # 简单添加甲基
        except Exception:
            return smiles

    def _call_ai_with_retry(self, prompt: str, innovation_level: int, top_k: int, max_retries: int = 3) -> List[str]:
        """
        带重试机制的AI调用
        
        Args:
            prompt: 提示词
            innovation_level: 创新度
            top_k: 返回数量
            max_retries: 最大重试次数
        
        Returns:
            靶点列表
        """
        import socket
        from openai import OpenAI

        last_exception = None

        for attempt in range(max_retries):
            try:
                with show_spinner(f"AI分析中... (尝试 {attempt + 1}/{max_retries})"):
                    response = self.client.chat.completions.create(
                        model=self.openai_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2 + (innovation_level * 0.05),
                        timeout=30  # 30秒超时
                    )

                text = response.choices[0].message.content.strip()
                targets = self._parse_targets_from_text(text, top_k)

                if targets:  # 如果成功获取到靶点，返回结果
                    return targets
                else:
                    logger.warning(f"尝试 {attempt + 1} 未返回有效靶点")

            except (socket.error, ConnectionError, BrokenPipeError) as e:
                last_exception = e
                logger.warning(f"网络连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue

            except Exception as e:
                last_exception = e
                logger.error(f"AI调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        # 所有重试都失败了
        logger.error(f"AI调用最终失败: {str(last_exception)}")
        return []
