"""
镜像库管理 Page Object（沙箱 -> 镜像管理 -> 镜像库管理）。

页面结构：
    - Tab: **系统镜像** / **自定义镜像**
    - 搜索区: 镜像名称输入框 + 查询按钮
    - 数据表格：第 1 列镜像ID、第 2 列镜像名称、其它列为规格/标签等

关键约定：
    - **iframe 定位**：主内容在 iframe 内，通过 ``page.locator("iframe").first.content_frame``
      获取 FrameLocator，避免 iframe 重载导致的引用失效。
    - **表格定位**：iframe 内第 1 个 ``<table>`` 是表头，第 2 个是数据行，
      因此使用 ``get_by_role("table").nth(1)``。
"""
import re
from typing import List

from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class ImageLibraryPage(BasePage):
    """镜像库管理 Page Object。

    覆盖系统/自定义镜像 tab 切换、镜像搜索、镜像 ID/名称读取等操作。
    """

    def __init__(self, page: Page):
        """初始化镜像库管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Image Library Page Initialized")

        # 沙箱主内容 iframe（FrameLocator 每次访问自动重新解析）
        self.frame = page.locator("iframe").first.content_frame

        # ==================== Tab ====================
        self.tab_system_image = self.frame.get_by_role("tab", name="系统镜像")
        self.tab_custom_image = self.frame.get_by_role("tab", name="自定义镜像")

        # ==================== 搜索区 ====================
        self.input_search = self.frame.get_by_placeholder("请输入镜像名称")
        self.btn_search = self.frame.get_by_role("button", name="查询")

        # ==================== 数据表格 ====================
        # Note: iframe 内第 1 个 table 是表头容器，第 2 个才是数据行
        self.table_body = self.frame.get_by_role("table").nth(1)

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入镜像库管理页面。

        菜单点击有时不刷新 iframe，稳定性要求高的用例应优先使用本方法。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到镜像库管理: {SandboxFramePath.IMAGE_LIBRARY_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.IMAGE_LIBRARY_MANAGE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        # 通过 tab 可见性代替固定 sleep 判定 iframe 内首次渲染完成
        expect(self.tab_system_image).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    # ==================== Tab 切换 ====================

    def switch_to_system_image(self) -> None:
        """切换到"系统镜像"tab，并等待 tab 变为激活状态。"""
        logger.info("切换到系统镜像tab")
        self.tab_system_image.click()
        self._wait_tab_active(self.tab_system_image, "系统镜像")

    def switch_to_custom_image(self) -> None:
        """切换到"自定义镜像"tab，并等待 tab 变为激活状态。"""
        logger.info("切换到自定义镜像tab")
        self.tab_custom_image.click()
        self._wait_tab_active(self.tab_custom_image, "自定义镜像")

    def _wait_tab_active(self, tab: Locator, tab_name: str) -> None:
        """等待 tab 变为激活状态。

        优先通过 ``aria-selected="true"`` 属性判定；无法判定时退化为短稳定等待。

        Args:
            tab: tab 元素定位器。
            tab_name: 用于日志的 tab 名称。
        """
        try:
            expect(tab).to_have_attribute(
                "aria-selected", "true", timeout=UITimeout.STABILIZE
            )
        except (PlaywrightTimeoutError, AssertionError):
            logger.debug(f"tab【{tab_name}】未通过 aria-selected 判定激活，退化为短稳定等待")
            self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 列表操作 ====================

    def search_image(self, image_name: str) -> None:
        """按名称搜索镜像。

        搜索后短稳定等待表格刷新完成。

        Args:
            image_name: 镜像名称。
        """
        logger.info(f"搜索镜像: {image_name}")
        self.input_search.fill(image_name)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    # ==================== 表格读取 ====================

    def get_first_system_image_name(self) -> str:
        """获取当前列表第一行的镜像名称（第 2 列）。

        Returns:
            str: 镜像名称；无数据或读取失败时返回 ``""``。
        """
        try:
            first_row = self.table_body.get_by_role("row").first
            # 镜像名称位于第 2 列（第 1 列是镜像 ID）
            cells = first_row.locator("td")
            if cells.count() >= 2:
                # Note: text_content() 可能返回 None，用 `or ""` 兜底
                return (cells.nth(1).text_content() or "").strip()
        except PlaywrightTimeoutError:
            logger.debug("获取第一条镜像名称超时")
        return ""

    def get_all_system_image_names(self) -> List[str]:
        """获取当前列表所有行的镜像名称（第 2 列）。

        Returns:
            list[str]: 名称列表；遍历中途异常时返回已收集到的部分结果。
        """
        names: List[str] = []
        try:
            rows = self.table_body.get_by_role("row")
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                if cells.count() >= 2:
                    names.append((cells.nth(1).text_content() or "").strip())
        except PlaywrightTimeoutError:
            logger.debug("遍历镜像列表超时")
        return names

    def get_image_id_by_name(self, image_name: str) -> str:
        """按镜像名称在当前列表定位镜像行，读取第 1 列（镜像 ID）。

        Args:
            image_name: 镜像名称。

        Returns:
            str: 镜像 ID；未匹配到行或读取失败时返回 ``""``。
        """
        try:
            row = self.table_body.get_by_role(
                "row", name=re.compile(re.escape(image_name))
            ).first
            if row.is_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT):
                return (row.locator("td").first.text_content() or "").strip()
        except PlaywrightTimeoutError:
            logger.debug(f"按名称获取镜像ID超时: {image_name}")
        return ""
