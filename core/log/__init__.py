"""
日志管理模块

该模块提供统一的日志记录功能：
- TestLogger: 测试日志记录器类
- get_logger: 获取日志记录器的便捷函数
"""

from core.log.logger import TestLogger, get_logger

__all__ = [
    'TestLogger',
    'get_logger',
]
