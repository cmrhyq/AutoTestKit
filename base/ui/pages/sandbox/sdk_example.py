"""
SDK 使用示例 Page Object（沙箱 -> SDK 使用示例）。

页面结构：
    - 页头: "SDK使用示例" 标题 + "下载SDK使用pdf" 按钮
    - 章节一: "一、SDK安装" — PyPi虚拟库配置 + SDK下载命令（代码块）
    - 章节二: "二、环境配置" — 环境变量配置（代码块）
    - 章节三: "三、使用示例" — 表格（场景、模板ID、集成、备注、示例）
    - 示例代码弹窗: 点击"查看示例"后弹出

iframe src: /sandbox-web/sdk/examples
UI 框架: Element Plus (el- 前缀) + CodeMirror 代码编辑器
"""
from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath

logger = get_logger(__name__)


class SdkExamplePage(BasePage):
    """SDK 使用示例 Page Object。"""

    def __init__(self, page: Page):
        """初始化 SDK 使用示例页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("SDK Example Page Initialized")

        # 沙箱主内容 iframe
        self.frame = page.locator("iframe").first.content_frame

        # ==================== 页头 ====================
        self.title_sdk_example = self.frame.locator(".page-header").get_by_text("SDK使用示例")
        self.btn_download_pdf = self.frame.get_by_role("button", name="下载SDK使用pdf")

        # ==================== 章节标题 ====================
        self.title_sdk_install = self.frame.locator(".section-title").filter(has_text="一、SDK安装")
        self.title_env_config = self.frame.locator(".section-title").filter(has_text="二、环境配置")
        self.title_usage_example = self.frame.locator(".section-title").filter(has_text="三、使用示例")

        # ==================== 代码块（CodeMirror） ====================
        # 3个代码块：PyPi配置、SDK下载、环境变量
        self.code_blocks = self.frame.locator(".code-mirror-wrapper")
        self.code_block_pypi = self.code_blocks.nth(0)
        self.code_block_install = self.code_blocks.nth(1)
        self.code_block_env = self.code_blocks.nth(2)

        # 代码块复制按钮
        self.btn_copy_buttons = self.frame.locator(".copy-button")

        # ==================== 使用示例表格 ====================
        self.table_example = self.frame.get_by_role("table").nth(1)  # 第2个table是数据行

        # 表头列
        self.col_scenario = self.frame.get_by_role("columnheader", name="场景")
        self.col_template_id = self.frame.get_by_role("columnheader", name="模板ID")
        self.col_integration = self.frame.get_by_role("columnheader", name="集成")
        self.col_remark = self.frame.get_by_role("columnheader", name="备注")
        self.col_example = self.frame.get_by_role("columnheader", name="示例")

        # ==================== 示例代码弹窗 ====================
        self.dialog_example_code = self.frame.locator(
            ".el-overlay-dialog"
        ).filter(has_text="示例代码")

    # ==================== 导航 ====================

    def navigate_to(self, base_url: str) -> None:
        """通过 URL 直接导航进入 SDK 使用示例页面。

        Args:
            base_url: 站点根 URL（``http[s]://host[:port]``），不含 iframe 路径。
        """
        logger.info(f"导航到SDK使用示例: {SandboxFramePath.SDK_EXAMPLE}")
        self.page.goto(base_url + SandboxFramePath.SDK_EXAMPLE, timeout=UITimeout.NAVIGATION_TIMEOUT)
        self.page.wait_for_load_state(state="load")
        expect(self.title_sdk_example).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)

    # ==================== 操作方法 ====================

    def click_view_example(self, scenario: str) -> None:
        """点击指定场景行的"查看示例"按钮。

        Args:
            scenario: 场景名称，如 "代码沙箱"、"桌面沙箱"、"浏览器沙箱"、"基础沙箱"
        """
        logger.info(f"查看示例：{scenario}")
        row = self.frame.get_by_role("row").filter(has_text=scenario)
        row.get_by_role("button", name="查看示例").click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def copy_code_block(self, index: int = 0) -> None:
        """点击指定代码块的复制按钮。

        Args:
            index: 代码块索引（0=PyPi配置, 1=SDK下载, 2=环境变量）
        """
        logger.info(f"复制第 {index + 1} 个代码块")
        self.btn_copy_buttons.nth(index).click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)
