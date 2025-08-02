"""
工作流引擎 - 协调整个药物发现流程
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..core.config import settings
from ..core.constants import WorkflowSteps, WorkflowStatus
from ..models.workflow import WorkflowState, workflow_state
from ..models.protein import Protein, StructureSource, Pocket, Compound
from ..models.exceptions import WorkflowError, ProcessingError
from ..utils.display import (
    print_info, print_warning, print_error, print_success, 
    print_step_start, print_step_complete, print_subsection, 
    print_options, print_explanation_box
)
from ..utils.helpers import safe_execute

from .ai_engine import AIEngine
from .pharma_engine import PharmaEngine
from .visualization_engine import VisualizationEngine

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流引擎类 - 协调整个药物发现流程"""
    
    def __init__(self):
        """初始化工作流引擎"""
        self.ai_engine = AIEngine()
        self.pharma_engine = PharmaEngine()
        self.visualization_engine = VisualizationEngine()
        self.current_workflow: Optional[WorkflowState] = None
    
    def execute_complete_workflow(self, disease: str, selected_targets: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行完整的药物发现工作流
        
        Args:
            disease: 疾病名称
            selected_targets: 预选的靶点列表（可选）
        
        Returns:
            工作流结果字典
        """
        try:
            # 初始化工作流状态
            import uuid
            workflow_id = str(uuid.uuid4())
            self.current_workflow = WorkflowState(
                workflow_id=workflow_id,
                disease=disease,
                status=WorkflowStatus.IN_PROGRESS
            )
            
            print_info(f"开始药物发现工作流: {disease}")
            
            # 步骤1: 靶点发现
            self._execute_target_discovery(selected_targets)
            
            # 步骤2: 结构获取
            self._execute_structure_retrieval()
            
            # 步骤3: 口袋预测
            self._execute_pocket_prediction()
            
            # 步骤4: 配体检索
            self._execute_ligand_retrieval()
            
            # 步骤5: 化合物优化
            self._execute_compound_optimization()
            
            # 步骤6: 分子对接
            self._execute_molecular_docking()
            
            # 步骤7: 结果分析
            self._execute_result_analysis()
            
            # 完成工作流
            self.current_workflow.status = WorkflowStatus.COMPLETED
            print_success("药物发现工作流已成功完成!")
            
            return self.current_workflow.to_dict()
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            if self.current_workflow:
                self.current_workflow.status = WorkflowStatus.FAILED
            raise WorkflowError(f"工作流执行失败: {str(e)}")
    
    def _execute_target_discovery(self, selected_targets: Optional[List[str]] = None):
        """执行靶点发现步骤"""
        step_name = WorkflowSteps.TARGET_DISCOVERY
        self.current_workflow.start_step(step_name)
        print_step_start("蛋白靶点识别", 1, 6)
        
        try:
            if not selected_targets:
                # 使用AI发现靶点
                targets = self.ai_engine.get_disease_targets(
                    self.current_workflow.disease,
                    innovation_level=5,
                    top_k=10
                )
                
                # 转换为Protein对象
                protein_objects = []
                for target in targets:
                    protein_objects.append(Protein(gene_symbol=target))
                
                self.current_workflow.targets = protein_objects
                
                # 显示靶点选项
                print_subsection("潜在靶点列表")
                print_options(targets, "系统找到以下与疾病相关的蛋白靶点")
                
                # AI选择最佳靶点
                context = f"我们正在为疾病'{self.current_workflow.disease}'寻找最佳药物靶点。理想的靶点应该在该疾病的发病机制中扮演关键角色，并且能够被药物作用。"
                idx, explanation = self.ai_engine.ai_make_decision(
                    targets, context, "哪个蛋白靶点最适合作为药物开发目标?"
                )
                
                selected_protein = protein_objects[idx]
                self.current_workflow.selected_target = selected_protein
                
                # 生成靶点解释
                target_explanation = self.ai_engine.generate_target_explanation(
                    selected_protein.gene_symbol, 
                    self.current_workflow.disease
                )
                print_explanation_box(f"关于 {selected_protein.gene_symbol} 靶点", target_explanation)
                
            else:
                # 使用预选靶点
                selected_protein = Protein(gene_symbol=selected_targets[0])
                self.current_workflow.selected_target = selected_protein
                self.current_workflow.targets = [selected_protein]
                print_info(f"使用预选靶点: {selected_targets[0]}")
            
            self.current_workflow.complete_step(step_name, selected_protein)
            print_step_complete("蛋白靶点识别", 1, 6)
            
        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            raise WorkflowError(f"靶点发现失败: {str(e)}")
    
    def _execute_structure_retrieval(self):
        """执行结构获取步骤"""
        step_name = WorkflowSteps.STRUCTURE_RETRIEVAL
        self.current_workflow.start_step(step_name)
        print_step_start("蛋白质结构获取", 2, 6)
        
        try:
            gene_symbol = self.current_workflow.selected_target.gene_symbol
            
            # 搜索UniProt
            print_info(f"正在搜索 {gene_symbol} 的蛋白质数据...")
            uniprot_entries = self.pharma_engine.search_uniprot(gene_symbol)
            
            if not uniprot_entries:
                # 尝试直接搜索PDB
                print_warning(f"UniProt未找到{gene_symbol}，尝试直接检索PDB数据库...")
                pdb_ids = self.pharma_engine.get_pdb_ids_for_gene(gene_symbol)
                
                if not pdb_ids:
                    raise ProcessingError("未找到蛋白结构信息")
                
                # 下载第一个PDB结构
                print_info(f"自动选择第一个PDB结构: {pdb_ids[0]}")
                struct_path = self.pharma_engine.download_pdb(pdb_ids[0])
                
                structure_source = StructureSource(
                    source_type="pdb",
                    identifier=pdb_ids[0],
                    file_path=struct_path
                )
                
            else:
                # 选择UniProt条目
                entries_display = [f'{entry["acc"]} — {entry["name"]}' for entry in uniprot_entries]
                print_subsection("UniProt数据库条目")
                print_options(entries_display, "查询到以下蛋白质记录")
                
                # AI选择最合适的条目
                context = f"我们需要为基因{gene_symbol}选择合适的蛋白质信息。理想的选择应该是人源蛋白，与疾病相关，且结构完整。"
                idx, explanation = self.ai_engine.ai_make_decision(
                    entries_display, context, "哪个UniProt条目最适合作为药物靶点?"
                )
                
                selected_entry = uniprot_entries[idx]
                acc = selected_entry["acc"]
                
                # 更新选中的蛋白质信息
                self.current_workflow.selected_target.uniprot_id = acc
                self.current_workflow.selected_target.name = selected_entry["name"]
                
                # 获取PDB结构
                pdb_ids = self.pharma_engine.get_pdb_ids_for_uniprot(acc)
                
                if pdb_ids:
                    print_subsection("可用PDB结构")
                    print_options(pdb_ids[:5], "找到以下PDB实验结构")
                    
                    # AI选择最佳PDB结构
                    context = f"我们需要为UniProt {acc}选择最适合药物设计的PDB结构。理想的选择应该是分辨率高、有配体结合信息、或者是晶体结构。"
                    pdb_idx, explanation = self.ai_engine.ai_make_decision(
                        pdb_ids, context, "哪个PDB结构最适合作为药物设计的起点?"
                    )
                    
                    selected_pdb = pdb_ids[pdb_idx]
                    print_info(f"正在下载PDB结构 {selected_pdb}...")
                    struct_path = self.pharma_engine.download_pdb(selected_pdb)
                    
                    structure_source = StructureSource(
                        source_type="pdb",
                        identifier=selected_pdb,
                        file_path=struct_path
                    )
                    print_success(f"成功获取PDB实验结构: {struct_path.name}")
                    
                else:
                    # 尝试AlphaFold
                    print_warning("未找到PDB实验结构，尝试获取AlphaFold预测结构...")
                    struct_path = self.pharma_engine.download_alphafold(acc)
                    
                    if not struct_path:
                        raise ProcessingError("无可用蛋白质结构")
                    
                    structure_source = StructureSource(
                        source_type="alphafold",
                        identifier=acc,
                        file_path=struct_path
                    )
                    print_success(f"成功获取AlphaFold预测结构: {struct_path.name}")
            
            self.current_workflow.structure_sources = [structure_source]
            self.current_workflow.selected_structure = structure_source
            
            self.current_workflow.complete_step(step_name, structure_source)
            print_step_complete("蛋白质结构获取", 2, 6)
            
        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            raise WorkflowError(f"结构获取失败: {str(e)}")

    def _execute_pocket_prediction(self):
        """执行口袋预测步骤"""
        step_name = WorkflowSteps.POCKET_PREDICTION
        self.current_workflow.start_step(step_name)
        print_step_start("药物结合口袋预测", 3, 6)

        try:
            struct_path = self.current_workflow.selected_structure.file_path

            # 确保路径是Path对象并且文件存在
            if isinstance(struct_path, str):
                struct_path = Path(struct_path)

            if not struct_path.exists():
                raise ProcessingError(f"结构文件不存在: {struct_path}")

            print_info(f"使用结构文件: {struct_path}")

            # 尝试P2Rank预测
            try:
                pockets_data = self.pharma_engine.run_p2rank(struct_path)
            except Exception as e:
                print_warning("本地口袋预测失败，尝试云端服务...")
                pockets_data = self.pharma_engine.run_dogsite_api(struct_path)

            if not pockets_data:
                raise ProcessingError("口袋预测失败")

            # 转换为Pocket对象
            pockets = []
            for pocket_data in pockets_data:
                pocket = Pocket(
                    pocket_id=pocket_data["pocket_id"],
                    center=pocket_data["center"],
                    score=pocket_data["score"],
                    prediction_method=pocket_data.get("prediction_method")
                )
                pockets.append(pocket)

            self.current_workflow.pockets = pockets

            # 显示口袋选项
            print_subsection("预测口袋")
            pocket_choices = [
                f"Score={p.score:.2f}, Center={tuple(round(x,2) for x in p.center)}"
                for p in pockets[:5]
            ]
            print_options(pocket_choices, "系统预测出以下潜在药物结合口袋")

            # AI选择最佳口袋
            gene_symbol = self.current_workflow.selected_target.gene_symbol
            uniprot_acc = self.current_workflow.selected_target.uniprot_id or "Unknown"
            context = f"我们需要为蛋白{gene_symbol} (UniProt: {uniprot_acc})选择最适合药物结合的口袋。理想的选择应该是得分高、在蛋白活性区域且可及性好的位点。"

            pocket_idx, explanation = self.ai_engine.ai_make_decision(
                pocket_choices, context, "哪个蛋白口袋最适合作为药物结合位点?"
            )

            selected_pocket = pockets[pocket_idx]
            self.current_workflow.selected_pocket = selected_pocket

            self.current_workflow.complete_step(step_name, selected_pocket)
            print_step_complete("药物结合口袋预测", 3, 6)

        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            raise WorkflowError(f"口袋预测失败: {str(e)}")

    def _execute_ligand_retrieval(self):
        """执行配体检索步骤"""
        step_name = WorkflowSteps.LIGAND_RETRIEVAL
        self.current_workflow.start_step(step_name)
        print_step_start("候选药物分子获取", 4, 6)

        try:
            uniprot_acc = self.current_workflow.selected_target.uniprot_id

            if uniprot_acc:
                # 从ChEMBL获取活性化合物
                smiles_list = self.pharma_engine.fetch_chembl_smiles(uniprot_acc, max_hits=20)
            else:
                # 使用默认药物样分子
                smiles_list = self.pharma_engine._get_default_drug_like_smiles(20)

            if not smiles_list:
                raise ProcessingError("未找到候选化合物")

            # 转换为Compound对象
            compounds = []
            for i, smiles in enumerate(smiles_list):
                compound = Compound(
                    smiles=smiles,
                    compound_id=f"compound_{i+1}",
                    source="chembl" if uniprot_acc else "default"
                )
                compounds.append(compound)

            self.current_workflow.compounds = compounds

            print_subsection("获取的活性化合物")
            for i, smiles in enumerate(smiles_list[:5], 1):
                print(f"  {i}. {smiles[:50]}...")

            if len(smiles_list) > 5:
                print(f"  ... 共{len(smiles_list)}个化合物")

            self.current_workflow.complete_step(step_name, compounds)
            print_step_complete("候选药物分子获取", 4, 6)

        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            raise WorkflowError(f"配体检索失败: {str(e)}")

    def _execute_compound_optimization(self):
        """执行化合物优化步骤"""
        step_name = WorkflowSteps.COMPOUND_OPTIMIZATION
        self.current_workflow.start_step(step_name)
        print_step_start("AI药物分子优化", 5, 7)

        try:
            smiles_list = [c.smiles for c in self.current_workflow.compounds]
            disease = self.current_workflow.disease
            protein = self.current_workflow.selected_target.gene_symbol
            pocket_center = tuple(self.current_workflow.selected_pocket.center) if self.current_workflow.selected_pocket else None

            # AI选择并优化化合物
            selected_smiles, optimized_smiles, explanation = self.ai_engine.ai_select_best_compound(
                smiles_list, disease, protein, pocket_center
            )

            # 创建优化后的化合物对象
            optimized_compound = Compound(
                smiles=optimized_smiles,
                compound_id="optimized_compound",
                name="AI优化化合物",
                source="ai_optimized"
            )

            self.current_workflow.selected_compound = optimized_compound

            print_success("AI已选择并优化了化合物")
            print_subsection("药物分子优化结果")
            print(f"原始SMILES: {selected_smiles[:60]}...")
            print(f"优化后SMILES: {optimized_smiles[:60]}...")

            print_explanation_box("分子优化分析", explanation)

            self.current_workflow.complete_step(step_name, optimized_compound)
            print_step_complete("AI药物分子优化", 5, 7)

        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            raise WorkflowError(f"化合物优化失败: {str(e)}")

    def _execute_molecular_docking(self):
        """执行分子对接步骤"""
        step_name = "molecular_docking"  # 新增步骤
        self.current_workflow.start_step(step_name)
        print_step_start("分子对接验证", 6, 7)

        try:
            # 获取必要的信息
            optimized_smiles = self.current_workflow.selected_compound.smiles
            protein_structure = self.current_workflow.selected_structure
            pocket_center = self.current_workflow.selected_pocket.center
            
            print_info(f"正在进行分子对接...")
            print_info(f"蛋白质结构: {protein_structure.file_path}")
            print_info(f"配体SMILES: {optimized_smiles[:50]}...")
            print_info(f"对接口袋中心: ({pocket_center[0]:.2f}, {pocket_center[1]:.2f}, {pocket_center[2]:.2f})")
            
            # 执行分子对接
            docking_result = self.pharma_engine.perform_molecular_docking(
                protein_path=protein_structure.file_path,
                ligand_smiles=optimized_smiles,
                pocket_center=pocket_center,
                box_size=[20, 20, 20]  # 默认搜索盒子大小
            )
            
            # 保存对接结果
            self.current_workflow.docking_result = docking_result
            
            # 显示对接结果
            print_success(f"分子对接完成!")
            print_subsection("对接结果")
            print(f"  最佳结合亲和力: {docking_result['best_score']:.2f} kcal/mol")
            print(f"  找到构象数: {len(docking_result['poses'])}")
            
            # 显示前3个构象的详情
            print_subsection("最佳构象详情")
            for i, pose in enumerate(docking_result['poses'][:3], 1):
                print(f"  构象 {i}: {pose['binding_affinity']:.2f} kcal/mol")
            
            # 评估结合强度
            best_score = docking_result['best_score']
            if best_score < -8.0:
                print_success("✓ 预测结合强度很强 (< -8.0 kcal/mol)")
            elif best_score < -6.0:
                print_info("○ 预测结合强度中等 (-8.0 ~ -6.0 kcal/mol)")
            else:
                print_warning("⚠ 预测结合强度较弱 (> -6.0 kcal/mol)")
                
            self.current_workflow.complete_step(step_name, docking_result)
            print_step_complete("分子对接验证", 6, 7)

        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            # 对接失败不阻塞工作流，但记录错误
            print_warning(f"分子对接失败: {str(e)}")
            print_info("继续进行结果分析...")
            
            # 创建一个空的对接结果
            self.current_workflow.docking_result = {
                "success": False,
                "error": str(e),
                "ligand_smiles": self.current_workflow.selected_compound.smiles,
                "protein_path": str(self.current_workflow.selected_structure.file_path),
                "pocket_center": pocket_center,
                "best_score": 0.0,
                "poses": []
            }
            print_step_complete("分子对接验证", 6, 7)

    def _execute_result_analysis(self):
        """执行结果分析步骤"""
        step_name = WorkflowSteps.RESULT_ANALYSIS
        self.current_workflow.start_step(step_name)
        print_step_start("分子结构可视化与分析", 7, 7)

        try:
            optimized_smiles = self.current_workflow.selected_compound.smiles

            # 生成分子可视化
            print_info("生成分子结构信息...")
            self.visualization_engine.display_molecule_ascii(optimized_smiles)

            # 生成分子图像
            print_info("生成高质量分子结构图...")
            molecule_image = self.visualization_engine.generate_molecule_image(optimized_smiles)

            # 生成对接可视化（如果有对接结果）
            docking_visualization = None
            if hasattr(self.current_workflow, 'docking_result') and self.current_workflow.docking_result:
                print_info("生成分子对接可视化...")
                if self.current_workflow.docking_result.get('success', False):
                    docking_visualization = self.visualization_engine.generate_docking_visualization(
                        self.current_workflow.docking_result
                    )
                else:
                    print_warning("跳过对接可视化（对接失败）")

            # 生成AI科学解释
            print_info("AI正在生成科学分析报告...")
            workflow_data = self.current_workflow.to_dict()
            explanation = self.ai_engine.ai_explain_results(workflow_data)

            # 保存结果
            results = {
                "molecule_image": molecule_image,
                "docking_visualization": docking_visualization,
                "scientific_explanation": explanation,
                "workflow_summary": workflow_data
            }

            self.current_workflow.complete_step(step_name, results)
            print_step_complete("分子结构可视化与分析", 7, 7)

        except Exception as e:
            self.current_workflow.fail_step(step_name, str(e))
            raise WorkflowError(f"结果分析失败: {str(e)}")
