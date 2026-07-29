"""
数据缓存模块

该模块提供线程安全的数据缓存功能：
- DataCache: 单例数据缓存类
- get_cache: 获取缓存实例的便捷函数
"""

from core.cache.data_cache import DataCache, get_cache

__all__ = [
    'DataCache',
    'get_cache',
]
