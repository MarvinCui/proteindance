"""
错误处理中间件
"""
import time
import uuid
import traceback
from typing import Callable, Dict, Any
from contextlib import asynccontextmanager

import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.logging_config import request_id_var, log_api_request, log_error_with_context


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 添加请求ID到响应头
        response = None
        status_code = 500
        error_message = None
        
        try:
            # 执行请求
            response = await call_next(request)
            status_code = response.status_code
            
        except HTTPException as e:
            # FastAPI HTTPException
            status_code = e.status_code
            error_message = str(e.detail)
            
            logger.warning(f"HTTP异常: {e.status_code} - {e.detail}", extra={
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'status_code': e.status_code,
                'detail': e.detail
            })
            
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.detail,
                    "request_id": request_id
                }
            )
            
        except StarletteHTTPException as e:
            # Starlette HTTPException
            status_code = e.status_code
            error_message = str(e.detail)
            
            logger.warning(f"Starlette HTTP异常: {e.status_code} - {e.detail}", extra={
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'status_code': e.status_code,
                'detail': e.detail
            })
            
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.detail,
                    "request_id": request_id
                }
            )
            
        except Exception as e:
            # 未处理的异常
            status_code = 500
            error_message = "内部服务器错误"
            
            # 记录详细错误信息
            log_error_with_context(e, {
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'headers': dict(request.headers),
                'path_params': dict(request.path_params),
                'query_params': dict(request.query_params)
            })
            
            response = JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": error_message,
                    "request_id": request_id
                }
            )
        
        finally:
            # 计算请求处理时间
            duration = time.time() - start_time
            
            # 记录API请求日志
            log_api_request(
                method=request.method,
                path=str(request.url.path),
                status_code=status_code,
                duration=duration,
                request_id=request_id,
                query_params=dict(request.query_params),
                user_agent=request.headers.get('user-agent', ''),
                ip_address=request.client.host if request.client else '',
                error_message=error_message
            )
        
        # 添加响应头
        if response:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration)
        
        return response


def create_error_handler() -> Callable:
    """创建错误处理器"""
    
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """HTTP异常处理器"""
        request_id = request_id_var.get('unknown')
        
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}", extra={
            'request_id': request_id,
            'status_code': exc.status_code,
            'detail': exc.detail
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "request_id": request_id
            }
        )
    
    return http_exception_handler


def create_validation_error_handler() -> Callable:
    """创建验证错误处理器"""
    
    async def validation_exception_handler(request: Request, exc) -> JSONResponse:
        """验证异常处理器"""
        request_id = request_id_var.get('unknown')
        
        # 解析验证错误
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(f"验证错误: {errors}", extra={
            'request_id': request_id,
            'validation_errors': errors
        })
        
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "请求数据验证失败",
                "validation_errors": errors,
                "request_id": request_id
            }
        )
    
    return validation_exception_handler


def create_general_exception_handler() -> Callable:
    """创建通用异常处理器"""
    
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """通用异常处理器"""
        request_id = request_id_var.get('unknown')
        
        # 记录错误
        log_error_with_context(exc, {
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url)
        })
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "内部服务器错误",
                "request_id": request_id
            }
        )
    
    return general_exception_handler


class APIException(Exception):
    """自定义API异常"""
    
    def __init__(self, message: str, status_code: int = 400, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessLogicError(APIException):
    """业务逻辑错误"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=400, details=details)


class ResourceNotFoundError(APIException):
    """资源未找到错误"""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"资源未找到: {resource}"
        if identifier:
            message += f" (ID: {identifier})"
        super().__init__(message, status_code=404)


class ValidationError(APIException):
    """验证错误"""
    
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=422, details=details)


class AuthenticationError(APIException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=401)


class AuthorizationError(APIException):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status_code=403)


class ExternalServiceError(APIException):
    """外部服务错误"""
    
    def __init__(self, service: str, message: str = None):
        error_message = f"外部服务错误: {service}"
        if message:
            error_message += f" - {message}"
        super().__init__(error_message, status_code=502)


def create_api_exception_handler() -> Callable:
    """创建API异常处理器"""
    
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """API异常处理器"""
        request_id = request_id_var.get('unknown')
        
        logger.warning(f"API异常: {exc.message}", extra={
            'request_id': request_id,
            'status_code': exc.status_code,
            'message': exc.message,
            'details': exc.details
        })
        
        content = {
            "success": False,
            "error": exc.message,
            "request_id": request_id
        }
        
        if exc.details:
            content["details"] = exc.details
        
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    
    return api_exception_handler


def setup_error_handlers(app: FastAPI) -> None:
    """设置错误处理器"""
    from fastapi.exceptions import RequestValidationError
    
    # 添加中间件
    app.add_middleware(ErrorHandlerMiddleware)
    
    # 添加异常处理器
    app.add_exception_handler(HTTPException, create_error_handler())
    app.add_exception_handler(RequestValidationError, create_validation_error_handler())
    app.add_exception_handler(APIException, create_api_exception_handler())
    app.add_exception_handler(Exception, create_general_exception_handler())


@asynccontextmanager
async def log_request_context(request: Request):
    """请求上下文日志管理器"""
    request_id = request_id_var.get('unknown')
    start_time = time.time()
    
    logger.info(f"开始处理请求: {request.method} {request.url.path}", extra={
        'request_id': request_id,
        'method': request.method,
        'path': request.url.path,
        'query_params': dict(request.query_params)
    })
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"完成处理请求: {request.method} {request.url.path} - {duration:.3f}s", extra={
            'request_id': request_id,
            'duration': duration
        })