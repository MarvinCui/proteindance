# backend/app.py

import os
from pathlib import Path
from typing import List, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import services_func


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


class DockingImageRequest(BaseModel):
    protein_path: str
    ligand_smiles: str
    pocket_center: Any


class CompleteWorkflowRequest(BaseModel):
    disease: str
    selected_targets: Optional[List[str]] = None


# —— 路由实现 —— #

@app.post("/api/disease-targets")
async def get_disease_targets(req: DiseaseRequest):
    try:
        return services_func.DrugDiscoveryAPI.get_disease_targets(req.disease)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/uniprot-entries")
async def get_uniprot_entries(req: UniprotRequest):
    try:
        return services_func.DrugDiscoveryAPI.get_uniprot_entries(req.gene_symbol)
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
        # 下载 AlphaFold 预测模型（返回 Path 或 None）
        af_path: Optional[Path] = services_func.download_alphafold(
            req.uniprot_acc, dest_dir=services_func.TMP_DIR
        )

        # 查询该 accession 对应的 PDB 列表
        pdb_ids: List[str] = services_func.get_pdb_ids_for_uniprot(req.uniprot_acc)

        return StructureSourcesResponse(
            success=True,
            alphafold_available=(af_path is not None),
            pdb_ids=pdb_ids,
            structure_path=str(af_path) if af_path else None
        )
    except Exception as e:
        # 500 错误返回
        raise HTTPException(status_code=500, detail=f"获取结构来源失败：{e}")


@app.post("/api/predict-pockets")
async def predict_pockets(req: PredictPocketsRequest):
    try:
        return services_func.DrugDiscoveryAPI.predict_pockets(req.structure_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/get-ligands")
async def get_ligands(req: LigandsRequest):
    if not req.uniprot_acc and not req.custom_smiles:
        raise HTTPException(status_code=400, detail="必须提供 uniprot_acc 或 custom_smiles")
    try:
        return services_func.DrugDiscoveryAPI.get_ligands(
            req.uniprot_acc, req.custom_smiles
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai-decision")
async def ai_decision(req: AIDecisionRequest):
    if not req.options or not req.question:
        raise HTTPException(status_code=400, detail="缺少 options 或 question 参数")
    try:
        return services_func.DrugDiscoveryAPI.ai_make_decision(
            req.options, req.context, req.question
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/select-compound")
async def select_compound(req: SelectCompoundRequest):
    if not req.smiles_list or not req.disease or not req.protein:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    try:
        return services_func.DrugDiscoveryAPI.select_best_compound(
            req.smiles_list, req.disease, req.protein, req.pocket_center
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/molecule-image")
async def molecule_image(req: MoleculeImageRequest):
    if not req.smiles:
        raise HTTPException(status_code=400, detail="缺少 smiles 参数")
    try:
        return services_func.DrugDiscoveryAPI.generate_molecule_image(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/docking-image")
async def docking_image(req: DockingImageRequest):
    if not (req.protein_path and req.ligand_smiles and req.pocket_center):
        raise HTTPException(status_code=400, detail="缺少 docking 所需参数")
    try:
        return services_func.DrugDiscoveryAPI.generate_docking_image(
            req.protein_path, req.ligand_smiles, req.pocket_center
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/complete-workflow")
async def complete_workflow(req: CompleteWorkflowRequest):
    if not req.disease:
        raise HTTPException(status_code=400, detail="缺少 disease 参数")
    try:
        return services_func.DrugDiscoveryAPI.complete_workflow(
            req.disease, req.selected_targets
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decision-explanations")
async def decision_explanations():
    try:
        return services_func.DrugDiscoveryAPI.get_decision_explanations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# —— 启动指令 —— #
# uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
