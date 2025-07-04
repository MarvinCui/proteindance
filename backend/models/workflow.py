"""
工作流相关数据模型
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core.constants import WorkflowStatus, WorkflowSteps
from .protein import Protein, StructureSource, Pocket, Compound


@dataclass
class WorkflowStep:
    """工作流步骤模型"""
    step_name: str
    status: str = WorkflowStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def start(self):
        """开始步骤"""
        self.status = WorkflowStatus.IN_PROGRESS
        self.start_time = datetime.now()
    
    def complete(self, result: Any = None):
        """完成步骤"""
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now()
        self.result = result
    
    def fail(self, error: str):
        """步骤失败"""
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now()
        self.error = error


@dataclass
class WorkflowState:
    """工作流状态模型"""
    workflow_id: str
    disease: str
    status: str = WorkflowStatus.NOT_STARTED
    current_step: Optional[str] = None
    
    # 工作流数据
    targets: List[Protein] = field(default_factory=list)
    selected_target: Optional[Protein] = None
    structure_sources: List[StructureSource] = field(default_factory=list)
    selected_structure: Optional[StructureSource] = None
    pockets: List[Pocket] = field(default_factory=list)
    selected_pocket: Optional[Pocket] = None
    compounds: List[Compound] = field(default_factory=list)
    selected_compound: Optional[Compound] = None
    
    # 步骤跟踪
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化工作流步骤"""
        if not self.steps:
            for step_name in [
                WorkflowSteps.TARGET_DISCOVERY,
                WorkflowSteps.STRUCTURE_RETRIEVAL,
                WorkflowSteps.POCKET_PREDICTION,
                WorkflowSteps.LIGAND_RETRIEVAL,
                WorkflowSteps.COMPOUND_OPTIMIZATION,
                WorkflowSteps.RESULT_ANALYSIS
            ]:
                self.steps[step_name] = WorkflowStep(step_name)
    
    def start_step(self, step_name: str):
        """开始指定步骤"""
        if step_name in self.steps:
            self.steps[step_name].start()
            self.current_step = step_name
            self.updated_at = datetime.now()
    
    def complete_step(self, step_name: str, result: Any = None):
        """完成指定步骤"""
        if step_name in self.steps:
            self.steps[step_name].complete(result)
            self.updated_at = datetime.now()
    
    def fail_step(self, step_name: str, error: str):
        """步骤失败"""
        if step_name in self.steps:
            self.steps[step_name].fail(error)
            self.status = WorkflowStatus.FAILED
            self.updated_at = datetime.now()
    
    def get_progress(self) -> float:
        """获取工作流进度百分比"""
        total_steps = len(self.steps)
        completed_steps = sum(1 for step in self.steps.values() 
                            if step.status == WorkflowStatus.COMPLETED)
        return (completed_steps / total_steps) * 100 if total_steps > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "workflow_id": self.workflow_id,
            "disease": self.disease,
            "status": self.status,
            "current_step": self.current_step,
            "progress": self.get_progress(),
            "targets": [{"gene_symbol": t.gene_symbol, "uniprot_id": t.uniprot_id} for t in self.targets],
            "selected_target": {"gene_symbol": self.selected_target.gene_symbol, "uniprot_id": self.selected_target.uniprot_id} if self.selected_target else None,
            "structure_sources": [{"source_type": s.source_type, "identifier": s.identifier} for s in self.structure_sources],
            "pockets": [{"pocket_id": p.pocket_id, "score": p.score} for p in self.pockets],
            "compounds": [{"smiles": c.smiles, "compound_id": c.compound_id} for c in self.compounds],
            "steps": {name: {"status": step.status, "error": step.error} for name, step in self.steps.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# 全局工作流状态实例
workflow_state = WorkflowState(
    workflow_id="default",
    disease=""
)
