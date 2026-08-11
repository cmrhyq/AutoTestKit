from playwright.sync_api import Page

from base.ui.pages.base import BasePage
from constants.bussiness import SandboxFramePath
from core import get_logger

logger = get_logger(__name__)


class NodeManagePage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 Node Manage Page 页面对象（沙箱集群 - 节点管理）

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("Node Manage Page Initialized")

        # 沙箱主内容iframe
        self.frame = page.locator("iframe").first.content_frame

        # 搜索区域
        self.input_node_id = self.frame.get_by_placeholder("请输入节点ID")
        self.btn_search = self.frame.get_by_role("button", name="查询")
        self.btn_refresh = self.frame.get_by_role("button", name="刷新")

        # 数据表格（第2个table，第1个为表头）
        self.table_data = self.frame.get_by_role("table").nth(1)

    def navigate_to(self, base_url: str) -> None:
        """
        通过URL直接导航进入节点管理页面（菜单点击可能不刷新iframe）
        """
        logger.info(f"导航到节点管理: {SandboxFramePath.NODE_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.NODE_MANAGE, timeout=60000)
        self.page.wait_for_load_state(state="load")
        self.page.wait_for_timeout(1000)
