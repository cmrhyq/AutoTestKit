"""
认证类型枚举。

集中收拢 API 客户端 / fixture 中散落的认证类型硬编码字符串
(``"bearer"`` / ``"basic"`` / ``"api_key"``)，防止拼写错误静默失效。

继承自 ``str + Enum`` 使成员可与原始字符串直接比较，无需 ``.value``::

    >>> AuthType.BEARER == "bearer"
    True
    >>> auth_type = AuthType.BEARER
    >>> str(auth_type) or f"{auth_type}"  # 可直接用于字符串上下文
"""

from enum import Enum


class AuthType(str, Enum):
    """API 客户端认证类型。"""

    #: Bearer Token 认证，通常配合 ``Authorization: Bearer <token>`` 头使用
    BEARER = "bearer"
    #: HTTP Basic 认证，配合 ``username`` + ``password`` 使用
    BASIC = "basic"
    #: API Key 认证，配合自定义 header (如 ``x-api-key``) 使用
    API_KEY = "api_key"


__all__ = ["AuthType"]
