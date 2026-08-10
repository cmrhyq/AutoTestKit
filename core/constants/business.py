"""
后端业务码枚举。

后端在响应体的 ``code`` 字段（`response_json["code"]`）返回业务级状态码。
本枚举将测试代码中散落在各文件顶部的 ``BUSINESS_SUCCESS_CODE`` / ``RESOURCE_NOT_FOUND_CODE``
/ ``RESOURCE_CONFLICT_CODE`` / ``RESOURCE_ALREADY_EXISTS_CODE`` / ``WORKLOAD_NOT_FOUND_CODE``
/ ``RBAC_NOT_FOUND_CODE`` 等常量统一收拢到一处。

由于继承自 :class:`IntEnum`，成员可与原始 ``int`` 直接比较，无需 ``.value``::

    >>> ApiCode.SUCCESS == 2000
    True
    >>> response_json.get("code") == ApiCode.SUCCESS  # 与 dict 中 int 值直接比较
    True

新增业务码时，请在此集中定义并附上中文语义注释；请勿再在测试文件内本地重复声明。
"""

from enum import IntEnum


class ApiCode(IntEnum):
    """后端业务码。"""

    #: 业务成功（HTTP 200 且业务逻辑成功）
    SUCCESS = 2000
    #: 登录接口专用的成功业务码（Portal 登录接口约定；与其他接口 SUCCESS=2000 不同）
    LOGIN_SUCCESS = 200
    #: 资源未找到（对应"若已存在则删除、若不存在则跳过"分支）
    NOT_FOUND = 4004
    #: 资源冲突/已存在（部分接口用于"已存在"语义，如 Harbor / Helm）
    CONFLICT = 4009


__all__ = ["ApiCode"]
