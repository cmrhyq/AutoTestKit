"""
core.constants 常量集中管理包。

- :mod:`api_codes`：后端业务码枚举（:class:`ApiCode`，如 ``SUCCESS=2000``）。
- :mod:`http_status`：HTTP 状态码枚举（:class:`HttpStatus`，如 ``OK=200``）。
- :mod:`tenants`：测试租户常量（:class:`Tenant`，如 ``ADMIN='tenant_admin'``）。
- :mod:`timings`：资源创建/就绪等待秒数集合（:class:`Timing`）。
- :mod:`domain`：领域内特化常量（:class:`HarborConst` / :class:`HelmConst`
  / :class:`ClusterFlag` / :class:`SecretConst`）。

约定：所有跨测试文件复用的固定量都收拢到本包，避免在测试文件内散落魔法数字/字符串。
"""

from core.constants.business import ApiCode
from core.constants.domain import ClusterFlag, HarborConst, HelmConst, SecretConst
from core.constants.http_status import HttpStatus
from core.constants.tenants import Tenant
from core.constants.timings import Timing

__all__ = [
    "ApiCode",
    "ClusterFlag",
    "HarborConst",
    "HelmConst",
    "HttpStatus",
    "SecretConst",
    "Tenant",
    "Timing",
]
