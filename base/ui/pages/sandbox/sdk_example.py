from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class SdkExamplePage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 SDK Example Page 页面对象（SDK使用示例）

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("SDK Example Page Initialized")

        # 沙箱主内容iframe
        self.frame = page.locator("iframe").first.content_frame

        # 页面标题
        self.title_sdk_example = self.frame.get_by_text("SDK使用示例").first

        # SDK安装章节标题
        self.title_sdk_install = self.frame.get_by_text("一、SDK安装").first

        # 下载按钮
        self.btn_download_pdf = self.frame.get_by_role("button", name="下载SDK使用pdf")

        # 使用示例表格
        self.table_example = self.frame.get_by_role("table").first

    def navigate_to(self, base_url: str) -> None:
        """
        通过URL直接导航进入SDK使用示例页面（菜单点击可能不刷新iframe）
        """
        logger.info(f"导航到SDK使用示例: {SandboxFramePath.SDK_EXAMPLE}")
        self.page.goto(base_url + SandboxFramePath.SDK_EXAMPLE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.title_sdk_example).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
