from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class BuildRecordPage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 Build Record Page 页面对象（模板管理 - 构建记录）

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("Build Record Page Initialized")

        # 沙箱主内容iframe
        self.frame = page.locator("iframe").first.content_frame

        # 搜索区域
        self.input_search = self.frame.get_by_placeholder("请输入模板名称或ID")
        self.btn_search = self.frame.get_by_role("button", name="查询")

        # 数据表格
        self.table_data = self.frame.get_by_role("table").first

    def navigate_to(self, base_url: str) -> None:
        """
        通过URL直接导航进入构建记录页面（菜单点击可能不刷新iframe）
        """
        logger.info(f"导航到构建记录: {SandboxFramePath.BUILD_RECORD}")
        self.page.goto(base_url + SandboxFramePath.BUILD_RECORD, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.input_search).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
