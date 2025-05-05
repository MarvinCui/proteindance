import os
from pathlib import Path
import tempfile

class Settings:
    # API Settings
    OPENAI_API_BASE = "https://api.siliconflow.cn/v1"
    OPENAI_API_KEY = "sk-kiuwnsdtlpclsjguvgajhuqdgowypqhmgozbxhhnenucutdp"
    
    # Paths
    TMP_DIR = Path(tempfile.gettempdir()) / "drug_flow"
    
    # API Endpoints
    UNIPROT_REST = "https://rest.uniprot.org"
    
    @classmethod
    def setup(cls):
        """Initialize settings and create necessary directories"""
        if cls.TMP_DIR.exists():
            import shutil
            shutil.rmtree(cls.TMP_DIR)
        cls.TMP_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
