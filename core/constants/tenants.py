"""
测试租户常量。
"""

from enum import Enum


class Tenant(str, Enum):
    """测试租户 code。"""

    #: 超级/租户管理员账号
    ADMIN = "tenant_admin"
    #: 通用测试租户（原 monitor-group）
    MONITOR_GROUP = "monitor-group"


__all__ = ["Tenant"]
