"""
UI 测试模块

该模块提供 UI 测试的基础组件：
- pages: Page Object Model 页面对象
- fixtures: UI 测试 pytest fixtures
"""

from base.ui.pages.base_page import BasePage, WaitUntil, ElementState, LoadState
from base.ui.fixtures import (
    playwright_instance,
    browser,
    context,
    page,
    ui_env,
    ui_logger,
)

__all__ = [
    # Page Objects
    'BasePage',
    'WaitUntil',
    'ElementState',
    'LoadState',
    
    # Fixtures
    'playwright_instance',
    'browser',
    'context',
    'page',
    'ui_env',
    'ui_logger',
]
