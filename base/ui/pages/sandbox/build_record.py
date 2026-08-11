"""
构建记录 Page Object（沙箱 -> 模板管理 -> 构建记录）。

页面结构：
    - 搜索区: 模板名称/ID 输入框 + 查询按钮
    - 数据表格: 构建历史记录（模板、构建人、状态、耗时、时间等）

关键约定：
    - **iframe 定位**：主内容在 iframe 内，通过 ``page.locator("iframe").first.content_frame``
      获取 FrameLocator（每次访问自动重新解析）。
    - **表格定位**：该页面表格结构较为简单，直接使用 ``get_by_role("table").first``。
"""
from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class BuildRecordPage(BasePage):
    """构建记录 Page Object。

    当前仅提供页面导航与元素定位，具体查询/日志读取交互按需扩展。
    """

    def __init__(self, page: Page):
        """初始化构建记录页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Build Record Page Initialized")

        # 沙箱主内容 iframe
        self.frame = page.locator("iframe").first.content_frame

        # ==================== 搜索区 ====================
        self.input_search = self.frame.get_by_placeholder("请输入模板名称或ID")
        self.btn_search = self.frame.get_by_role("button", name="查询")

        # ==================== 数据表格 ====================
        # Note: 构建记录页表格结构较简单，第 1 个 table 即数据表
        self.table_data = self.frame.get_by_role("table").first

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入构建记录页面。

        菜单点击有时不刷新 iframe，稳定性要求高的用例应优先使用本方法。
        末尾通过搜索输入框可见性判定页面渲染完成。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到构建记录: {SandboxFramePath.BUILD_RECORD}")
        self.page.goto(base_url + SandboxFramePath.BUILD_RECORD, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.input_search).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
