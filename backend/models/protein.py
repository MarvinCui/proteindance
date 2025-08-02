"""
蛋白质相关数据模型
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..core.constants import StructureSourceType


@dataclass
class Protein:
    """蛋白质模型"""
    gene_symbol: str
    uniprot_id: Optional[str] = None
    name: Optional[str] = None
    organism: Optional[str] = None
    sequence: Optional[str] = None
    function: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Protein({self.gene_symbol}, {self.uniprot_id})"


@dataclass
class StructureSource:
    """结构来源模型"""
    source_type: str  # pdb, alphafold, custom
    identifier: str
    file_path: Optional[Path] = None
    resolution: Optional[float] = None
    method: Optional[str] = None
    confidence: Optional[float] = None
    
    def __str__(self) -> str:
        return f"StructureSource({self.source_type}:{self.identifier})"


@dataclass
class Pocket:
    """口袋模型"""
    pocket_id: str
    center: List[float]  # [x, y, z]
    score: float
    volume: Optional[float] = None
    surface_area: Optional[float] = None
    residues: List[str] = field(default_factory=list)
    prediction_method: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Pocket({self.pocket_id}, score={self.score:.2f})"


@dataclass
class Compound:
    """化合物模型"""
    smiles: str
    compound_id: Optional[str] = None
    name: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    hbd: Optional[int] = None  # Hydrogen bond donors
    hba: Optional[int] = None  # Hydrogen bond acceptors
    tpsa: Optional[float] = None  # Topological polar surface area
    source: Optional[str] = None
    activity_data: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"Compound({self.compound_id or 'Unknown'}, {self.smiles[:20]}...)"
    
    def passes_lipinski(self) -> bool:
        """检查是否符合Lipinski规则"""
        from ..core.constants import Defaults
        
        if not all([self.molecular_weight, self.logp, self.hbd, self.hba]):
            return False
            
        return (
            self.molecular_weight <= Defaults.LIPINSKI_MW_MAX and
            self.logp <= Defaults.LIPINSKI_LOGP_MAX and
            self.hbd <= Defaults.LIPINSKI_HBD_MAX and
            self.hba <= Defaults.LIPINSKI_HBA_MAX
        )
