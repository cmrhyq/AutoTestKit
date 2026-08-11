"""
UI 自动化通用超时/间隔常量。

集中收拢 Page Object 中散落的 ``wait_for_timeout(500/800/1000/2000)`` 等魔法数字，
统一到本模块的 :class:`UITimeout`，方便调优与全局把控。

设计动机
--------

- **可读性**：调用点写 ``UITimeout.QUERY`` 比写 ``800`` 更能表达意图；
- **可维护**：网络环境变化时只需调本模块，无须遍历所有 Page Object；
- **一致性**：避免同一场景不同页面使用不同的等待时长导致的用例稳定性差异；
- **静态类型友好**：类级 ``int`` 常量能被 Playwright 类型 stub
  （``timeout: float | timedelta | None``）无告警接收。

.. Note::
    这里刻意使用 **纯类 + ``Final[int]`` 类常量** 而非 ``IntEnum``。原因：
    Playwright 的 ``timeout`` 参数类型为 ``float | timedelta | None``；
    ``IntEnum`` 成员的静态类型是 ``Literal[UITimeout.XXX]``，
    与 ``float`` 不兼容，IDE 会报
    ``Expected 'float | timedelta | None', got 'Literal[...]'``。
    改用纯类常量后静态类型就是 ``int``（可隐式向 ``float`` 兼容）。

使用示例::

    from core.constants import UITimeout

    self.page.goto(url, timeout=UITimeout.NAVIGATION_TIMEOUT)
    expect(self.tab_alive).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
    self.page.wait_for_timeout(UITimeout.ANIMATION)
"""

from typing import Final


class UITimeout:
    """UI 自动化超时/间隔常量集合（单位：**毫秒**）。

    命名约定：
        - 以 ``*_TIMEOUT`` 结尾的常量：用作 Playwright API 的 ``timeout=`` 参数
          （行为完成即立即返回，未完成才等待到上限抛出）；
        - 其它常量：用作 ``page.wait_for_timeout()`` 的固定短稳定/动画等待
          （无条件等待到指定时间）。

    调优建议：
        - 生产网速：默认值即可；
        - CI/慢速网络：可将 ``*_TIMEOUT`` 系列适度上调；
        - 本地调试：短稳定类（如 ``ANIMATION``）可适度上调以便观察。
    """

    #: 极短动画/过渡等待（下拉展开、单选按钮回填、tooltip 出现等）
    ANIMATION: Final[int] = 300

    #: 弹窗按钮点击后的短稳定等待（弹窗关闭动画、二次确认等）
    SHORT: Final[int] = 500

    #: 表单搜索/查询后的短等待（服务端返回后表格刷新时间）
    QUERY: Final[int] = 800

    #: 一般点击后的稳定等待（tab 切换、菜单跳转，需要等 SPA 路由 + 内容渲染）
    STABILIZE: Final[int] = 1000

    #: 提交表单/异步刷新后的中等等待（保留常量以备未来调用点使用）
    MEDIUM: Final[int] = 2000

    #: 轮询模板构建状态时的两次点击"查询"之间的间隔
    POLL_INTERVAL: Final[int] = 5000

    #: 元素可见等待默认上限（``expect(...).to_be_visible(timeout=...)`` 等）
    ELEMENT_VISIBLE_TIMEOUT: Final[int] = 10_000

    #: 页面导航默认上限（``page.goto(..., timeout=...)``）
    NAVIGATION_TIMEOUT: Final[int] = 60_000

    #: 顶部导航切换较慢（涉及 SPA 路由 + iframe 内容加载），需要更宽松的等待
    TOP_MENU_SWITCH_TIMEOUT: Final[int] = 120_000

    #: 模板构建轮询总时长上限；配合 ``POLL_INTERVAL`` 决定最大轮询轮次
    BUILD_MAX_WAIT: Final[int] = 120_000


__all__ = ["UITimeout"]
