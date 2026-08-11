from playwright.sync_api import Page

from base.ui.pages.base import BasePage
from core import get_logger

logger = get_logger(__name__)


class ImageLibraryPage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 Image Library Page 页面对象

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("Image Library Page Initialized")

        # 沙箱主内容iframe（FrameLocator 每次访问时自动重新解析）
        self.frame = page.locator("iframe").first.content_frame

        # tab 切换
        self.tab_system_image = self.frame.get_by_role("tab", name="系统镜像")
        self.tab_custom_image = self.frame.get_by_role("tab", name="自定义镜像")

        # 搜索区域
        self.input_search = self.frame.get_by_placeholder("请输入镜像名称")
        self.btn_search = self.frame.get_by_role("button", name="查询")

        # 数据表格（第2个table，第1个为表头）
        self.table_body = self.frame.get_by_role("table").nth(1)

        # ==================== tab 切换 ====================

    def switch_to_system_image(self):
        # 切换到系统镜像tab
        logger.info("切换到系统镜像tab")
        self.tab_system_image.click()
        self.page.wait_for_timeout(1000)

    def switch_to_custom_image(self):
        # 切换到自定义镜像tab
        logger.info("切换到自定义镜像tab")
        self.tab_custom_image.click()
        self.page.wait_for_timeout(1000)