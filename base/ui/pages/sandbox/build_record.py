"""
构建记录 Page Object（沙箱 -> 模板管理 -> 构建记录）。

页面结构：
    - 搜索区: 构建状态下拉 + 模板名称/ID 输入框 + 查询按钮
    - 数据表格: 构建历史记录（模板ID、模板、状态、开始时间、描述等）
    - 分页: 每页条数切换 + 上一页/下一页
"""
import re

from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout
from core.constants.bussiness import SandboxFramePath, BuildRecordStatus, PageSize

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
        self.dropdown_build_status = self.frame.get_by_text("请选择构建状态")
        self.btn_search = self.frame.get_by_role("button", name="查询")

        # ==================== 数据表格 ====================
        self.table_data = self.frame.get_by_role("table").first

        # 表头列
        self.col_template_id = self.frame.get_by_role("columnheader", name="模板ID")
        self.col_template = self.frame.get_by_text("模板", exact=True)
        self.col_status = self.frame.get_by_text("状态", exact=True)
        self.col_start_time = self.frame.get_by_text("开始时间")
        self.col_description = self.frame.get_by_text("描述")

        # ==================== 分页 ====================
        self.btn_next_page = self.frame.get_by_role("button", name="下一页")
        self.btn_prev_page = self.frame.get_by_role("button", name="上一页")

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

    def chose_build_status(self, build_status: BuildRecordStatus) -> None:
        """选择构建状态下拉选项。

        Args:
            build_status: 状态文本，如 "成功"、"失败"、"构建中"
        """
        logger.info(f"选择构建状态：{build_status}")
        self.dropdown_build_status.click()
        self.frame.get_by_role("option", name=build_status).click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def change_page_size(self, size: PageSize) -> None:
        """切换每页显示条数。

        Args:
            size: 每页条数文本，如 "10条/页"、"20条/页"
        """
        logger.info(f"切换每页条数: {size}")
        # 点击当前分页大小下拉
        self.frame.locator("div").filter(has_text=re.compile(r"^\d+条/页$")).last.click()
        self.frame.get_by_role("option", name=size).click()
        self.page.wait_for_timeout(UITimeout.QUERY)
