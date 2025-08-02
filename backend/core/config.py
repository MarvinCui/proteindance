"""
配置管理模块
"""
import os
import tempfile
from pathlib import Path
from typing import Optional


class Settings:
    """应用配置类"""

    # API配置
    OPENAI_API_BASE: str = "https://api.siliconflow.cn/v1"
    OPENAI_API_KEY: str = "sk-kiuwnsdtlpclsjguvgajhuqdgowypqhmgozbxhhnenucutdp"

    # 路径配置
    TMP_DIR: Path = Path(tempfile.gettempdir()) / "drug_flow"
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    # 数据库API端点
    UNIPROT_REST: str = "https://rest.uniprot.org"
    RCSB_SEARCH_API: str = "https://search.rcsb.org/rcsbsearch/v2/query"
    CHEMBL_API: str = "https://www.ebi.ac.uk/chembl/api/data"
    ALPHAFOLD_API: str = "https://alphafold.ebi.ac.uk/files"
    DOGSITE_API: str = "https://proteins.plus/api/v2/dogsite"

    # P2Rank配置
    P2RANK_CANDIDATES: list = [
        PROJECT_ROOT / "p2rank/prank",
        Path.home() / "p2rank/prank"
    ]
    
    # 分子对接配置
    VINA_EXECUTABLE: Path = PROJECT_ROOT / "vina"
    
    # PyMOL配置
    PYMOL_CANDIDATES: list = [
        # Conda environment paths
        PROJECT_ROOT / ".conda/bin/pymol",
        Path.home() / ".conda/envs/molecular-docking/bin/pymol",
        Path.home() / "anaconda3/envs/molecular-docking/bin/pymol",
        Path.home() / "miniconda3/envs/molecular-docking/bin/pymol",
        # System paths
        Path("/opt/conda/bin/pymol"),
        Path("/usr/local/bin/pymol"),
        Path("/usr/bin/pymol")
    ]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "drug_discovery.log"

    # 终端显示配置
    TERM_WIDTH: int = 120

    @classmethod
    def setup_directories(cls):
        """初始化必要的目录"""
        # 确保临时目录存在
        cls.TMP_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_p2rank_binary(cls) -> Optional[Path]:
        """获取P2Rank可执行文件路径"""
        # 检查候选路径
        for candidate in cls.P2RANK_CANDIDATES:
            if candidate.exists() and candidate.is_file():
                return candidate

        # 检查环境变量
        env_path = os.getenv("P2RANK_BIN")
        if env_path and Path(env_path).exists():
            return Path(env_path)

        # 检查PATH
        from shutil import which
        which_path = which("prank")
        if which_path:
            return Path(which_path)

        return None
    
    @classmethod
    def get_vina_binary(cls) -> Optional[Path]:
        """获取AutoDock Vina可执行文件路径"""
        # 检查项目根目录
        if cls.VINA_EXECUTABLE.exists() and cls.VINA_EXECUTABLE.is_file():
            return cls.VINA_EXECUTABLE
            
        # 检查环境变量
        env_path = os.getenv("VINA_BIN")
        if env_path and Path(env_path).exists():
            return Path(env_path)
            
        # 检查PATH
        from shutil import which
        which_path = which("vina")
        if which_path:
            return Path(which_path)
            
        return None
    
    @classmethod
    def get_pymol_binary(cls) -> Optional[Path]:
        """获取PyMOL可执行文件路径"""
        # 检查候选路径
        for candidate in cls.PYMOL_CANDIDATES:
            if candidate.exists() and candidate.is_file():
                return candidate
                
        # 检查环境变量
        env_path = os.getenv("PYMOL_BIN")
        if env_path and Path(env_path).exists():
            return Path(env_path)
            
        # 检查PATH
        from shutil import which
        which_path = which("pymol")
        if which_path:
            return Path(which_path)
            
        return None
    
    @classmethod
    def check_conda_environment(cls) -> dict:
        """检查conda环境和必要的包"""
        status = {
            "conda_available": False,
            "molecular_docking_env": False,
            "pymol_installed": False,
            "rdkit_installed": False,
            "recommendations": []
        }
        
        # 检查conda
        from shutil import which
        conda_path = which("conda")
        if conda_path:
            status["conda_available"] = True
            
            # 检查molecular-docking环境
            try:
                import subprocess
                result = subprocess.run(
                    ["conda", "env", "list"], 
                    capture_output=True, text=True, timeout=10
                )
                if "molecular-docking" in result.stdout:
                    status["molecular_docking_env"] = True
                else:
                    status["recommendations"].append(
                        "Create conda environment: conda env create -f docking_test/environment.yml"
                    )
            except Exception:
                pass
        else:
            status["recommendations"].append(
                "Install conda: https://docs.conda.io/en/latest/miniconda.html"
            )
        
        # 检查PyMOL
        try:
            import pymol
            status["pymol_installed"] = True
        except ImportError:
            status["recommendations"].append(
                "Install PyMOL: conda install -c conda-forge pymol-open-source"
            )
        
        # 检查RDKit
        try:
            import rdkit
            status["rdkit_installed"] = True
        except ImportError:
            status["recommendations"].append(
                "Install RDKit: conda install -c conda-forge rdkit"
            )
        
        return status


# 全局配置实例
settings = Settings()
settings.setup_directories()

# 初始化目录
settings.setup_directories()