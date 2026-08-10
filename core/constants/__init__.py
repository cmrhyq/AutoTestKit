"""
core.constants 常量集中管理包。

约定：所有跨测试文件复用的固定量都收拢到本包，避免在测试文件内散落魔法数字/字符串。
"""

from core.constants.auth import AuthType
from core.constants.http_status import HttpStatus
from core.constants.playwright import (
    PlaywrightElementState,
    PlaywrightLoadState,
    PlaywrightWaitUntil,
)

__all__ = [
    "AuthType",
    "HttpStatus",
    "PlaywrightElementState",
    "PlaywrightLoadState",
    "PlaywrightWaitUntil",
]
