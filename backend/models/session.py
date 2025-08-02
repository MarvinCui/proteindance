from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import time

class SessionData(BaseModel):
    """
    Represents the full state of a drug discovery workflow session.
    This model is used for saving and restoring the application state.
    """
    disease: Optional[str] = None
    innovationLevel: Optional[int] = 5
    logs: Optional[List[Dict[str, Any]]] = []
    decisionTarget: Optional[Dict[str, Any]] = None
    decisionPocket: Optional[Dict[str, Any]] = None
    decisionCompound: Optional[Dict[str, Any]] = None
    moleculeImage: Optional[str] = None
    originalMoleculeImage: Optional[str] = None
    workflowState: Optional[Dict[str, Any]] = None
    allTargets: Optional[List[Dict[str, Any]]] = []
    triedTargets: Optional[List[str]] = []
    targetExplanation: Optional[str] = None
    selectionReason: Optional[str] = None
    optimizationExplanation: Optional[str] = None
    scientificAnalysis: Optional[str] = None
    currentStructurePath: Optional[str] = None
    currentPocketCenter: Optional[List[float]] = None
    currentProteinName: Optional[str] = "蛋白质结构"
    currentLigandSmiles: Optional[List[str]] = None
    currentOptimizedSmiles: Optional[str] = None
    isUsingAlphaFold: Optional[bool] = False
    step: Optional[int] = 0

class Session(BaseModel):
    """
    Represents a session record in the database.
    """
    id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="A short, descriptive title for the session")
    created_at: float = Field(default_factory=time.time, description="Session creation timestamp")
    updated_at: float = Field(default_factory=time.time, description="Session last update timestamp")
    session_data: SessionData = Field(..., description="The complete state of the workflow")
    user_id: Optional[int] = Field(None, description="ID of the user who owns this session")

class SessionMetadata(BaseModel):
    """
    Represents the metadata for a session, used for list views.
    """
    id: str
    title: str
    created_at: float
    updated_at: float
