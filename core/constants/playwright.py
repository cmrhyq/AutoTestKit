"""
Playwright 状态枚举。

集中收拢 UI 页面对象里散落的 Playwright 状态字符串
(``"load"`` / ``"domcontentloaded"`` / ``"networkidle"`` / ``"visible"`` 等)，
避免拼写错误静默失效。

继承自 ``str + Enum``，成员可直接传给 Playwright API，无需 ``.value``::

    >>> from core.constants import PlaywrightLoadState
    >>> page.wait_for_load_state(PlaywrightLoadState.NETWORKIDLE)
"""

from enum import Enum


class PlaywrightLoadState(str, Enum):
    """``page.wait_for_load_state`` 支持的加载状态。"""

    #: ``load`` 事件已触发
    LOAD = "load"
    #: DOMContentLoaded 事件已触发
    DOMCONTENTLOADED = "domcontentloaded"
    #: 网络已空闲（连续 500ms 无网络请求）
    NETWORKIDLE = "networkidle"


class PlaywrightWaitUntil(str, Enum):
    """``page.goto`` / ``page.reload`` 等导航方法的 ``wait_until`` 参数。"""

    #: 导航提交后立即返回，不等待任何事件
    COMMIT = "commit"
    #: 等待 DOMContentLoaded 事件
    DOMCONTENTLOADED = "domcontentloaded"
    #: 等待 ``load`` 事件
    LOAD = "load"
    #: 等待网络空闲
    NETWORKIDLE = "networkidle"


class PlaywrightElementState(str, Enum):
    """``locator.wait_for`` / ``page.wait_for_selector`` 的元素状态。"""

    #: 元素已附加到 DOM
    ATTACHED = "attached"
    #: 元素已从 DOM 移除
    DETACHED = "detached"
    #: 元素可见
    VISIBLE = "visible"
    #: 元素不可见（隐藏或从 DOM 移除）
    HIDDEN = "hidden"


__all__ = [
    "PlaywrightLoadState",
    "PlaywrightWaitUntil",
    "PlaywrightElementState",
]
