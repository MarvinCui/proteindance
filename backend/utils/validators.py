"""
数据验证工具
"""
import re
from typing import List, Optional
from pathlib import Path
from ..models.exceptions import ValidationError


def validate_disease_name(disease: str) -> bool:
    """验证疾病名称"""
    if not disease or not disease.strip():
        return False
    
    # 基本长度检查
    if len(disease.strip()) < 2 or len(disease.strip()) > 100:
        return False
    
    return True


def validate_gene_symbol(gene_symbol: str) -> bool:
    """验证基因符号"""
    if not gene_symbol or not gene_symbol.strip():
        return False
    
    # 基因符号通常是2-12个字符，包含字母、数字、连字符
    pattern = r'^[A-Za-z][A-Za-z0-9_-]{1,11}$'
    return bool(re.match(pattern, gene_symbol.strip()))


def validate_uniprot_id(uniprot_id: str) -> bool:
    """验证UniProt ID"""
    if not uniprot_id or not uniprot_id.strip():
        return False
    
    # UniProt ID格式: 6-10个字符，字母数字组合
    pattern = r'^[A-Za-z0-9]{6,10}$'
    return bool(re.match(pattern, uniprot_id.strip()))


def validate_pdb_id(pdb_id: str) -> bool:
    """验证PDB ID"""
    if not pdb_id or not pdb_id.strip():
        return False
    
    # PDB ID格式: 4个字符，数字+字母
    pattern = r'^[0-9][A-Za-z0-9]{3}$'
    return bool(re.match(pattern, pdb_id.strip().upper()))


def validate_smiles(smiles: str) -> bool:
    """验证SMILES字符串"""
    if not smiles or not smiles.strip():
        return False
    
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles.strip())
        return mol is not None
    except ImportError:
        # 如果没有rdkit，进行基本验证
        # SMILES应该包含有效的化学符号
        valid_chars = set('CNOPSFClBrI()[]=#-+@/\\0123456789cnops')
        return all(c in valid_chars for c in smiles.strip())


def validate_coordinates(coords: List[float]) -> bool:
    """验证3D坐标"""
    if not coords or len(coords) != 3:
        return False
    
    try:
        # 检查是否为有效数字
        for coord in coords:
            float(coord)
        return True
    except (ValueError, TypeError):
        return False


