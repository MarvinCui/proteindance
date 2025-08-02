"""
自定义异常类
"""


class DrugDiscoveryError(Exception):
    """药物发现基础异常类"""
    pass


class WorkflowError(DrugDiscoveryError):
    """工作流异常"""
    pass


class APIError(DrugDiscoveryError):
    """API调用异常"""
    pass


class NetworkError(DrugDiscoveryError):
    """网络连接异常"""
    pass


class ValidationError(DrugDiscoveryError):
    """数据验证异常"""
    pass


class ProcessingError(DrugDiscoveryError):
    """数据处理异常"""
    pass


class FileError(DrugDiscoveryError):
    """文件操作异常"""
    pass


class ConfigurationError(DrugDiscoveryError):
    """配置错误异常"""
    pass
