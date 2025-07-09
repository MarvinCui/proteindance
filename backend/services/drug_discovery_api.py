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
            # 由于AI引擎已经有了fallback机制，这里应该不会抛出异常
            # 但为了保险起见，还是返回默认靶点
            return {
                "success": True,
                "targets": ["EGFR", "TP53", "BRAF", "HER2", "VEGF"],
                "warning": f"AI调用失败，使用默认靶点: {str(e)}"
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
            logger.info(f"开始获取UniProt {uniprot_acc}的结构来源...")
            
            # 首先尝试PDB结构（实验结构优先）
            pdb_ids = []
            pdb_path = None
            try:
                logger.info(f"尝试获取PDB结构...")
                pdb_ids = api.pharma_engine.get_pdb_ids_for_uniprot(uniprot_acc)
                logger.info(f"找到{len(pdb_ids)}个PDB结构")
                
                # 如果找到PDB，下载第一个
                if pdb_ids:
                    try:
                        pdb_path = api.pharma_engine.download_pdb(
                            pdb_ids[0], 
                            dest_dir=settings.TMP_DIR
                        )
                        logger.info(f"成功下载PDB结构: {pdb_path}")
                    except Exception as e:
                        logger.warning(f"PDB下载失败: {str(e)}")
                        pdb_path = None
            except Exception as e:
                logger.warning(f"PDB查询失败: {str(e)}")
                pdb_ids = []
            
            # 如果PDB可用，优先使用PDB
            if pdb_path and pdb_path.exists():
                return {
                    "success": True,
                    "alphafold_available": False,
                    "pdb_ids": pdb_ids,
                    "structure_path": str(pdb_path),
                    "structure_source": "pdb"
                }
            
            # 如果PDB不可用，尝试AlphaFold结构
            af_available = False
            af_path = None
            try:
                logger.info(f"PDB不可用，尝试获取AlphaFold结构...")
                af_path = api.pharma_engine.download_alphafold(
                    uniprot_acc, 
                    dest_dir=settings.TMP_DIR
                )
                af_available = af_path is not None
                logger.info(f"AlphaFold可用性: {af_available}")
            except Exception as e:
                logger.warning(f"AlphaFold获取失败: {str(e)}")
            
            # 如果AlphaFold可用，使用AlphaFold
            if af_available:
                return {
                    "success": True,
                    "alphafold_available": True,
                    "pdb_ids": pdb_ids,
                    "structure_path": str(af_path),
                    "structure_source": "alphafold"
                }
            
            # 如果都没有找到，返回错误
            logger.warning(f"未找到{uniprot_acc}的结构，PDB和AlphaFold均不可用")
            return {
                "success": False,
                "error": f"未找到UniProt {uniprot_acc}对应的蛋白质结构（PDB和AlphaFold均不可用）",
                "alphafold_available": False,
                "pdb_ids": pdb_ids,
                "structure_source": None
            }
            
        except ValidationError as e:
            logger.error(f"请求验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "alphafold_available": False,
                "pdb_ids": [],
                "structure_source": None
            }
        except Exception as e:
            logger.error(f"获取结构来源失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "alphafold_available": False,
                "pdb_ids": [],
                "structure_source": None
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
    def get_ligands(uniprot_acc: Optional[str] = None, custom_smiles: Optional[List[str]] = None, disease: Optional[str] = None) -> Dict:
        """获取配体"""
        try:
            logger.info(f"🔍 [LIGAND_DEBUG] 开始获取配体，UniProt: {uniprot_acc}, 自定义SMILES: {custom_smiles}, 疾病: {disease}")

            # 验证请求
            RequestValidator.validate_ligand_request({
                "uniprot_acc": uniprot_acc,
                "custom_smiles": custom_smiles,
                "disease": disease
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
                logger.warning(f"❌ [LIGAND_DEBUG] 未从ChEMBL或默认列表获取到配体，尝试AI生成...")
                # 尝试使用AI生成
                protein_target = uniprot_acc if uniprot_acc else "a relevant protein target"
                disease_context = disease if disease else "a relevant disease"
                
                try:
                    smiles_list = api.ai_engine.generate_ligand_smiles(
                        protein_target=protein_target,
                        disease_context=disease_context,
                        num_smiles=10
                    )
                    logger.info(f"🤖 [LIGAND_DEBUG] AI生成了 {len(smiles_list)} 个配体")
                    
                    # 如果AI也未能生成，则返回最终错误
                    if not smiles_list:
                        logger.error(f"❌ [LIGAND_DEBUG] AI也未能生成任何配体")
                        return {
                            "success": False,
                            "error": "无法获取或生成任何配体"
                        }
                    
                    # 如果AI生成成功，将其标记为ai_generated
                    logger.info(f"✅ [LIGAND_DEBUG] 成功通过AI获取{len(smiles_list)}个配体")
                    return {
                        "success": True,
                        "ai_generated_smiles": smiles_list
                    }

                except Exception as ai_error:
                    logger.error(f"❌ [LIGAND_DEBUG] AI生成配体时出错: {ai_error}")
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
    
    @staticmethod
    def generate_scientific_analysis(workflow_data: Dict[str, Any]) -> Dict:
        """生成科学分析解释"""
        try:
            # 验证必要的工作流数据
            if not workflow_data.get("disease") or not workflow_data.get("gene_symbol"):
                return {
                    "success": False,
                    "error": "缺少必要的工作流数据"
                }
            
            api = DrugDiscoveryAPI()
            explanation = api.ai_engine.ai_explain_results(workflow_data)
            
            return {
                "success": True,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"生成科学分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_verified_target(self, disease: str) -> Dict:
        """获取已验证的靶点"""
        try:
            # 这里可以使用AI引擎来获取一个已验证的靶点
            # 作为备选方案，当常规靶点查找失败时使用
            
            # 常见疾病的已验证靶点映射
            verified_targets = {
                "癌症": {
                    "symbol": "EGFR",
                    "uniprot_acc": "P00533",
                    "name": "Epidermal growth factor receptor",
                    "innovation_score": 3
                },
                "阿尔茨海默病": {
                    "symbol": "APP",
                    "uniprot_acc": "P05067", 
                    "name": "Amyloid-beta precursor protein",
                    "innovation_score": 6
                },
                "糖尿病": {
                    "symbol": "INS",
                    "uniprot_acc": "P01308",
                    "name": "Insulin",
                    "innovation_score": 2
                },
                "高血压": {
                    "symbol": "ACE",
                    "uniprot_acc": "P12821",
                    "name": "Angiotensin-converting enzyme",
                    "innovation_score": 1
                }
            }
            
            # 默认靶点
            default_target = {
                "symbol": "TP53",
                "uniprot_acc": "P04637",
                "name": "Tumor protein p53",
                "innovation_score": 4
            }
            
            # 尝试匹配疾病
            target = None
            for disease_key, target_info in verified_targets.items():
                if disease_key in disease:
                    target = target_info
                    break
            
            if not target:
                target = default_target
            
            # 构造与UniProt entries相同的格式
            entries = [{
                "acc": target["uniprot_acc"],
                "name": target["name"]
            }]
            
            return {
                "success": True,
                "symbol": target["symbol"],
                "uniprot_acc": target["uniprot_acc"],
                "name": target["name"],
                "innovation_score": target["innovation_score"],
                "entries": entries
            }
            
        except Exception as e:
            logger.error(f"获取已验证靶点失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
