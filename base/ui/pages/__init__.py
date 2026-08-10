"""
Page Object Model 页面对象模块

该模块提供 UI 测试的页面对象：
- BasePage: 基础页面类，提供通用的页面操作方法
- 具体页面类: 针对特定页面的封装
"""

from base.ui.pages.base_page import BasePage, WaitUntil, ElementState, LoadState

__all__ = [
    # Base
    'BasePage',
    'WaitUntil',
    'ElementState',
    'LoadState',
]
