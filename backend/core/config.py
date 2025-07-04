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


# 全局配置实例
settings = Settings()
settings.setup_directories()

# 初始化目录
settings.setup_directories()