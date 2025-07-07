# backend/app.py

import os
import logging
from pathlib import Path
from typing import List, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Import organized backend services
from .services.drug_discovery_api import DrugDiscoveryAPI
from .core.config import settings


# —— FastAPI 实例化 —— #
app = FastAPI(
    title="Drug Discovery API",
    description="AI 全自动药物发现流程接口",
    version="1.0.0"
)

# —— 全局中间件（CORS）—— #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 开发时允许所有源，生产请锁域名
    allow_methods=["*"],
    allow_headers=["*"],
)


# —— Pydantic 请求/响应模型 —— #
class DiseaseRequest(BaseModel):
    disease: str
    innovation_level: int = 5  # 默认创新度为5


class UniprotRequest(BaseModel):
    gene_symbol: str


class StructureRequest(BaseModel):
    uniprot_acc: str


class StructureSourcesResponse(BaseModel):
    success: bool
    alphafold_available: bool
    pdb_ids: List[str]
    structure_path: Optional[str] = None  # 实际下载到的文件路径


class PredictPocketsRequest(BaseModel):
    structure_path: str


class LigandsRequest(BaseModel):
    uniprot_acc: Optional[str] = None
    custom_smiles: Optional[List[str]] = None
    disease: Optional[str] = None


class AIDecisionRequest(BaseModel):
    options: List[str]
    context: Optional[str] = ""
    question: str


class SelectCompoundRequest(BaseModel):
    smiles_list: List[str]
    disease: str
    protein: str
    pocket_center: Optional[Any] = None


class MoleculeImageRequest(BaseModel):
    smiles: str

 # class DockingImageRequest(BaseModel):
 #     protein_path: str
 #     ligand_smiles: str
 #     pocket_center: Any

class CompleteWorkflowRequest(BaseModel):
    disease: str
    selected_targets: Optional[List[str]] = None


# —— 路由实现 —— #

