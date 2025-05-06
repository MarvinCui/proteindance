from typing import List, Tuple
from openai import OpenAI

client = OpenAI()
from ..core.config import settings
from ..models.workflow import workflow_state

class AIService:
    @staticmethod
    def get_disease_targets(disease: str, innovation_level: int = 5) -> List[str]:
        """Get protein targets for disease with specified innovation level"""
        if innovation_level <= 3:
            prompt = f"""列举与{disease}相关、已有成熟药物的经典靶点（保守策略）。"""
        elif innovation_level <= 7:
            prompt = f"""列举与{disease}相关、处于临床试验阶段的新型靶点（平衡策略）。"""
        else:
            prompt = f"""列举与{disease}相关的创新性靶点，优先考虑新发现的信号通路（创新策略）。"""

        response = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2 + (innovation_level * 0.05)  # Adjust creativity based on innovation level)

        text = response.choices[0].message.content
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        proteins = []
        for l in lines:
            token = re.sub(r"[^A-Za-z0-9_-]", "", l.split()[0])
            if 2 <= len(token) <= 12:
                proteins.append(token.upper())

        return proteins[:10]

    @staticmethod
    def optimize_compound(smiles_list: List[str], disease: str, protein: str, 
                         innovation_level: int = 5) -> Tuple[str, str, str]:
        """Optimize compound with specified innovation level"""
        if innovation_level <= 3:
            strategy = "保守优化策略，基于已知药物骨架进行小幅改进"
        elif innovation_level <= 7:
            strategy = "平衡优化策略，在保持药物性的同时进行适度创新"
        else:
            strategy = "创新优化策略，探索全新骨架和作用机制"

        prompt = f"""基于{strategy}，为{disease}的{protein}靶点优化以下化合物:
候选SMILES列表:
{chr(10).join([f"{i+1}. {smi}" for i, smi in enumerate(smiles_list)])}

请执行以下任务:
1. 选择一个最佳先导化合物（给出SMILES和编号）
2. 解释为什么选择该化合物（考虑结构特点、药效团、药物化学性质等）
3. 对该化合物进行结构优化，生成一个新的改进版SMILES
4. 解释你做的修饰如何提高其作为药物的潜力

请按以下格式回复：
选择SMILES编号: [数字]
选择的SMILES: [完整SMILES]
选择理由: [100-200字解释]
优化后的SMILES: [完整SMILES]
优化解释: [100-200字解释]
        """

        response = client.chat.completions.create(model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000)

        text = response.choices[0].message.content.strip()
        selected_idx_match = re.search(r'选择SMILES编号:\s*(\d+)', text, re.IGNORECASE)
        selected_smiles_match = re.search(r'选择的SMILES:\s*(.*?)(?:\n|$)', text, re.DOTALL)
        reason_match = re.search(r'选择理由:\s*(.*?)(?:\n|$)', text, re.DOTALL)
        optimized_smiles_match = re.search(r'优化后的SMILES:\s*(.*?)(?:\n|$)', text, re.DOTALL)
        optimization_match = re.search(r'优化解释:\s*(.*?)(?:\n|$)', text, re.DOTALL)

        selected_idx = int(selected_idx_match.group(1)) if selected_idx_match else 1
        selected_smiles = selected_smiles_match.group(1).strip() if selected_smiles_match else smiles_list[selected_idx - 1]
        reason = reason_match.group(1).strip() if reason_match else "未提供选择理由"
        optimized_smiles = optimized_smiles_match.group(1).strip() if optimized_smiles_match else selected_smiles
        optimization_explanation = optimization_match.group(1).strip() if optimization_match else "未提供优化解释"

        mol = Chem.MolFromSmiles(optimized_smiles)
        if not mol:
            optimized_smiles = selected_smiles

        explanation = f"选择理由: {reason}\n\n优化解释: {optimization_explanation}"
        return selected_smiles, optimized_smiles, explanation