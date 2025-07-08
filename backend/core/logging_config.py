"""
日志配置模块
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import traceback
import json
import asyncio
from contextvars import ContextVar

# 创建上下文变量来存储请求ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # 添加请求ID（如果存在）
        request_id = request_id_var.get('')
        if request_id:
            log_data['request_id'] = request_id
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 添加额外的字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # 添加请求ID
        request_id = request_id_var.get('')
        request_id_str = f"[{request_id}] " if request_id else ""
        
        formatted = super().format(record)
        return f"{request_id_str}{formatted}"


class RequestIDFilter(logging.Filter):
    """添加请求ID的过滤器"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_id_var.get('')
        if request_id:
            record.request_id = request_id
        return True


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "proteindance",
    enable_json: bool = True,
    enable_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    设置日志配置
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
        app_name: 应用名称
        enable_json: 是否启用JSON格式的文件日志
        enable_console: 是否启用控制台日志
        max_file_size: 最大文件大小
        backup_count: 备份文件数量
    """
    
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    handlers = []
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(RequestIDFilter())
        handlers.append(console_handler)
    
    # 文件处理器 - 应用日志
    app_log_file = log_path / f"{app_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    if enable_json:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(RequestIDFilter())
    handlers.append(file_handler)
    
    # 错误日志文件处理器
    error_log_file = log_path / f"{app_name}_error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    error_handler.addFilter(RequestIDFilter())
    handlers.append(error_handler)
    
    # 访问日志文件处理器
    access_log_file = log_path / f"{app_name}_access.log"
    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(file_formatter)
    access_handler.addFilter(RequestIDFilter())
    
    # 为访问日志创建单独的日志器
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # 添加处理器到根日志器
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # 配置第三方库的日志级别
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    

class LoggerMixin:
    """日志混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志器"""
        return logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self._log_with_extra('info', message, kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self._log_with_extra('warning', message, kwargs)
    
    def log_error(self, message: str, error: Exception = None, **kwargs) -> None:
        """记录错误日志"""
        if error:
            kwargs['error_type'] = error.__class__.__name__
            kwargs['error_message'] = str(error)
        self._log_with_extra('error', message, kwargs, exc_info=error is not None)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self._log_with_extra('debug', message, kwargs)
    
    def _log_with_extra(self, level: str, message: str, extra_data: Dict[str, Any], exc_info: bool = False) -> None:
        """带额外数据的日志记录"""
        log_record = logging.LogRecord(
            name=self.logger.name,
            level=getattr(logging, level.upper()),
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=None if not exc_info else sys.exc_info()
        )
        log_record.extra_data = extra_data
        self.logger.handle(log_record)


def get_logger(name: str = None) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name or __name__)


def log_function_call(func_name: str, args: tuple = (), kwargs: dict = None) -> None:
    """记录函数调用"""
    logger = get_logger('function_calls')
    logger.debug(f"调用函数: {func_name}", extra={
        'function': func_name,
        'args': str(args),
        'kwargs': str(kwargs or {})
    })


def log_api_request(method: str, path: str, status_code: int, duration: float, **kwargs) -> None:
    """记录API请求"""
    access_logger = logging.getLogger('access')
    access_logger.info(f"{method} {path} - {status_code} - {duration:.3f}s", extra={
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration': duration,
        **kwargs
    })


def log_error_with_context(error: Exception, context: Dict[str, Any] = None) -> None:
    """记录带上下文的错误"""
    logger = get_logger('errors')
    logger.error(f"发生错误: {error}", extra={
        'error_type': error.__class__.__name__,
        'error_message': str(error),
        'context': context or {},
        'traceback': traceback.format_exc()
    }, exc_info=True)


# 初始化日志配置
def init_logging():
    """初始化日志配置"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(
        log_level=log_level,
        log_dir="logs",
        app_name="proteindance",
        enable_json=True,
        enable_console=True
    )