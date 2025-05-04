from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class WorkflowState:
    disease: str = ""
    gene_symbol: Optional[str] = None
    uniprot_acc: Optional[str] = None
    structure_path: Optional[Path] = None
    pocket_center: Optional[tuple] = None
    smiles_list: List[str] = field(default_factory=list)
    optimized_smiles: Optional[str] = None
    molecule_image: Optional[str] = None
    docking_image: Optional[str] = None
    error_count: int = 0
    consecutive_errors: int = 0
    last_successful_step: Optional[str] = None
    decision_explanations: Dict[str, Any] = field(default_factory=dict)
    current_step: int = 0
    total_steps: int = 7
    innovation_level: int = 5

    def reset(self):
        """Reset workflow state"""
        self.error_count = 0
        self.consecutive_errors = 0
        self.last_successful_step = None
        self.decision_explanations = {}
        self.current_step = 0

workflow_state = WorkflowState()
