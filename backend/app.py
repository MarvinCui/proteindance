# backend/app.py

import os
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Any
from dotenv import load_dotenv

# 防止tokenizers并行化死锁和设置多进程安全模式
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'  # 控制OpenMP线程数
os.environ['OPENBLAS_NUM_THREADS'] = '1'  # 控制OpenBLAS线程数
os.environ['MKL_NUM_THREADS'] = '1'  # 控制MKL线程数

# 防止PyMOL启动GUI模式导致进程挂起
os.environ['PYMOL_PATH'] = '/dev/null'
os.environ['DISPLAY'] = ''

# 加载环境变量
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Import organized backend services
from .services.drug_discovery_api import DrugDiscoveryAPI
from .services.auth_service import AuthService
from .core.config import settings
from .database.session_manager import session_manager
from .models.session import Session, SessionData, SessionMetadata
from .models.user import User, UserCreate, UserLogin, PasswordReset, PasswordResetConfirm, EmailVerification
from .middleware.auth_middleware import get_current_user, get_current_active_user, get_optional_user


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

# —— 静态文件服务 —— #
# 为temp目录提供静态文件访问
project_root = Path(__file__).parent.parent
temp_dir = project_root / "temp"
temp_dir.mkdir(exist_ok=True)
app.mount("/static/temp", StaticFiles(directory=str(temp_dir)), name="temp_static")


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
    structure_source: Optional[str] = None  # 结构来源：pdb或alphafold


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

class ScientificAnalysisRequest(BaseModel):
    disease: str
    gene_symbol: str
    uniprot_acc: Optional[str] = None
    structure_path: Optional[str] = None
    pocket_center: Optional[List[float]] = None
    smiles_list: Optional[List[str]] = None
    optimized_smiles: Optional[str] = None
    docking_result: Optional[dict] = None
    docking_score: Optional[float] = None


# —— Authentication API —— #

