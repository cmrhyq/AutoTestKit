"""
UI 自动化通用超时/间隔常量。

集中收拢 Page Object 中散落的 ``wait_for_timeout(500/800/1000/2000)`` 等魔法数字，
统一到本模块的 ``UITimeout``，方便调优与全局把控。

Note:
    这里用类级 ``int`` 常量而非 ``IntEnum``，因为 Playwright 的类型 stub 声明
    ``timeout: float | timedelta | None``。``IntEnum`` 成员的静态类型是
    ``Literal[UITimeout.XXX]``，与 ``float`` 不兼容，会触发 IDE 类型告警；
    改用纯类常量后静态类型就是 ``int``（自动向 ``float`` 兼容），无告警。
"""

from typing import Final


class UITimeout:
    """UI 自动化超时/间隔常量（单位：毫秒）。

    命名约定：
        - ``*_TIMEOUT``: 用作 ``timeout=`` 参数上限，行为完成时立即返回
        - 其它: 用作 ``wait_for_timeout()`` 的短稳定/动画等待
    """

    #: 极短动画/过渡（下拉展开、radio 选中回填等）
    ANIMATION: Final[int] = 300
    #: 弹窗按钮点击后的短稳定
    SHORT: Final[int] = 500
    #: 表单搜索/查询后的短等待
    QUERY: Final[int] = 800
    #: 一般点击后的稳定等待（tab 切换、菜单跳转）
    STABILIZE: Final[int] = 1000
    #: 提交表单/异步刷新后的中等等待
    MEDIUM: Final[int] = 2000
    #: 轮询模板构建状态的间隔
    POLL_INTERVAL: Final[int] = 5000

    #: 元素可见等待默认上限
    ELEMENT_VISIBLE_TIMEOUT: Final[int] = 10_000
    #: 页面导航默认上限
    NAVIGATION_TIMEOUT: Final[int] = 60_000
    #: 顶部导航切换较慢，需更宽松的等待
    TOP_MENU_SWITCH_TIMEOUT: Final[int] = 120_000
    #: 模板构建轮询总时长上限
    BUILD_MAX_WAIT: Final[int] = 120_000


__all__ = ["UITimeout"]
