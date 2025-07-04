"""
药物发现API - 统一的API接口类
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..core.config import settings
from ..models.exceptions import APIError, ValidationError
from ..utils.validators import RequestValidator
from .ai_engine import AIEngine
from .pharma_engine import PharmaEngine
from .visualization_engine import VisualizationEngine
from .workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class DrugDiscoveryAPI:
    """药物发现API类 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.ai_engine = AIEngine()
            self.pharma_engine = PharmaEngine()
            self.visualization_engine = VisualizationEngine()
            self.workflow_engine = WorkflowEngine()
            self._initialized = True
    
    @staticmethod
    def get_disease_targets(disease: str, innovation_level: int = 5) -> Dict:
        """获取疾病相关靶点"""
        try:
            # 验证请求
            RequestValidator.validate_disease_targets_request({"disease": disease})
            
            api = DrugDiscoveryAPI()
            targets = api.ai_engine.get_disease_targets(disease, innovation_level)
            
            return {
                "success": True,
                "targets": targets
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
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
            # 验证请求
            RequestValidator.validate_uniprot_request({"gene_symbol": gene_symbol})
            
            api = DrugDiscoveryAPI()
            entries = api.pharma_engine.search_uniprot(gene_symbol)
            
            return {
                "success": True,
                "entries": entries
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
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
            # 验证请求
            RequestValidator.validate_structure_request({"uniprot_acc": uniprot_acc})
            
            api = DrugDiscoveryAPI()
            
            # 获取PDB结构
            pdb_ids = api.pharma_engine.get_pdb_ids_for_uniprot(uniprot_acc)
            
            # 检查AlphaFold可用性（仅在没有PDB时）
            af_available = False
            af_path = None
            if not pdb_ids:
                af_path = api.pharma_engine.download_alphafold(
                    uniprot_acc, 
                    dest_dir=settings.TMP_DIR / "temp_check"
                )
                af_available = af_path is not None
            
            return {
                "success": True,
                "alphafold_available": af_available,
                "pdb_ids": pdb_ids,
                "structure_path": str(af_path) if af_path else None
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"获取结构来源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def download_structure(pdb_id: str = None, uniprot_acc: str = None, source_type: str = "pdb") -> Dict:
        """下载结构文件"""
        try:
            api = DrugDiscoveryAPI()

            if source_type == "pdb" and pdb_id:
                # 下载PDB文件
                structure_path = api.pharma_engine.download_pdb(pdb_id)
                return {
                    "success": True,
                    "structure_path": str(structure_path),
                    "source_type": "pdb",
                    "identifier": pdb_id
                }
            elif source_type == "alphafold" and uniprot_acc:
                # 下载AlphaFold文件
                structure_path = api.pharma_engine.download_alphafold(uniprot_acc)
                if structure_path:
                    return {
                        "success": True,
                        "structure_path": str(structure_path),
                        "source_type": "alphafold",
                        "identifier": uniprot_acc
                    }
                else:
                    return {
                        "success": False,
                        "error": "AlphaFold结构不可用"
                    }
            else:
                return {
                    "success": False,
                    "error": "缺少必要参数"
                }

        except Exception as e:
            logger.error(f"下载结构失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def predict_pockets(structure_path: str) -> Dict:
        """预测口袋 - 自动处理PDB ID或文件路径"""
        try:
            logger.info(f"🔍 [DEBUG] 开始口袋预测，输入: {structure_path}")

            # 检查输入是PDB ID还是文件路径
            from pathlib import Path
            import re

            # 判断是否为PDB ID (4个字符的字母数字组合)
            is_pdb_id = bool(re.match(r'^[A-Za-z0-9]{4}$', structure_path.strip()))
            logger.info(f"🔍 [DEBUG] 是否为PDB ID: {is_pdb_id}")

            if is_pdb_id:
                # 如果是PDB ID，先下载文件
                logger.info(f"🔍 [DEBUG] 检测到PDB ID，开始下载: {structure_path}")
                api = DrugDiscoveryAPI()

                # 下载PDB文件
                download_result = api.download_structure(pdb_id=structure_path, source_type="pdb")
                if not download_result.get("success"):
                    logger.error(f"❌ [DEBUG] PDB下载失败: {download_result.get('error')}")
                    return {
                        "success": False,
                        "error": f"无法下载PDB文件 {structure_path}: {download_result.get('error')}"
                    }

                actual_file_path = download_result["structure_path"]
                logger.info(f"✅ [DEBUG] PDB下载成功: {actual_file_path}")
            else:
                # 如果是文件路径，直接使用
                actual_file_path = structure_path
                logger.info(f"🔍 [DEBUG] 使用提供的文件路径: {actual_file_path}")

            # 验证文件路径
            path_obj = Path(actual_file_path)
            logger.info(f"🔍 [DEBUG] 最终文件路径: {path_obj}")
            logger.info(f"🔍 [DEBUG] 文件存在: {path_obj.exists()}")
            logger.info(f"🔍 [DEBUG] 是否为文件: {path_obj.is_file()}")
            logger.info(f"🔍 [DEBUG] 文件扩展名: {path_obj.suffix}")

            # 验证请求
            logger.info(f"🔍 [DEBUG] 开始验证请求...")
            RequestValidator.validate_pocket_request({"structure_path": actual_file_path})
            logger.info(f"🔍 [DEBUG] 请求验证通过")

            # 执行口袋预测
            if not hasattr(DrugDiscoveryAPI, '_instance') or DrugDiscoveryAPI._instance is None:
                api = DrugDiscoveryAPI()
            else:
                api = DrugDiscoveryAPI._instance

            logger.info(f"🔍 [DEBUG] 开始调用P2Rank...")
            pockets = api.pharma_engine.run_p2rank(Path(actual_file_path))
            logger.info(f"🔍 [DEBUG] P2Rank完成，找到{len(pockets)}个口袋")

            return {
                "success": True,
                "pockets": [{"center": p["center"], "score": p["score"]} for p in pockets],
                "structure_path": actual_file_path  # 返回实际使用的文件路径
            }

        except ValidationError as e:
            logger.error(f"❌ [DEBUG] 请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"❌ [DEBUG] 预测口袋失败: {str(e)}")
            import traceback
            logger.error(f"❌ [DEBUG] 完整错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_ligands(uniprot_acc: Optional[str] = None, custom_smiles: Optional[List[str]] = None) -> Dict:
        """获取配体"""
        try:
            logger.info(f"🔍 [LIGAND_DEBUG] 开始获取配体，UniProt: {uniprot_acc}, 自定义SMILES: {custom_smiles}")

            # 验证请求
            RequestValidator.validate_ligand_request({
                "uniprot_acc": uniprot_acc,
                "custom_smiles": custom_smiles
            })
            logger.info(f"✅ [LIGAND_DEBUG] 请求验证通过")

            api = DrugDiscoveryAPI()

            if custom_smiles:
                logger.info(f"🔍 [LIGAND_DEBUG] 使用自定义SMILES，数量: {len(custom_smiles)}")
                smiles_list = custom_smiles
            elif uniprot_acc:
                logger.info(f"🔍 [LIGAND_DEBUG] 从ChEMBL获取配体，UniProt: {uniprot_acc}")
                smiles_list = api.pharma_engine.fetch_chembl_smiles(uniprot_acc)
                logger.info(f"🔍 [LIGAND_DEBUG] ChEMBL返回配体数量: {len(smiles_list) if smiles_list else 0}")
            else:
                logger.info(f"🔍 [LIGAND_DEBUG] 使用默认药物样分子")
                smiles_list = api.pharma_engine._get_default_drug_like_smiles(10)
                logger.info(f"🔍 [LIGAND_DEBUG] 默认分子数量: {len(smiles_list) if smiles_list else 0}")

            # 检查结果
            if not smiles_list:
                logger.error(f"❌ [LIGAND_DEBUG] 未获取到任何配体")
                return {
                    "success": False,
                    "error": "无法获取或生成任何配体"
                }

            logger.info(f"✅ [LIGAND_DEBUG] 成功获取{len(smiles_list)}个配体")

            # 根据来源分类返回数据，匹配前端期望的格式
            if custom_smiles:
                return {
                    "success": True,
                    "custom_smiles": smiles_list
                }
            elif uniprot_acc:
                return {
                    "success": True,
                    "chembl_smiles": smiles_list
                }
            else:
                return {
                    "success": True,
                    "ai_generated_smiles": smiles_list
                }

        except ValidationError as e:
            logger.error(f"❌ [LIGAND_DEBUG] 请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"❌ [LIGAND_DEBUG] 获取配体失败: {str(e)}")
            import traceback
            logger.error(f"❌ [LIGAND_DEBUG] 完整错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def ai_make_decision(options: List[str], context: str, question: str) -> Dict:
        """AI决策"""
        try:
            # 验证请求
            RequestValidator.validate_ai_decision_request({
                "options": options,
                "context": context,
                "question": question
            })
            
            api = DrugDiscoveryAPI()
            selection_idx, explanation = api.ai_engine.ai_make_decision(options, context, question)
            
            return {
                "success": True,
                "selected_option": options[selection_idx],
                "selected_index": selection_idx,
                "explanation": explanation
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"AI决策失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def select_best_compound(smiles_list: List[str], disease: str, protein: str, 
                           pocket_center: Optional[tuple] = None) -> Dict:
        """AI选择并优化化合物"""
        try:
            # 验证请求
            RequestValidator.validate_compound_selection_request({
                "smiles_list": smiles_list,
                "disease": disease,
                "protein": protein
            })
            
            api = DrugDiscoveryAPI()
            selected, optimized, explanation = api.ai_engine.ai_select_best_compound(
                smiles_list, disease, protein, pocket_center
            )
            
            return {
                "success": True,
                "selected_smiles": selected,
                "optimized_smiles": optimized,
                "explanation": explanation
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
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
            # 验证请求
            RequestValidator.validate_molecule_image_request({"smiles": smiles})
            
            api = DrugDiscoveryAPI()
            
            # 生成图像
            image_path = api.visualization_engine.generate_molecule_image(smiles)
            
            if not image_path:
                return {
                    "success": False,
                    "error": "无法生成分子图像"
                }
            
            # 转换为base64
            image_data = api.visualization_engine.molecule_to_base64(smiles)
            
            return {
                "success": True,
                "image_path": image_path,
                "image_data": image_data
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"生成分子结构图失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def complete_workflow(disease: str, selected_targets: Optional[List[str]] = None) -> Dict:
        """执行完整工作流"""
        try:
            # 验证请求
            RequestValidator.validate_disease_targets_request({"disease": disease})
            
            api = DrugDiscoveryAPI()
            result = api.workflow_engine.execute_complete_workflow(disease, selected_targets)
            
            return {
                "success": True,
                "workflow_result": result
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_decision_explanations() -> Dict:
        """获取所有决策的解释"""
        try:
            # 这里可以从工作流状态中获取决策解释
            # 暂时返回空的解释
            return {
                "success": True,
                "explanations": {}
            }
            
        except Exception as e:
            logger.error(f"获取决策解释失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
