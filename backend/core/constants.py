"""
常量定义模块
"""

# 工作流状态
class WorkflowStatus:
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# 工作流步骤
class WorkflowSteps:
    TARGET_DISCOVERY = "target_discovery"
    STRUCTURE_RETRIEVAL = "structure_retrieval"
    POCKET_PREDICTION = "pocket_prediction"
    LIGAND_RETRIEVAL = "ligand_retrieval"
    COMPOUND_OPTIMIZATION = "compound_optimization"
    RESULT_ANALYSIS = "result_analysis"

# 结构来源类型
class StructureSourceType:
    PDB = "pdb"
    ALPHAFOLD = "alphafold"
    CUSTOM = "custom"

# 口袋预测方法
class PocketPredictionMethod:
    P2RANK = "p2rank"
    DOGSITE = "dogsite"

# 分子格式
class MoleculeFormat:
    SMILES = "smiles"
    SDF = "sdf"
    PDB = "pdb"
    PDBQT = "pdbqt"

# API响应状态
class APIStatus:
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

# 终端颜色代码
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# 默认值
class Defaults:
    MAX_TARGETS = 10
    MAX_COMPOUNDS = 20
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    
    # Lipinski规则阈值
    LIPINSKI_MW_MAX = 500
    LIPINSKI_LOGP_MAX = 5
    LIPINSKI_HBD_MAX = 5
    LIPINSKI_HBA_MAX = 10

# 错误消息
class ErrorMessages:
    NETWORK_ERROR = "网络连接错误"
    API_ERROR = "API调用失败"
    FILE_NOT_FOUND = "文件未找到"
    INVALID_INPUT = "输入参数无效"
    PROCESSING_ERROR = "数据处理错误"
    TIMEOUT_ERROR = "操作超时"
