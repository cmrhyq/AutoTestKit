"""
测试租户常量。

集中定义测试代码中反复使用的租户标识（``TENANT = "tenant_admin"``、
``TENANT = "monitor-group"``）。使用 :class:`str` + :class:`Enum` 混合基类
使成员可直接与 ``str`` 比较，也可作为函数参数直接透传::

    >>> Tenant.ADMIN == "tenant_admin"
    True
    >>> with service_factory(SomeService, Tenant.ADMIN) as svc: ...

新增租户时请在此处集中添加，勿在测试文件内重复本地字符串。
"""

from enum import Enum


class Tenant(str, Enum):
    """测试租户 code。"""

    #: 超级/租户管理员账号
    ADMIN = "tenant_admin"
    #: 通用测试租户（原 monitor-group）
    MONITOR_GROUP = "monitor-group"


__all__ = ["Tenant"]