@app.post("/api/disease-targets")
async def get_disease_targets(req: DiseaseRequest):
    try:
        return DrugDiscoveryAPI.get_disease_targets(
            req.disease,
            innovation_level=req.innovation_level
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/uniprot-entries")
async def get_uniprot_entries(req: UniprotRequest):
    try:
        return DrugDiscoveryAPI.get_uniprot_entries(req.gene_symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/structure-sources",
    response_model=StructureSourcesResponse,
    summary="获取 AlphaFold & PDB 结构来源"
)
async def get_structure_sources(req: StructureRequest):
    """
    1) 先尝试下载 AlphaFold 预测结构，
    2) 再查询 PDB ID 列表，
    3) 返回是否可用 + 实际下载到的文件路径（如果有）。
    """
    try:
        return DrugDiscoveryAPI.get_structure_sources(req.uniprot_acc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/target-explanation")
async def target_explanation(req: dict):
    try:
        gene_symbol = req.get("gene_symbol")
        disease = req.get("disease")
        if not gene_symbol or not disease:
            raise HTTPException(status_code=400, detail="缺少gene_symbol或disease参数")

        api = DrugDiscoveryAPI()
        explanation = api.ai_engine.generate_target_explanation(gene_symbol, disease)
        return {
            "success": True,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verified-target")
async def get_verified_target(req: dict):
    try:
        disease = req.get("disease")
        if not disease:
            raise HTTPException(status_code=400, detail="缺少disease参数")

        # 使用DrugDiscoveryAPI获取已验证的靶点
        api = DrugDiscoveryAPI()
        result = api.get_verified_target(disease)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download-structure")
async def download_structure(req: dict):
    try:
        return DrugDiscoveryAPI.download_structure(
            pdb_id=req.get("pdb_id"),
            uniprot_acc=req.get("uniprot_acc"),
            source_type=req.get("source_type", "pdb")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict-pockets")
async def predict_pockets(req: PredictPocketsRequest):
    try:
        return DrugDiscoveryAPI.predict_pockets(req.structure_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/get-ligands")
async def get_ligands(req: LigandsRequest):
    if not req.uniprot_acc and not req.custom_smiles:
        raise HTTPException(status_code=400, detail="必须提供 uniprot_acc 或 custom_smiles")
    try:
        return DrugDiscoveryAPI.get_ligands(
            req.uniprot_acc, req.custom_smiles, req.disease
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai-decision")
async def ai_decision(req: AIDecisionRequest):
    if not req.options or not req.question:
        raise HTTPException(status_code=400, detail="缺少 options 或 question 参数")
    try:
        return DrugDiscoveryAPI.ai_make_decision(
            req.options, req.context, req.question
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/select-compound")
async def select_compound(req: SelectCompoundRequest):
    if not req.smiles_list or not req.disease or not req.protein:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    try:
        return DrugDiscoveryAPI.select_best_compound(
            req.smiles_list, req.disease, req.protein, req.pocket_center
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/molecule-image")
async def molecule_image(req: MoleculeImageRequest):
    if not req.smiles:
        raise HTTPException(status_code=400, detail="缺少 smiles 参数")
    try:
        return DrugDiscoveryAPI.generate_molecule_image(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/docking-image")
# async def docking_image(req: DockingImageRequest):
#     if not (req.protein_path and req.ligand_smiles and req.pocket_center):
#         raise HTTPException(status_code=400, detail="缺少 docking 所需参数")
#     try:
#         return services_func.DrugDiscoveryAPI.generate_docking_image(
#             req.protein_path, req.ligand_smiles, req.pocket_center
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/complete-workflow")
async def complete_workflow(req: CompleteWorkflowRequest):
    if not req.disease:
        raise HTTPException(status_code=400, detail="缺少 disease 参数")
    try:
        return DrugDiscoveryAPI.complete_workflow(
            req.disease, req.selected_targets
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decision-explanations")
async def decision_explanations():
    try:
        return DrugDiscoveryAPI.get_decision_explanations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/structure/{structure_identifier:path}")
async def get_structure_file(structure_identifier: str):
    """
    获取蛋白质结构文件内容用于3D可视化
    支持PDB ID (如 1B8M) 或完整文件路径
    """
    try:
        import urllib.parse
        import glob
        
        decoded_identifier = urllib.parse.unquote(structure_identifier)
        
        # 如果是完整路径，直接使用
        if decoded_identifier.startswith('/'):
            file_path = Path(decoded_identifier)
        else:
            # 如果是PDB ID，在临时目录中查找对应文件
            pdb_id = decoded_identifier.upper()
            
            # 可能的文件名格式
            possible_patterns = [
                f"pdb{pdb_id.lower()}.ent",  # pdb1b8m.ent
                f"{pdb_id.lower()}.pdb",     # 1b8m.pdb  
                f"{pdb_id.upper()}.pdb",     # 1B8M.pdb
                f"pdb{pdb_id.upper()}.ent",  # pdb1B8M.ent
            ]
            
            file_path = None
            # 在临时目录中搜索
            search_dir = settings.TMP_DIR
            for pattern in possible_patterns:
                matches = glob.glob(str(search_dir / "**" / pattern), recursive=True)
                if matches:
                    file_path = Path(matches[0])
                    break
            
            if not file_path:
                raise HTTPException(
                    status_code=404, 
                    detail=f"未找到结构文件: {structure_identifier}. 搜索目录: {search_dir}"
                )
        
        # 验证文件存在
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"结构文件不存在: {file_path}")
        
        # 安全检查：只允许访问临时目录中的文件
        if not str(file_path.resolve()).startswith(str(settings.TMP_DIR.resolve())):
            raise HTTPException(status_code=403, detail="无权访问该文件")
        
        # 返回文件内容
        return FileResponse(
            path=file_path,
            media_type="text/plain",
            filename=file_path.name
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取结构文件时发生错误: {str(e)}")


@app.get("/api/structure-debug/{structure_identifier:path}")
async def debug_structure_file(structure_identifier: str):
    """
    调试结构文件访问 - 显示详细信息
    """
    try:
        import urllib.parse
        import glob
        
        decoded_identifier = urllib.parse.unquote(structure_identifier)
        
        debug_info = {
            "identifier": structure_identifier,
            "decoded": decoded_identifier,
            "tmp_dir": str(settings.TMP_DIR),
            "tmp_dir_exists": settings.TMP_DIR.exists(),
            "found_files": [],
            "searched_patterns": []
        }
        
        # 如果是PDB ID，在临时目录中查找对应文件
        if not decoded_identifier.startswith('/'):
            pdb_id = decoded_identifier.upper()
            
            # 可能的文件名格式
            possible_patterns = [
                f"pdb{pdb_id.lower()}.ent",  # pdb1b8m.ent
                f"{pdb_id.lower()}.pdb",     # 1b8m.pdb  
                f"{pdb_id.upper()}.pdb",     # 1B8M.pdb
                f"pdb{pdb_id.upper()}.ent",  # pdb1B8M.ent
            ]
            
            search_dir = settings.TMP_DIR
            for pattern in possible_patterns:
                debug_info["searched_patterns"].append(f"{search_dir}/**/{pattern}")
                matches = glob.glob(str(search_dir / "**" / pattern), recursive=True)
                if matches:
                    debug_info["found_files"].extend(matches)
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/protein-visualization")
async def generate_protein_visualization(req: dict):
    """
    生成蛋白质3D可视化HTML
    """
    try:
        structure_path = req.get("structure_path")
        pocket_center = req.get("pocket_center")
        
        if not structure_path:
            raise HTTPException(status_code=400, detail="缺少structure_path参数")
        
        # 使用后端可视化引擎
        api = DrugDiscoveryAPI()
        
        # 读取结构文件
        file_path = Path(structure_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="结构文件不存在")
        
        with open(file_path, 'r') as f:
            pdb_data = f.read()
        
        # 生成3D查看器HTML
        html = api.visualization_engine.generate_3d_viewer(
            smiles=None,  # 仅显示蛋白质
            pdb_data=pdb_data
        )
        
        # 可以在未来版本中使用pocket_center添加口袋标记
        if pocket_center:
            logger.info(f"口袋中心坐标: {pocket_center}")
        
        return {
            "success": True,
            "html": html,
            "structure_path": structure_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# —— 启动指令 —— #
# uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
