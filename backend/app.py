# backend/app.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import services_func, os
from pathlib import Path

app = FastAPI(
    title="Drug Discovery API",
    description="AI 全自动药物发现流程接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

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
    structure_path: Optional[str]  # 新增：实际下载到的文件路径

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

@app.post("/api/structure-sources", response_model=StructureSourcesResponse)
async def get_structure_sources(req: StructureRequest):
    try:
        # 把 download_alphafold 改成：download_alphafold(acc, dest_dir=TMP_DIR)
        # 它会返回下载文件的 Path（或 None）
        af_file = services_func.download_alphafold(req.uniprot_acc, dest_dir=services_func.TMP_DIR)
        pdb_ids = services_func.get_pdb_ids_for_uniprot(req.uniprot_acc)
        return {
            "success": True,
            "alphafold_available": af_file is not None,
            "pdb_ids": pdb_ids,
            "structure_path": str(af_file) if af_file else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        return services_func.DrugDiscoveryAPI.get_ligands(req.uniprot_acc, req.custom_smiles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-decision")
async def ai_decision(req: AIDecisionRequest):
    if not req.options or not req.question:
        raise HTTPException(status_code=400, detail="缺少 options 或 question 参数")
    try:
        return services_func.DrugDiscoveryAPI.ai_make_decision(req.options, req.context, req.question)
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
        return services_func.DrugDiscoveryAPI.complete_workflow(req.disease, req.selected_targets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/decision-explanations")
async def decision_explanations():
    try:
        return services_func.DrugDiscoveryAPI.get_decision_explanations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 运行: uvicorn backend.app:app --host 0.0.0.0 --port 5000 --reload
