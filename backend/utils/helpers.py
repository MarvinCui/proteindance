"""
通用辅助函数
"""
import time
import logging
from typing import Callable, Optional, Any
from pathlib import Path
from ..models.exceptions import DrugDiscoveryError
from .display import print_warning, Colors


def safe_execute(func: Callable, error_msg: str, operation_name: str, 
                max_retries: int = 3, delay: float = 1.0) -> Optional[Any]:
    """
    安全执行函数，带重试机制
    
    Args:
        func: 要执行的函数
        error_msg: 错误消息
        operation_name: 操作名称
        max_retries: 最大重试次数
        delay: 重试延迟
    
    Returns:
        函数执行结果或None
    """
    logger = logging.getLogger(__name__)
    
    for retry in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.error(f"{operation_name} 失败 (尝试 {retry + 1}/{max_retries}): {str(e)}")
            
            if retry < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"{error_msg}: {str(e)}")
                raise DrugDiscoveryError(f"{error_msg}: {str(e)}")
    
    return None


def natural_language_input(prompt: str, default_value: str = None, 
                          validator: Callable = None) -> str:
    """
    处理自然语言输入，支持默认值和输入验证
    
    Args:
        prompt: 提示语
        default_value: 默认值，如果用户输入为空
        validator: 验证函数，返回True表示有效输入
    
    Returns:
        用户输入或默认值
    """
    full_prompt = f"{Colors.BOLD}{prompt}{Colors.ENDC} "
    if default_value:
        full_prompt += f"[{Colors.OKBLUE}默认: {default_value}{Colors.ENDC}]"
    
    while True:
        user_input = input(full_prompt + ": ").strip()
        
        if not user_input and default_value:
            return default_value
        
        if not validator or validator(user_input):
            return user_input
        
        print_warning("输入无效，请重新输入。")


def ensure_directory(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_file_exists(file_path: Path) -> bool:
    """验证文件是否存在"""
    return file_path.exists() and file_path.is_file()


def validate_smiles(smiles: str) -> bool:
    """验证SMILES字符串"""
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except ImportError:
        # 如果没有rdkit，进行简单验证
        return bool(smiles and len(smiles.strip()) > 0)


def calculate_molecular_properties(smiles: str) -> dict:
    """计算分子性质"""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, Lipinski
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}
        
        return {
            "molecular_weight": Descriptors.MolWt(mol),
            "logp": Descriptors.MolLogP(mol),
            "hbd": Lipinski.NumHDonors(mol),
            "hba": Lipinski.NumHAcceptors(mol),
            "tpsa": Descriptors.TPSA(mol),
            "rotatable_bonds": Descriptors.NumRotatableBonds(mol)
        }
    except ImportError:
        return {}


def format_time_duration(seconds: float) -> str:
    """格式化时间持续时间"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def truncate_text(text: str, max_length: int = 50) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
