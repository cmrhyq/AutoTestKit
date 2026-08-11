from playwright.sync_api import Page

from base.ui.pages.base import BasePage
from core import get_logger

logger = get_logger(__name__)


class SandboxManagePage(BasePage):

    def __init__(self, page: Page):
        """
        初始化 Sandbox Manage Page 页面对象

        Args:
            page: Playwright Page 对象
        """
        super().__init__(page)
        logger.info("Sandbox Manage Page Initialized")

        # 沙箱主内容iframe（FrameLocator 每次访问时自动重新解析）
        self.frame = page.locator("iframe").first.content_frame

        # tab 切换
        self.tab_alive = self.frame.get_by_role("tab", name="存活沙箱")
        self.tab_history = self.frame.get_by_role("tab", name="历史沙箱")

        # 存活沙箱搜索区域（实际无"模板类别"下拉，仅租户名称+沙箱ID两个textbox）
        self.input_tenant_alive = self.frame.get_by_placeholder("请输入租户名称")
        self.input_sandbox_id = self.frame.get_by_placeholder("请输入沙箱ID或模板名称")
        self.btn_search_alive = self.frame.get_by_role("button", name="查询")

        # 历史沙箱搜索区域（租户名称+开始日期+结束日期+查询）
        self.input_tenant_history = self.frame.get_by_placeholder("请输入租户名称")
        self.input_start_date = self.frame.get_by_placeholder("开始日期")
        self.input_end_date = self.frame.get_by_placeholder("结束日期")
        self.btn_search_history = self.frame.get_by_role("button", name="查询")

        # 数据表格（第2个table，第1个为表头；存活/历史共用定位方式）
        self.table_data = self.frame.get_by_role("table").nth(1)

        # 删除确认弹窗
        self.msg_box = self.frame.locator(".ep-message-box, .el-message-box, .message-box").first
        self.alert = self.frame.locator(".ep-message__content, .el-message__content").first

        #自动刷新
        self.link_auto_refresh=self.frame.get_by_text("自动刷新")
        self.item_refresh_5s=self.frame.get_by_text("5s", exact=True)

    # ==================== tab 切换 ====================

    def switch_to_alive(self):
        # 切换到存活沙箱tab
        logger.info("切换到存活沙箱tab")
        self.tab_alive.click()
        self.page.wait_for_timeout(1000)

    def switch_to_history(self):
        # 切换到历史沙箱tab
        logger.info("切换到历史沙箱tab")
        self.tab_history.click()
        self.page.wait_for_timeout(1000)