@app.post("/api/auth/register", summary="用户注册")
async def register_user(user_data: UserCreate):
    """
    用户注册
    """
    try:
        auth_service = AuthService()
        result = auth_service.register(user_data)
        return result
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@app.post("/api/auth/login", summary="用户登录")
async def login_user(login_data: UserLogin):
    """
    用户登录
    """
    try:
        auth_service = AuthService()
        result = auth_service.login(login_data)
        return result
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@app.post("/api/auth/verify-email", summary="验证邮箱")
async def verify_email(verification: EmailVerification):
    """
    验证用户邮箱
    """
    try:
        auth_service = AuthService()
        result = auth_service.verify_email(verification.token)
        return result
    except Exception as e:
        logger.error(f"邮箱验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

@app.post("/api/auth/request-password-reset", summary="请求密码重置")
async def request_password_reset(reset_request: PasswordReset):
    """
    请求密码重置
    """
    try:
        auth_service = AuthService()
        result = auth_service.request_password_reset(reset_request.email)
        return result
    except Exception as e:
        logger.error(f"密码重置请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置请求失败: {str(e)}")

@app.post("/api/auth/reset-password", summary="重置密码")
async def reset_password(reset_data: PasswordResetConfirm):
    """
    重置密码
    """
    try:
        auth_service = AuthService()
        result = auth_service.reset_password(reset_data.token, reset_data.new_password)
        return result
    except Exception as e:
        logger.error(f"密码重置失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")

@app.get("/api/auth/me", summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    """
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "status": current_user.status,
            "email_verified": current_user.email_verified,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
    }

@app.post("/api/auth/resend-verification", summary="重新发送验证邮件")
async def resend_verification_email(current_user: User = Depends(get_current_user)):
    """
    重新发送邮箱验证邮件
    """
    try:
        auth_service = AuthService()
        result = auth_service.resend_verification_email(current_user.id)
        return result
    except Exception as e:
        logger.error(f"重新发送验证邮件失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")

# —— Session Management API —— #

@app.post("/api/sessions", response_model=Session, summary="保存或更新会话")
async def save_or_update_session(
    session_data: SessionData, 
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    保存一个新的会话或更新一个现有会话。
    - 如果提供了 session_id，则更新现有会话。
    - 如果未提供 session_id，则创建新会话。
    - 会话将与当前登录用户关联。
    """
    try:
        session = session_manager.save_session(session_data, session_id, current_user.id)
        return session
    except Exception as e:
        logger.error(f"保存会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"无法保存会话: {str(e)}")

@app.get("/api/sessions", response_model=List[SessionMetadata], summary="列出会话")
async def list_sessions(current_user: User = Depends(get_current_user)):
    """
    获取会话的元数据列表（ID, 标题, 更新时间），按更新时间降序排列。
    只返回当前登录用户的会话。
    """
    try:
        return session_manager.list_sessions(current_user.id)
    except Exception as e:
        logger.error(f"列出会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"无法列出会话: {str(e)}")

@app.get("/api/sessions/{session_id}", response_model=Session, summary="获取特定会话")
async def get_session(session_id: str, current_user: User = Depends(get_current_user)):
    """
    通过ID获取一个完整的会话数据。
    用户只能访问自己的会话。
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")
    
    # 检查权限：用户只能访问自己的会话
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    return session

@app.delete("/api/sessions/{session_id}", status_code=204, summary="删除会话")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    """
    通过ID删除一个会话。
    用户只能删除自己的会话。
    """
    # 先获取会话检查权限
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="要删除的会话未找到")
    
    # 检查权限：用户只能删除自己的会话
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此会话")
    
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="要删除的会话未找到")
    return None


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

@app.post("/api/smiles-to-3d")
async def smiles_to_3d(request: dict):
    """将SMILES转换为3D分子结构"""
    try:
        smiles = request.get('smiles')
        if not smiles:
            raise HTTPException(status_code=400, detail="缺少SMILES参数")
        
        from rdkit import Chem
        from rdkit.Chem import AllChem
        
        # 生成分子对象
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"success": False, "error": "SMILES格式错误"}
        
        # 添加氢原子
        mol = Chem.AddHs(mol)
        
        # 生成3D坐标
        result = AllChem.EmbedMolecule(mol, randomSeed=42)
        if result != 0:
            # 如果失败，尝试使用强制方法
            AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=42)
        
        # 优化分子几何结构
        try:
            AllChem.UFFOptimizeMolecule(mol, maxIters=200)
        except:
            # 如果优化失败，继续使用未优化的结构
            pass
        
        # 转换为SDF格式
        sdf_data = Chem.MolToMolBlock(mol)
        
        return {
            "success": True,
            "mol_data": sdf_data,
            "smiles": smiles
        }
        
    except Exception as e:
        logger.error(f"SMILES转3D失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


class DockingRequest(BaseModel):
    protein_path: str
    ligand_smiles: str
    pocket_center: List[float]
    box_size: Optional[List[float]] = None

@app.post("/api/molecular-docking")
async def molecular_docking(req: DockingRequest):
    """执行分子对接"""
    try:
        api = DrugDiscoveryAPI()
        result = api.pharma_engine.perform_molecular_docking(
            protein_path=Path(req.protein_path),
            ligand_smiles=req.ligand_smiles,
            pocket_center=req.pocket_center,
            box_size=req.box_size
        )
        return result
    except Exception as e:
        logger.error(f"分子对接失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/docking-visualization")
async def docking_visualization(req: DockingRequest, current_user: User = Depends(get_optional_user)):
    """生成对接结果可视化"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 开始分子对接可视化流程")
        logger.info(f"📁 蛋白质文件: {req.protein_path}")
        logger.info(f"🧬 配体SMILES: {req.ligand_smiles[:50]}...")
        logger.info(f"📍 口袋中心: {req.pocket_center}")
        logger.info(f"📦 盒子大小: {req.box_size}")
        
        # 创建基于会话的输出目录
        project_root = Path(__file__).parent.parent
        temp_base = project_root / "temp"
        temp_base.mkdir(exist_ok=True)
        
        # 使用用户ID和时间戳创建唯一的会话目录
        import time
        session_timestamp = int(time.time())
        user_id = current_user.id if current_user else "anonymous"
        session_dir = temp_base / f"{user_id}_{session_timestamp}"
        session_dir.mkdir(exist_ok=True)
        
        logger.info(f"📂 会话输出目录: {session_dir}")
        
        api = DrugDiscoveryAPI()
        logger.info("✅ DrugDiscoveryAPI 实例创建成功")
        
        # 执行对接（使用成熟的DockingEngine）
        logger.info("🔬 开始执行分子对接...")
        docking_result = api.pharma_engine.perform_molecular_docking(
            protein_path=Path(req.protein_path),
            ligand_smiles=req.ligand_smiles,
            pocket_center=req.pocket_center,
            box_size=req.box_size,
            output_dir=session_dir  # 传递会话目录
        )
        logger.info("✅ 分子对接执行完成")
        logger.info(f"📊 对接结果keys: {list(docking_result.keys()) if docking_result else 'None'}")
        
        if docking_result:
            logger.info(f"✅ 对接成功状态: {docking_result.get('success', False)}")
            logger.info(f"🎯 最佳得分: {docking_result.get('best_score', 'N/A')}")
            logger.info(f"🔢 构象数量: {len(docking_result.get('poses', []))}")
            logger.info(f"🎭 可视化数据: {bool(docking_result.get('visualization'))}")
        else:
            logger.error("❌ 对接结果为空")
        
        # 处理成熟对接引擎的结果
        if docking_result.get("success") and docking_result.get("visualization"):
            logger.info("🎨 开始处理可视化结果...")
            # 从成熟对接系统获取PyMOL图像
            pymol_images = docking_result["visualization"].get("images", [])
            logger.info(f"🖼️ PyMOL图像数量: {len(pymol_images)}")
            if pymol_images:
                logger.info(f"📷 图像路径示例: {pymol_images[0] if pymol_images else 'None'}")
            
            # 转换绝对路径为相对URL
            def convert_to_static_url(file_path: str) -> str:
                """将绝对文件路径转换为静态文件URL"""
                try:
                    path_obj = Path(file_path)
                    temp_base = project_root / "temp"
                    relative_path = path_obj.relative_to(temp_base)
                    return f"/static/temp/{relative_path}"
                except Exception as e:
                    logger.warning(f"无法转换图像路径: {file_path}, 错误: {e}")
                    return file_path
            
            # 转换图像路径为URL
            pymol_image_urls = [convert_to_static_url(img) for img in pymol_images]
            logger.info(f"🔗 转换后的图像URL示例: {pymol_image_urls[0] if pymol_image_urls else 'None'}")
            
            # 创建兼容的可视化结果
            logger.info("📦 创建可视化结果数据包...")
            visualization_result = {
                "success": True,
                "html_content": "<html><body><h1>PyMOL Visualization Available</h1><p>Please check the PyMOL images section for professional visualization.</p></body></html>",
                "docking_summary": {
                    "ligand_smiles": req.ligand_smiles,
                    "best_score": docking_result.get("best_score", 0.0),
                    "num_poses": len(docking_result.get("poses", [])),
                    "pocket_center": req.pocket_center
                },
                "images": pymol_image_urls,  # PyMOL图像URL列表
                "pymol_analysis": {
                    "ki_estimate": docking_result.get("analysis", {}).get("ki_estimate", "N/A"),
                    "ic50_prediction": docking_result.get("analysis", {}).get("ic50_prediction", "N/A"),
                    "binding_analysis": docking_result.get("analysis", {}).get("binding_analysis", "Professional PyMOL analysis completed")
                }
            }
            
            # 转换对接结果格式以匹配前端期望
            processed_docking_result = {
                "success": True,
                "best_score": docking_result.get("best_score", 0.0),
                "num_poses": len(docking_result.get("poses", [])),
                "poses": []
            }
            
            # 转换构象数据
            for i, pose in enumerate(docking_result.get("poses", [])):
                processed_docking_result["poses"].append({
                    "pose_id": i + 1,
                    "binding_affinity": pose.get("binding_affinity", 0.0),
                    "rmsd_lower": pose.get("rmsd_lower", 0.0),
                    "rmsd_upper": pose.get("rmsd_upper", 0.0)
                })
            
            final_result = {
                "success": True,
                "docking_result": processed_docking_result,
                "visualization": visualization_result,
                "output_directory": str(session_dir)  # 添加输出目录信息
            }
            
            logger.info("🎉 成功创建最终结果数据包")
            logger.info(f"📤 返回数据包大小: {len(str(final_result))} 字符")
            logger.info(f"📁 可视化文件保存在: {session_dir}")
            logger.info("=" * 60)
            
            return final_result
        else:
            # 如果成熟对接失败，尝试生成基础可视化
            if docking_result.get("docking_file") and docking_result.get("receptor_file"):
                visualization_result = api.visualization_engine.generate_docking_visualization(
                    protein_file=docking_result["receptor_file"],
                    ligand_file=docking_result["ligand_file"],
                    output_dir=docking_result.get("output_dir", "/tmp/docking_viz")
                )
            else:
                visualization_result = {
                    "success": False,
                    "error": "Unable to generate visualization - missing required files"
                }
            
            return {
                "success": docking_result.get("success", False),
                "docking_result": docking_result,
                "visualization": visualization_result
            }
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ 对接可视化过程中发生异常")
        logger.error(f"🚨 错误类型: {type(e).__name__}")
        logger.error(f"📄 错误消息: {str(e)}")
        import traceback
        logger.error(f"📚 完整堆栈: {traceback.format_exc()}")
        logger.error("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/docking-image")
async def generate_docking_image(req: DockingRequest):
    """生成分子对接静态图像"""
    try:
        api = DrugDiscoveryAPI()
        
        # 生成对接图像
        docking_image = api.visualization_engine.generate_docking_image(
            protein_pdb_path=req.protein_path,
            ligand_smiles=req.ligand_smiles,
            pocket_center=req.pocket_center
        )
        
        if docking_image:
            return {
                "success": True,
                "image_data": docking_image
            }
        else:
            return {
                "success": False,
                "error": "对接图像生成失败"
            }
        
    except Exception as e:
        logger.error(f"对接图像生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/scientific-analysis")
async def scientific_analysis(req: ScientificAnalysisRequest):
    if not req.disease or not req.gene_symbol:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    try:
        # 构建工作流数据
        workflow_data = {
            "disease": req.disease,
            "gene_symbol": req.gene_symbol,
            "uniprot_acc": req.uniprot_acc,
            "structure_path": req.structure_path,
            "pocket_center": req.pocket_center,
            "smiles_list": req.smiles_list or [],
            "optimized_smiles": req.optimized_smiles,
            "docking_result": req.docking_result,
            "docking_score": req.docking_score
        }
        return DrugDiscoveryAPI.generate_scientific_analysis(workflow_data)
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


@app.get("/api/download/ligand/{session_id}", summary="下载配体文件")
async def download_ligand_file(
    session_id: str,
    ligand_type: str = "optimized",  # "original" or "optimized"
    file_format: str = "pdb",        # "pdb" or "pdbqt"
    ligand_index: int = 0,           # 用于原始配体数组的索引
    current_user: User = Depends(get_current_user)
):
    """
    下载配体文件
    
    Args:
        session_id: 会话ID
        ligand_type: 配体类型 ("original" 或 "optimized")
        file_format: 文件格式 ("pdb" 或 "pdbqt")
        ligand_index: 原始配体数组索引（仅当ligand_type="original"时使用）
        current_user: 当前用户
    
    Returns:
        配体文件下载
    """
    try:
        # 获取会话数据
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话未找到")
        
        # 检查权限
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        # 获取SMILES数据
        smiles_data = None
        if ligand_type == "original":
            if hasattr(session.session_data, 'currentLigandSmiles') and session.session_data.currentLigandSmiles:
                if ligand_index < len(session.session_data.currentLigandSmiles):
                    smiles_data = session.session_data.currentLigandSmiles[ligand_index]
                else:
                    raise HTTPException(status_code=404, detail=f"配体索引{ligand_index}超出范围")
            else:
                raise HTTPException(status_code=404, detail="原始配体数据未找到")
        elif ligand_type == "optimized":
            if hasattr(session.session_data, 'currentOptimizedSmiles') and session.session_data.currentOptimizedSmiles:
                smiles_data = session.session_data.currentOptimizedSmiles
            else:
                raise HTTPException(status_code=404, detail="优化配体数据未找到")
        else:
            raise HTTPException(status_code=400, detail="无效的配体类型")
        
        if not smiles_data:
            raise HTTPException(status_code=404, detail="配体数据为空")
        
        # 创建PharmaEngine实例进行转换
        api = DrugDiscoveryAPI()
        pharma_engine = api.pharma_engine
        
        # 构建文件名
        if ligand_type == "original":
            filename = f"original_ligand_{ligand_index + 1}.{file_format}"
        else:
            filename = f"optimized_ligand.{file_format}"
        
        # 根据格式转换SMILES
        if file_format == "pdb":
            file_path = pharma_engine.smiles_to_pdb(smiles_data, filename.split('.')[0])
        elif file_format == "pdbqt":
            file_path = pharma_engine.smiles_to_pdbqt(smiles_data, filename.split('.')[0])
        else:
            raise HTTPException(status_code=400, detail="无效的文件格式")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载配体文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文件时发生错误: {str(e)}")


@app.get("/api/download/structure/{session_id}", summary="下载蛋白质结构文件")
async def download_structure_file(
    session_id: str,
    file_format: str = "pdb",  # "pdb" 或 "pdbqt"
    current_user: User = Depends(get_current_user)
):
    """
    下载蛋白质结构文件
    
    Args:
        session_id: 会话ID
        file_format: 文件格式 ("pdb" 或 "pdbqt")
        current_user: 当前用户
    
    Returns:
        蛋白质结构文件下载
    """
    try:
        # 获取会话数据
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话未找到")
        
        # 检查权限
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        # 获取结构文件路径
        structure_path = None
        if hasattr(session.session_data, 'currentStructurePath') and session.session_data.currentStructurePath:
            structure_path = session.session_data.currentStructurePath
        elif hasattr(session.session_data, 'workflowState') and session.session_data.workflowState:
            structure_path = session.session_data.workflowState.get('structure_path')
        
        if not structure_path:
            raise HTTPException(status_code=404, detail="结构文件路径未找到")
        
        # 验证文件存在
        file_path = Path(structure_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="结构文件不存在")
        
        # 安全检查：只允许访问临时目录中的文件
        if not str(file_path.resolve()).startswith(str(settings.TMP_DIR.resolve())):
            raise HTTPException(status_code=403, detail="无权访问该文件")
        
        # 验证文件格式
        if file_format not in ["pdb", "pdbqt"]:
            raise HTTPException(status_code=400, detail="无效的文件格式")
        
        # 创建PharmaEngine实例进行格式转换
        api = DrugDiscoveryAPI()
        pharma_engine = api.pharma_engine
        
        # 构建文件名
        filename = f"protein_structure_{session_id[:8]}.{file_format}"
        
        # 根据格式转换文件
        converted_path = pharma_engine.convert_protein_structure(
            file_path, 
            file_format, 
            f"protein_structure_{session_id[:8]}"
        )
        
        # 返回文件
        return FileResponse(
            path=converted_path,
            media_type="application/octet-stream",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载结构文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文件时发生错误: {str(e)}")

@app.get("/api/images/{image_path:path}", summary="获取PyMOL生成的图像")
async def get_pymol_image(image_path: str):
    """
    获取PyMOL生成的分子对接图像
    
    Args:
        image_path: 图像文件路径（相对于输出目录）
    """
    try:
        # 安全性检查：确保路径不包含恶意字符
        if ".." in image_path:
            raise HTTPException(status_code=400, detail="无效的图像路径")
        
        # 如果是绝对路径，直接检查该文件是否存在
        if image_path.startswith("/"):
            absolute_path = Path(image_path)
            if absolute_path.exists() and absolute_path.is_file():
                # 验证是图像文件
                if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    raise HTTPException(status_code=400, detail="不支持的图像格式")
                
                return FileResponse(
                    path=absolute_path,
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"}
                )
            else:
                raise HTTPException(status_code=404, detail="图像文件不存在")
        
        # 查找图像文件（优先在项目temp目录中搜索）
        project_root = Path(__file__).parent.parent
        temp_base = project_root / "temp"
        
        possible_dirs = [
            temp_base,  # 项目temp目录
            settings.TMP_DIR,
            settings.TMP_DIR / "docking_results", 
            Path(tempfile.gettempdir()) / "drug_flow"
        ]
        
        image_file = None
        for base_dir in possible_dirs:
            potential_path = base_dir / image_path
            if potential_path.exists() and potential_path.is_file():
                image_file = potential_path
                break
            
            # 也搜索子目录
            for subdir in base_dir.glob("*/"):
                if subdir.is_dir():
                    potential_path = subdir / image_path
                    if potential_path.exists() and potential_path.is_file():
                        image_file = potential_path
                        break
        
        if not image_file:
            raise HTTPException(status_code=404, detail="图像文件不存在")
        
        # 验证是图像文件
        if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            raise HTTPException(status_code=400, detail="不支持的图像格式")
        
        # 返回图像文件
        return FileResponse(
            path=image_file,
            media_type="image/png",  # 大部分PyMOL图像都是PNG
            headers={"Cache-Control": "public, max-age=3600"}  # 缓存1小时
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图像时发生错误: {str(e)}")


# —— 启动指令 —— #
# uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload
