"""
节点管理 Page Object（沙箱 -> 沙箱集群 -> 节点管理）。

页面结构：
    - 搜索区: 节点 ID 输入框 + 查询按钮 + 刷新按钮
    - 数据表格: 节点列表

关键约定：
    - **iframe 定位**：主内容在 iframe 内，通过 ``page.locator("iframe").first.content_frame``
      获取 FrameLocator（每次访问自动重新解析，避免 iframe 重载后引用失效）。
    - **表格定位**：iframe 内第 1 个 ``<table>`` 是表头，第 2 个是数据行。
    - **管理视图独占**：该页面属于沙箱集群下级菜单，用户视图不可见。
"""
from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class NodeManagePage(BasePage):
    """节点管理 Page Object。

    当前仅提供页面导航与元素定位，具体查询/操作交互按需扩展。
    """

    def __init__(self, page: Page):
        """初始化节点管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Node Manage Page Initialized")

        # 沙箱主内容 iframe
        self.frame = page.locator("iframe").first.content_frame

        # ==================== 搜索区 ====================
        self.input_node_id = self.frame.get_by_placeholder("请输入节点ID")
        self.btn_search = self.frame.get_by_role("button", name="查询")
        self.btn_refresh = self.frame.get_by_role("button", name="刷新")

        # ==================== 数据表格 ====================
        # Note: iframe 内第 1 个 table 是表头，第 2 个是数据行
        self.table_data = self.frame.get_by_role("table").nth(1)

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入节点管理页面。

        菜单点击有时不刷新 iframe，稳定性要求高的用例应优先使用本方法。
        末尾通过节点 ID 输入框可见性判定页面渲染完成，代替固定 sleep。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到节点管理: {SandboxFramePath.NODE_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.NODE_MANAGE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.input_node_id).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
