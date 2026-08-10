"""
基础测试模块

该模块提供测试框架的基础组件：
- api: API 测试基础服务和 fixtures
- ui: UI 测试基础页面对象和 fixtures
"""

from base.api.services.base_service import BaseService
from base.ui.pages.base_page import BasePage

__all__ = [
    'BaseService',
    'BasePage',
]