def validate_file_path(file_path: str, extensions: Optional[List[str]] = None) -> bool:
    """验证文件路径"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🔍 [VALIDATOR] 验证文件路径: {file_path}")

    if not file_path:
        logger.error(f"❌ [VALIDATOR] 文件路径为空")
        return False

    path = Path(file_path)
    logger.info(f"🔍 [VALIDATOR] Path对象: {path}")
    logger.info(f"🔍 [VALIDATOR] 文件存在: {path.exists()}")
    logger.info(f"🔍 [VALIDATOR] 是否为文件: {path.is_file()}")
    logger.info(f"🔍 [VALIDATOR] 文件扩展名: {path.suffix}")

    # 检查文件是否存在
    if not path.exists():
        logger.error(f"❌ [VALIDATOR] 文件不存在: {path}")
        return False

    if not path.is_file():
        logger.error(f"❌ [VALIDATOR] 不是文件: {path}")
        return False

    # 检查文件扩展名
    if extensions:
        logger.info(f"🔍 [VALIDATOR] 允许的扩展名: {extensions}")
        valid_ext = path.suffix.lower() in [ext.lower() for ext in extensions]
        logger.info(f"🔍 [VALIDATOR] 扩展名验证结果: {valid_ext}")
        return valid_ext

    logger.info(f"✅ [VALIDATOR] 文件路径验证通过")
    return True


def validate_pocket_data(pocket_data: dict) -> bool:
    """验证口袋数据"""
    required_fields = ['pocket_id', 'center', 'score']
    
    # 检查必需字段
    for field in required_fields:
        if field not in pocket_data:
            return False
    
    # 验证中心坐标
    if not validate_coordinates(pocket_data['center']):
        return False
    
    # 验证分数
    try:
        score = float(pocket_data['score'])
        if score < 0 or score > 100:  # 假设分数范围0-100
            return False
    except (ValueError, TypeError):
        return False
    
    return True


def validate_compound_data(compound_data: dict) -> bool:
    """验证化合物数据"""
    # 必须有SMILES
    if 'smiles' not in compound_data:
        return False
    
    if not validate_smiles(compound_data['smiles']):
        return False
    
    # 验证分子性质（如果存在）
    numeric_fields = ['molecular_weight', 'logp', 'hbd', 'hba', 'tpsa']
    for field in numeric_fields:
        if field in compound_data:
            try:
                value = float(compound_data[field])
                # 基本范围检查
                if field == 'molecular_weight' and (value < 0 or value > 2000):
                    return False
                elif field == 'logp' and (value < -10 or value > 10):
                    return False
                elif field in ['hbd', 'hba'] and (value < 0 or value > 50):
                    return False
                elif field == 'tpsa' and (value < 0 or value > 500):
                    return False
            except (ValueError, TypeError):
                return False
    
    return True


def validate_workflow_request(request_data: dict) -> List[str]:
    """验证工作流请求数据，返回错误列表"""
    errors = []
    
    # 检查疾病名称
    if 'disease' not in request_data:
        errors.append("缺少疾病名称")
    elif not validate_disease_name(request_data['disease']):
        errors.append("疾病名称无效")
    
    # 检查可选的靶点列表
    if 'selected_targets' in request_data:
        targets = request_data['selected_targets']
        if not isinstance(targets, list):
            errors.append("靶点列表格式错误")
        else:
            for target in targets:
                if not validate_gene_symbol(target):
                    errors.append(f"无效的基因符号: {target}")
    
    return errors


class RequestValidator:
    """请求验证器类"""
    
    @staticmethod
    def validate_disease_targets_request(data: dict) -> None:
        """验证疾病靶点请求"""
        if not data.get('disease'):
            raise ValidationError("疾病名称不能为空")
        
        if not validate_disease_name(data['disease']):
            raise ValidationError("疾病名称格式无效")
    
    @staticmethod
    def validate_uniprot_request(data: dict) -> None:
        """验证UniProt请求"""
        if not data.get('gene_symbol'):
            raise ValidationError("基因符号不能为空")
        
        if not validate_gene_symbol(data['gene_symbol']):
            raise ValidationError("基因符号格式无效")
    
    @staticmethod
    def validate_structure_request(data: dict) -> None:
        """验证结构请求"""
        if not data.get('uniprot_acc'):
            raise ValidationError("UniProt ID不能为空")
        
        if not validate_uniprot_id(data['uniprot_acc']):
            raise ValidationError("UniProt ID格式无效")
    
    @staticmethod
    def validate_pocket_request(data: dict) -> None:
        """验证口袋预测请求"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔍 [POCKET_VALIDATOR] 开始验证口袋预测请求: {data}")

        if not data.get('structure_path'):
            logger.error(f"❌ [POCKET_VALIDATOR] 结构文件路径为空")
            raise ValidationError("结构文件路径不能为空")

        structure_path = data['structure_path']
        logger.info(f"🔍 [POCKET_VALIDATOR] 结构文件路径: {structure_path}")

        if not validate_file_path(structure_path, ['.pdb', '.ent', '.cif']):
            logger.error(f"❌ [POCKET_VALIDATOR] 文件验证失败: {structure_path}")
            raise ValidationError("结构文件不存在或格式无效")

        logger.info(f"✅ [POCKET_VALIDATOR] 口袋预测请求验证通过")
    
    @staticmethod
    def validate_ligand_request(data: dict) -> None:
        """验证配体请求"""
        if not data.get('uniprot_acc') and not data.get('custom_smiles'):
            raise ValidationError("必须提供UniProt ID或自定义SMILES")
        
        if data.get('custom_smiles'):
            smiles_list = data['custom_smiles']
            if not isinstance(smiles_list, list):
                raise ValidationError("自定义SMILES必须是列表格式")
            
            for smiles in smiles_list:
                if not validate_smiles(smiles):
                    raise ValidationError(f"无效的SMILES: {smiles}")
    
    @staticmethod
    def validate_ai_decision_request(data: dict) -> None:
        """验证AI决策请求"""
        if not data.get('options'):
            raise ValidationError("选项列表不能为空")
        
        if not data.get('question'):
            raise ValidationError("问题不能为空")
        
        if not isinstance(data['options'], list):
            raise ValidationError("选项必须是列表格式")
    
    @staticmethod
    def validate_compound_selection_request(data: dict) -> None:
        """验证化合物选择请求"""
        required_fields = ['smiles_list', 'disease', 'protein']
        
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"{field}不能为空")
        
        if not isinstance(data['smiles_list'], list):
            raise ValidationError("SMILES列表必须是列表格式")
        
        for smiles in data['smiles_list']:
            if not validate_smiles(smiles):
                raise ValidationError(f"无效的SMILES: {smiles}")
    
    @staticmethod
    def validate_molecule_image_request(data: dict) -> None:
        """验证分子图像请求"""
        if not data.get('smiles'):
            raise ValidationError("SMILES不能为空")
        
        if not validate_smiles(data['smiles']):
            raise ValidationError("SMILES格式无效")
    
    @staticmethod
    def validate_docking_visualization_request(data: dict) -> None:
        """验证对接可视化请求"""
        if not data.get("protein_file"):
            raise ValidationError("蛋白质文件路径是必需的")
        if not validate_file_path(data["protein_file"], extensions=[".pdb", ".pdbqt"]):
            raise ValidationError("无效的蛋白质文件路径或格式")
            
        if not data.get("ligand_file"):
            raise ValidationError("配体文件路径是必需的")
        if not validate_file_path(data["ligand_file"], extensions=[".pdb", ".pdbqt", ".sdf", ".mol2"]):
            raise ValidationError("无效的配体文件路径或格式")

        if not data.get("output_dir"):
            raise ValidationError("输出目录是必需的")
