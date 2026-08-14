"""消费者应用 Page Object（AIOS -> 消费者应用）。

页面结构：
    - 搜索区: 所属租户下拉 + 应用名称关键字搜索框 + 查询按钮 + 刷新缓存按钮 + 新增按钮
    - 数据表格: 应用名称、AppSecret、所属租户、创建人、创建时间、已订阅API数、操作
    - 操作列图标: ri-file-list-2-line(查看详情) / ri-edit-2-line(编辑)
      / ri-refresh-line(重新生成密钥) / ri-delete-bin-line(删除)
    - 弹窗: 新增消费者应用 / 编辑消费者应用 / 删除确认 message-box

关键约定：
    - 本页面渲染在主文档中（非 iframe），直接使用 ``page`` 定位；
    - 表格为 Element Plus 结构，get_by_role("table") 匹配 header + body 两个 table，
      ``nth(1)`` 才是数据行表；
    - 新增按钮在小窗口下文本隐藏，通过 ri-add-line 图标定位；
    - 已订阅API数位于数据行第 6 列（index 5）。
"""
import re
from typing import Optional

from playwright.sync_api import Locator, Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout

logger = get_logger(__name__)


class ConsumerAppPage(BasePage):
    """消费者应用 Page Object。"""

    def __init__(self, page: Page):
        """初始化消费者应用页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Consumer App Page Initialized")

        # ==================== 搜索区 ====================
        self.dropdown_tenant = page.locator(
            ".ep-form-item:has-text('所属租户') .ep-select__wrapper"
        ).first
        self.input_app_name = page.get_by_placeholder("应用名称关键字")
        self.btn_search = page.get_by_role("button", name="查询")
        self.btn_refresh_cache = page.get_by_role("button", name="刷新缓存")

        # 新增按钮（小窗口下文本隐藏，用图标定位）
        self.btn_add = page.locator("button:has(.ri-add-line)")

        # ==================== 数据表格 ====================
        self.table = page.get_by_role("table").first

        # ==================== 新增消费者应用弹窗 ====================
        self.dialog_add = page.get_by_role("dialog", name="新增消费者应用")
        self.input_add_name = self.dialog_add.get_by_role("textbox", name="应用名称")
        self.input_add_desc = self.dialog_add.get_by_role("textbox", name="应用描述")
        self.btn_add_confirm = self.dialog_add.get_by_role("button", name="确定")
        self.btn_add_cancel = self.dialog_add.get_by_role("button", name="取消")

        # ==================== 编辑消费者应用弹窗 ====================
        self.dialog_edit_app = page.get_by_role("dialog", name="编辑消费者应用")
        self.input_edit_name = self.dialog_edit_app.get_by_role("textbox", name="应用名称")
        self.input_edit_desc = self.dialog_edit_app.get_by_role("textbox", name="应用描述")
        self.btn_edit_confirm = self.dialog_edit_app.get_by_role("button", name="确定")
        self.btn_edit_cancel = self.dialog_edit_app.get_by_role("button", name="取消")

        # ==================== 删除/确认 message-box ====================
        self.msgbox = page.locator(".ep-overlay-message-box").first
        self.btn_msgbox_delete = self.msgbox.get_by_role("button", name=re.compile(r"删除")).last
        self.btn_msgbox_confirm = self.msgbox.get_by_role("button", name="确定")

        # ==================== 分页统计与面包屑 ====================
        self.text_total = page.locator("text=/共 \\d+ 条/")
        self.menu_bread_app = page.get_by_label("面包屑").get_by_text("消费者应用")

    # ==================== 内部辅助方法 ====================

    def _get_data_table(self) -> Locator:
        """获取数据表格（Element Plus 表格第 1 个是表头，第 2 个是数据行）。"""
        return self.page.get_by_role("table").nth(1)

    def _get_row_by_name(self, app_name: str) -> Locator:
        """按应用名称定位数据行。"""
        return self._get_data_table().get_by_role(
            "row", name=re.compile(re.escape(app_name))
        ).first

    def _click_row_icon(self, app_name: str, icon_selector: str) -> None:
        """在指定应用行点击操作图标。"""
        row = self._get_row_by_name(app_name)
        expect(row).to_be_visible()
        row.locator(icon_selector).first.click()

    # ==================== 搜索/筛选 ====================

    def search_by_name(self, keyword: str) -> None:
        """按应用名称关键字搜索。"""
        logger.info(f"搜索消费者应用名称: {keyword}")
        self.input_app_name.fill(keyword)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def search_by_tenant(self, tenant_name: str) -> None:
        """按所属租户筛选（选择租户下拉后查询）。"""
        logger.info(f"按租户筛选消费者应用: {tenant_name}")
        self.dropdown_tenant.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.page.get_by_role("option", name=tenant_name, exact=True).click()
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    # ==================== 新增消费者应用 ====================

    def click_add(self) -> None:
        """点击新增按钮，打开新增消费者应用弹窗。"""
        logger.info("点击新增消费者应用按钮")
        self.btn_add.click()
        expect(self.dialog_add).to_be_visible()

    def fill_add_form(self, app_name: str, app_desc: Optional[str] = None) -> None:
        """填写新增消费者应用表单。"""
        logger.info(f"填写新增消费者应用: 名称={app_name}")
        expect(self.dialog_add).to_be_visible()
        self.input_add_name.fill(app_name)
        if app_desc is not None:
            self.input_add_desc.fill(app_desc)

    def confirm_add(self) -> None:
        """确认新增消费者应用。"""
        logger.info("确认新增消费者应用")
        self.btn_add_confirm.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def cancel_add(self) -> None:
        """取消新增消费者应用。"""
        logger.info("取消新增消费者应用")
        self.btn_add_cancel.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def create_consumer_app(self, app_name: str, app_desc: str) -> None:
        """创建消费者应用（幂等：已存在则跳过）。"""
        self.search_by_name(app_name)
        row = self._get_row_by_name(app_name)
        if row.is_visible():
            logger.info(f"消费者应用【{app_name}】已存在，跳过创建")
            return

        self.click_add()
        self.fill_add_form(app_name, app_desc)
        self.confirm_add()
        self.menu_bread_app.click()  # 返回应用菜单
        self.search_by_name(app_name)
        expect(self._get_row_by_name(app_name)).to_be_visible()
        logger.info(f"消费者应用【{app_name}】创建成功")

    # ==================== 行操作 ====================

    def click_row_view(self, app_name: str) -> None:
        """点击行内查看图标，进入详情页。"""
        logger.info(f"点击消费者应用【{app_name}】的查看进入详情")
        self._click_row_icon(app_name, ".ri-file-list-2-line")
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def click_app_name(self, app_name: str) -> None:
        """点击应用名称进入详情（click_row_view 的别名）。"""
        self.click_row_view(app_name)

    def click_row_edit(self, app_name: str) -> None:
        """点击行内编辑按钮。"""
        logger.info(f"点击消费者应用【{app_name}】的编辑按钮")
        self._click_row_icon(app_name, ".ri-edit-2-line")
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_row_regenerate_key(self, app_name: str) -> None:
        """点击行内重新生成密钥按钮。"""
        logger.info(f"点击消费者应用【{app_name}】的重新生成密钥按钮")
        self._click_row_icon(app_name, ".ri-refresh-line")
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_row_delete(self, app_name: str) -> None:
        """点击行内删除按钮。"""
        logger.info(f"点击消费者应用【{app_name}】的删除按钮")
        self._click_row_icon(app_name, ".ri-delete-bin-line")
        self.page.wait_for_timeout(UITimeout.SHORT)

    def get_subscribe_count(self, app_name: str) -> int:
        """获取某应用行「已订阅API数」列的值（第 6 列，index 5）。"""
        logger.info(f"获取消费者应用【{app_name}】的已订阅API数")
        row = self._get_row_by_name(app_name)
        expect(row).to_be_visible()
        # 列顺序: 应用名称(0) AppSecret(1) 所属租户(2) 创建人(3) 创建时间(4) 已订阅API数(5) 操作(6)
        return int(row.get_by_role("cell").nth(5).inner_text().strip())

    # ==================== 确认弹窗 ====================

    def confirm_delete(self) -> None:
        """在删除确认弹窗中点击删除。"""
        expect(self.msgbox).to_be_visible()
        self.btn_msgbox_delete.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def confirm_regenerate(self) -> None:
        """在重新生成密钥确认弹窗中点击确定。"""
        expect(self.msgbox).to_be_visible()
        self.btn_msgbox_confirm.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 编辑弹窗 ====================

    def fill_edit_form(self, app_name: Optional[str] = None, app_desc: Optional[str] = None) -> None:
        """填写编辑消费者应用表单。"""
        expect(self.dialog_edit_app).to_be_visible()
        if app_name is not None:
            self.input_edit_name.fill(app_name)
        if app_desc is not None:
            self.input_edit_desc.fill(app_desc)

    def confirm_edit(self) -> None:
        """确认编辑消费者应用。"""
        self.btn_edit_confirm.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def cancel_edit(self) -> None:
        """取消编辑消费者应用。"""
        self.btn_edit_cancel.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    # ==================== 分页统计 ====================

    def get_row_count(self) -> int:
        """获取当前列表数据行数。"""
        return self._get_data_table().get_by_role("row").count()

    def get_total_count(self) -> int:
        """获取列表总条数。"""
        if self.text_total.is_visible():
            match = re.search(r"(\d+)", self.text_total.text_content())
            if match:
                return int(match.group(1))
        return 0

    # ==================== 数据清理 ====================

    def cleanup_consumer_app(self, app_name: str) -> None:
        """安全删除消费者应用（幂等）。"""
        logger.info(f"清理消费者应用: {app_name}")
        try:
            self.search_by_name(app_name)
            row = self._get_row_by_name(app_name)
            if row.is_visible():
                self.click_row_delete(app_name)
                self.confirm_delete()
                logger.info(f"消费者应用【{app_name}】删除成功")
            else:
                logger.info(f"消费者应用【{app_name}】不存在，无需清理")
        except Exception as e:
            logger.info(f"清理消费者应用【{app_name}】异常: {e}")
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(UITimeout.ANIMATION)
            except Exception:
                pass
