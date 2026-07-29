"""
API 测试模块

该模块提供 API 测试的基础组件：
- services: API 服务封装类
- fixtures: API 测试 pytest fixtures
"""

from base.api.services.base_service import BaseService
from base.api.fixtures import (
    api_logger,
    api_cache,
    api_env,
    base_service,
    authenticated_service,
    custom_service,
    api_test_context,
)

__all__ = [
    # Services
    'BaseService',
    
    # Fixtures
    'api_logger',
    'api_cache',
    'api_env',
    'base_service',
    'authenticated_service',
    'custom_service',
    'api_test_context',
]
