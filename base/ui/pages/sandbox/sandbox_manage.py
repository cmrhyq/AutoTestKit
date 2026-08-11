import re

from playwright.sync_api import Page, expect

from base.ui.pages.base import BasePage
from constants.bussiness import SandboxFramePath
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

        # 自动刷新
        self.link_auto_refresh = self.frame.get_by_text("自动刷新")
        self.item_refresh_5s = self.frame.get_by_text("5s", exact=True)

    def navigate_to(self, base_url: str) -> None:
        """
        通过URL直接导航进入沙箱管理页面（菜单点击可能不刷新iframe）
        """
        logger.info(f"导航到沙箱管理: {SandboxFramePath.SANDBOX_MANAGE}")
        self.page.goto(base_url + SandboxFramePath.SANDBOX_MANAGE, timeout=60000)
        self.page.wait_for_load_state(state="load")
        self.page.wait_for_timeout(1000)

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

    def auto_refresh(self):
        self.link_auto_refresh.click()
        self.item_refresh_5s.click()

    # ==================== 存活沙箱搜索 ====================

    def search_alive_sandbox(self, tenant_name: str = None, sandbox_id_or_template: str = None):
        # 在存活沙箱tab按条件搜索（实际无"模板类别"下拉，仅租户名称+沙箱ID两个textbox）
        logger.info(f"搜索存活沙箱: tenant={tenant_name}, id/template={sandbox_id_or_template}")
        if tenant_name:
            if self.input_tenant_alive.is_visible():
                self.input_tenant_alive.fill(tenant_name)
        if sandbox_id_or_template:
            if self.input_sandbox_id.is_visible():
                self.input_sandbox_id.fill(sandbox_id_or_template)
        # 查询
        self.btn_search_alive.click()
        self.page.wait_for_timeout(1000)

    def get_alive_sandbox_count(self) -> int:
        # 获取存活沙箱数据行数
        try:
            return self.table_data.get_by_role("row").count()
        except Exception:
            return 0

    def is_sandbox_alive(self, sandbox_id: str) -> bool:
        # 检查指定沙箱ID是否在存活沙箱列表中
        try:
            self.search_alive_sandbox(sandbox_id_or_template=sandbox_id)
            row = self.table_data.get_by_role("row", name=re.compile(re.escape(sandbox_id))).first
            return row.is_visible()
        except Exception:
            return False

    # ==================== 删除沙箱实例 ====================

    def click_delete_sandbox(self, sandbox_id: str):
        # 点击沙箱的删除按钮
        logger.info(f"点击沙箱【{sandbox_id}】的删除按钮")
        row = self.table_data.get_by_role("row", name=re.compile(re.escape(sandbox_id))).first
        expect(row).to_be_visible()
        row.get_by_role("button", name="删除").click()
        self.page.wait_for_timeout(800)

    def confirm_delete(self):
        # 确认删除沙箱实例
        if self.msg_box.is_visible():
            self.msg_box.get_by_role("button", name=re.compile(r"删除")).last.click()
            self.page.wait_for_timeout(1000)

    # ==================== 历史沙箱 ====================

    def search_history_sandbox(self, tenant_name: str = None):
        # 在历史沙箱tab搜索
        logger.info(f"搜索历史沙箱: tenant={tenant_name}")
        if tenant_name:
            if self.input_tenant_history.is_visible():
                self.input_tenant_history.fill(tenant_name)
        self.btn_search_history.click()
        self.page.wait_for_timeout(1000)

    def get_history_sandbox_count(self) -> int:
        # 获取历史沙箱行数
        try:
            return self.table_data.get_by_role("row").count()
        except Exception:
            return 0

    # ==================== 指标统计 ====================

    def get_alive_metrics(self) -> dict:
        # 获取存活沙箱tab的统计卡片数据（CPU/内存/磁盘/沙箱数）
        metrics = {}
        try:
            # 统计卡片文本中通常包含"CPU使用率"、"内存使用率"等关键词
            for label in ["CPU使用率", "内存使用率", "磁盘", "正在运行"]:
                try:
                    el = self.frame.locator(f"text=/{label}.*\\d+/").first
                    if el.is_visible():
                        metrics[label] = el.text_content().strip()
                except Exception:
                    pass
        except Exception:
            pass
        return metrics
