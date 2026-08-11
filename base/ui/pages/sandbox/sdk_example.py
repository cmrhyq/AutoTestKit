"""
SDK 使用示例 Page Object（沙箱 -> SDK 使用示例）。

页面结构：
    - 页面标题: "SDK 使用示例"
    - 章节标题: "一、SDK 安装" 等
    - 下载 PDF 按钮
    - 使用示例表格（各语言 SDK 的示例代码等）

关键约定：
    - **iframe 定位**：主内容在 iframe 内，通过 ``page.locator("iframe").first.content_frame``
      获取 FrameLocator。
"""
from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class SdkExamplePage(BasePage):
    """SDK 使用示例 Page Object。

    当前仅提供页面导航与元素定位，具体下载/展开交互按需扩展。
    """

    def __init__(self, page: Page):
        """初始化 SDK 使用示例页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("SDK Example Page Initialized")

        # 沙箱主内容 iframe
        self.frame = page.locator("iframe").first.content_frame

        # 页面标题（.first 避免命中侧边栏菜单同名文本）
        self.title_sdk_example = self.frame.get_by_text("SDK使用示例").first

        # 首个章节标题："一、SDK 安装"
        self.title_sdk_install = self.frame.get_by_text("一、SDK安装").first

        # 下载 PDF 按钮
        self.btn_download_pdf = self.frame.get_by_role("button", name="下载SDK使用pdf")

        # 使用示例表格（页面结构较简单，第 1 个 table 即示例表）
        self.table_example = self.frame.get_by_role("table").first

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入 SDK 使用示例页面。

        菜单点击有时不刷新 iframe，稳定性要求高的用例应优先使用本方法。
        末尾通过页面标题可见性判定渲染完成。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到SDK使用示例: {SandboxFramePath.SDK_EXAMPLE}")
        self.page.goto(base_url + SandboxFramePath.SDK_EXAMPLE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.title_sdk_example).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
