import re

from playwright.sync_api import Page

from base.ui.pages.base import BasePage
from constants.bussiness import SandboxFramePath
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

    def navigate_to(self, base_url: str) -> None:
        """
        通过URL直接导航进入镜像库管理页面（菜单点击可能不刷新iframe）
        """
        logger.info(f"导航到镜像库管理: {SandboxFramePath.IMAGE_LIBRARY_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.IMAGE_LIBRARY_MANAGE, timeout=60000)
        self.page.wait_for_load_state(state="load")
        self.page.wait_for_timeout(1000)

    def switch_to_system_image(self):
        """
        切换到系统镜像tab
        """
        logger.info("切换到系统镜像tab")
        self.tab_system_image.click()
        self.page.wait_for_timeout(1000)

    def switch_to_custom_image(self):
        """
        切换到自定义镜像tab
        """
        logger.info("切换到自定义镜像tab")
        self.tab_custom_image.click()
        self.page.wait_for_timeout(1000)

    def search_image(self, image_name: str):
        """
        搜索镜像
        """
        logger.info(f"搜索镜像: {image_name}")
        self.input_search.fill(image_name)
        self.btn_search.click()
        self.page.wait_for_timeout(800)

    def get_first_system_image_name(self) -> str:
        """
        获取系统镜像列表中第一条镜像名称
        """
        try:
            first_row = self.table_body.get_by_role("row").first
            # 镜像名称通常在第2列
            cells = first_row.locator("td")
            if cells.count() >= 2:
                return cells.nth(1).text_content().strip()
        except Exception:
            pass
        return ""

    def get_all_system_image_names(self) -> list:
        """
        获取系统镜像列表中所有镜像名称
        """
        names = []
        try:
            rows = self.table_body.get_by_role("row")
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                if cells.count() >= 2:
                    names.append(cells.nth(1).text_content().strip())
        except Exception:
            pass
        return names

    def get_image_id_by_name(self, image_name: str) -> str:
        """
        按镜像名称获取镜像ID
        """
        try:
            row = self.table_body.get_by_role(
                "row", name=re.compile(re.escape(image_name))
            ).first
            if row.is_visible():
                return row.locator("td").first.text_content().strip()
        except Exception:
            pass
        return ""
