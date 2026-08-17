"""消费者应用详情 Page Object（AIOS -> 消费者应用 -> 详情页）。

页面结构：
    - 面包屑: 返回消费者应用列表
    - 应用信息头部: 应用图标 + 所属租户 + 创建时间 + AppSecret（复制/刷新按钮）
    - 已订阅API搜索区: API名称/URL关键字 + 所属产品/产品模块下拉 + 查询按钮
    - 操作按钮: API订阅 / 取消订阅
    - 已订阅API表格: 含全选复选框与分页
    - 弹窗: API订阅 / 取消API订阅 / 刷新密钥二次确认 message-box

关键约定：
    - 本页面渲染在主文档中（非 iframe），直接使用 ``page`` 定位；
    - 表格为 Element Plus 结构，get_by_role("table") 匹配 header + body 两个 table，
      ``nth(1)`` 才是数据行表；
    - API订阅/取消订阅弹窗含审批人下拉、到期日期、申请理由等字段；
    - AppSecret 刷新需二次确认，重置后需 reload 页面获取新值。
"""
import re
from typing import Optional

from playwright.sync_api import Locator, Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout

logger = get_logger(__name__)


class ConsumerAppDetailPage(BasePage):
    """消费者应用详情 Page Object。"""

    def __init__(self, page: Page):
        """初始化消费者应用详情页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Consumer App Detail Page Initialized")

        # ==================== 面包屑与应用信息头部 ====================
        self.link_breadcrumb = page.locator("a[href='/costomerAPP']").first
        self.heading_app_name = page.get_by_alt_text("应用图标")
        self.text_tenant = page.locator("text=所属租户").first
        self.text_create_time = page.locator("text=创建时间").first
        self.text_app_secret = page.locator("text=AppSecret").first
        self.btn_copy_secret = page.locator(".ri-file-copy-line").first
        self.btn_refresh_secret = page.locator(".ri-refresh-line").first

        # ==================== 已订阅API搜索区 ====================
        self.input_api_name = page.get_by_placeholder("API名称关键字")
        self.input_url = page.get_by_placeholder("URL关键字")
        self.dropdown_product = page.locator("div").filter(has_text=re.compile(r"^请选择所属产品$")).nth(1)
        self.dropdown_product_module = page.locator("div").filter(has_text=re.compile(r"^请选择产品模块$")).nth(1)
        self.btn_search_api = page.get_by_role("button", name="查询")

        # ==================== 操作按钮 ====================
        self.btn_subscribe = page.get_by_role("button", name="API订阅")
        self.btn_unsubscribe = page.get_by_role("button", name="取消订阅")

        # ==================== 已订阅API表格 ====================
        self.table_subscribed = page.get_by_role("table").first
        self.checkbox_select_all = self.table_subscribed.locator("label.ep-checkbox").first

        # ==================== 提示消息 ====================
        self.alert = page.locator(".ep-message__content, .el-message__content").first

        # ==================== API订阅弹窗 ====================
        self.dialog_subscribe = page.get_by_role("dialog", name="API订阅")
        self.input_subscribe_search = self.dialog_subscribe.get_by_placeholder("API名称关键字")
        self.btn_subscribe_search = self.dialog_subscribe.get_by_role("button", name="查询")
        self.table_subscribe_header = self.dialog_subscribe.get_by_role("table").nth(0)
        self.table_subscribe_body = self.dialog_subscribe.get_by_role("table").nth(1)
        self.text_subscribe_per_page = self.dialog_subscribe.get_by_text("条/页")
        self.checkbox_subscribe_select_all = self.table_subscribe_header.locator("label.ep-checkbox").first
        self.input_subscribe_expire = self.dialog_subscribe.locator(
            ".ep-form-item:has-text('到期日期') input"
        ).first
        self.dropdown_subscribe_approver = self.dialog_subscribe.locator(
            ".ep-form-item:has-text('审批人') .ep-select__wrapper"
        )
        self.input_subscribe_reason = self.dialog_subscribe.get_by_role("textbox", name="申请理由")
        self.btn_subscribe_confirm = self.dialog_subscribe.get_by_role("button", name="确定")
        self.btn_subscribe_cancel = self.dialog_subscribe.get_by_role("button", name="取消")

        # ==================== 取消API订阅弹窗 ====================
        self.dialog_unsubscribe = page.get_by_role("dialog", name="取消API订阅")
        self.dropdown_unsubscribe_approver = self.dialog_unsubscribe.locator(
            ".ep-form-item:has-text('审批人') .ep-select__wrapper"
        )
        self.input_unsubscribe_reason = self.dialog_unsubscribe.get_by_role("textbox", name="取消理由")
        self.btn_unsubscribe_confirm = self.dialog_unsubscribe.get_by_role("button", name="确定")
        self.btn_unsubscribe_cancel = self.dialog_unsubscribe.get_by_role("button", name="取消")

        # ==================== 刷新密钥二次确认 message-box ====================
        self.msgbox = page.locator(".ep-overlay-message-box").first
        self.btn_msgbox_confirm = self.msgbox.get_by_role("button", name="确定")

        # ==================== 分页 ====================
        self.text_main_per_page = page.get_by_role("main").get_by_text("条/页")
        self.option_100_per_page = page.get_by_role("option", name="100条/页")

    # ==================== 内部辅助方法 ====================

    def _get_subscribed_data_table(self) -> Locator:
        """获取已订阅API数据表格（第 2 个 table，第 1 个是表头）。"""
        return self.page.get_by_role("table").nth(1)

    def _get_subscribed_row_by_name(self, api_name: str) -> Locator:
        """按 API 名称定位已订阅表格行。"""
        return self._get_subscribed_data_table().get_by_role(
            "row", name=re.compile(re.escape(api_name))
        ).first

    def _select_approver(self, dropdown: Locator, approver: str) -> None:
        """点击审批人下拉并选择指定审批人。"""
        dropdown.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.page.get_by_role("option", name=approver, exact=True).click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def _fill_expire_date(self, expire_date: str) -> None:
        """填写订阅到期日期。"""
        self.input_subscribe_expire.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.input_subscribe_expire.fill(expire_date)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def _confirm_msgbox(self) -> None:
        """确认二次弹窗（message-box）。"""
        expect(self.msgbox).to_be_visible()
        self.btn_msgbox_confirm.click()

    # ==================== 已订阅API搜索 ====================

    def search_api(self, api_name: str) -> None:
        """按API名称搜索已订阅API。"""
        logger.info(f"搜索已订阅API名称: {api_name}")
        self.input_api_name.fill(api_name)
        self.btn_search_api.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def select_subscribed_api(self, api_name: str) -> None:
        """在已订阅表格中勾选指定API的复选框。"""
        logger.info(f"勾选已订阅API【{api_name}】")
        row = self._get_subscribed_row_by_name(api_name)
        expect(row).to_be_visible()
        row.get_by_role("checkbox").click()

    # ==================== 操作按钮 ====================

    def click_subscribe(self) -> None:
        """点击API订阅按钮。"""
        logger.info("点击API订阅按钮")
        self.btn_subscribe.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def click_unsubscribe(self) -> None:
        """点击取消订阅按钮。"""
        logger.info("点击取消订阅按钮")
        self.btn_unsubscribe.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    # ==================== API订阅弹窗 ====================

    def select_available_api(self, api_name: str) -> None:
        """在API订阅弹窗的可订阅列表中勾选指定API。"""
        logger.info(f"在订阅弹窗勾选可订阅API【{api_name}】")
        expect(self.dialog_subscribe).to_be_visible()
        row = self.table_subscribe_body.get_by_role(
            "row", name=re.compile(re.escape(api_name))
        ).first
        expect(row).to_be_visible()
        row.get_by_role("checkbox").click()

    def fill_subscribe_form(self, approver: Optional[str] = None, reason: Optional[str] = None) -> None:
        """填写API订阅弹窗表单（审批人、申请理由）。"""
        expect(self.dialog_subscribe).to_be_visible()
        if approver:
            self._select_approver(self.dropdown_subscribe_approver, approver)
        if reason:
            self.input_subscribe_reason.fill(reason)

    def confirm_subscribe(self) -> None:
        """在API订阅弹窗中点击确定。"""
        self.btn_subscribe_confirm.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def cancel_subscribe(self) -> None:
        """在API订阅弹窗中点击取消。"""
        self.btn_subscribe_cancel.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    # ==================== 取消API订阅弹窗 ====================

    def fill_unsubscribe_form(self, approver: Optional[str] = None, reason: Optional[str] = None) -> None:
        """填写取消API订阅弹窗表单（审批人、取消理由）。"""
        expect(self.dialog_unsubscribe).to_be_visible()
        if approver:
            self._select_approver(self.dropdown_unsubscribe_approver, approver)
        if reason:
            self.input_unsubscribe_reason.fill(reason)

    def confirm_unsubscribe(self) -> None:
        """在取消API订阅弹窗中点击确定。"""
        self.btn_unsubscribe_confirm.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def cancel_unsubscribe(self) -> None:
        """在取消API订阅弹窗中点击取消。"""
        self.btn_unsubscribe_cancel.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    # ==================== 导航 ====================

    def navigate_back(self) -> None:
        """点击面包屑返回消费者应用列表页。"""
        logger.info("点击面包屑返回消费者应用列表页")
        self.link_breadcrumb.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    # ==================== 应用密钥操作 ====================

    def get_app_secret(self) -> str:
        """获取 AppSecret 文本内容。"""
        secret_locator = self.text_app_secret.locator("..").locator("span, div").last
        return secret_locator.text_content().strip()

    def click_refresh_secret(self) -> None:
        """点击刷新 AppSecret 按钮。"""
        logger.info("点击刷新AppSecret按钮")
        self.btn_refresh_secret.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def confirm_refresh_secret(self) -> None:
        """在刷新密钥确认弹窗中点击确定。"""
        expect(self.msgbox).to_be_visible()
        self.btn_msgbox_confirm.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def reset_app_secret(self) -> None:
        """重置 AppSecret（点击刷新 + 二次确认），完成后需 reload 获取新密钥。"""
        self.click_refresh_secret()
        self.confirm_refresh_secret()
        logger.info("AppSecret已重置")

    def capture_app_secret(self) -> str:
        """通过响应拦截获取 AppSecret（注册 listener 后 reload 触发接口请求）。

        Returns:
            str: 捕获到的 appSecret 字符串
        """
        captured = [None]

        def _capture(response) -> None:
            if "consumer/app/detail" in response.url and response.status == 200:
                try:
                    body = response.json()
                    secret = body.get("data", {}).get("appSecret")
                    if secret:
                        captured[0] = secret
                except Exception:
                    pass

        self.page.on("response", _capture)
        self.page.reload()
        self.page.wait_for_load_state(state="load")
        self.page.wait_for_timeout(UITimeout.MEDIUM)
        self.page.remove_listener("response", _capture)
        assert captured[0], "通过接口响应获取AppSecret失败"
        logger.info(f"获取AppSecret成功: {captured[0]}")
        return captured[0]

    # ==================== 订阅完整流程 ====================

    def do_subscribe_api(self, api_keyword: str, approver: str, reason: str,
                         expire_date: str = "2027-12-31") -> bool:
        """API订阅完整流程（全选API）。

        Returns:
            bool: True 表示提交了订阅申请，False 表示无可订阅API
        """
        self.click_subscribe()
        expect(self.dialog_subscribe).to_be_visible()

        self.input_subscribe_search.fill(api_keyword)
        self.btn_subscribe_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

        if not self._has_available_api(api_keyword):
            self.cancel_subscribe()
            logger.info(f"无可订阅API【{api_keyword}】")
            return False

        # 切换 100 条/页确保全选覆盖所有 API
        self.text_subscribe_per_page.click()
        self.option_100_per_page.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

        self.checkbox_subscribe_select_all.check()
        self._fill_expire_date(expire_date)
        self._select_approver(self.dropdown_subscribe_approver, approver)
        self.input_subscribe_reason.fill(reason)

        self.btn_subscribe_confirm.click()
        self.page.wait_for_timeout(UITimeout.QUERY)
        self._confirm_msgbox()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

        expect(self.dialog_subscribe).to_be_hidden(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        logger.info(f"API订阅申请提交成功: {api_keyword}")
        return True

    def do_subscribe_api_single(self, api_keyword: str, approver: str,
                                reason: Optional[str] = None,
                                expire_date: str = "2027-12-31") -> bool:
        """API订阅流程（单选API，理由可选）。

        Returns:
            bool: True 表示提交了订阅申请，False 表示无可订阅API
        """
        self.click_subscribe()
        expect(self.dialog_subscribe).to_be_visible()

        self.input_subscribe_search.fill(api_keyword)
        self.btn_subscribe_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

        if not self._has_available_api(api_keyword):
            self.cancel_subscribe()
            logger.info(f"无可订阅API【{api_keyword}】")
            return False

        # 勾选单个 API
        row = self.table_subscribe_body.get_by_role("row").filter(
            has=self.page.get_by_role("cell", name=api_keyword, exact=True)
        ).first
        checkbox = row.locator("label.ep-checkbox").nth(0)
        expect(checkbox).to_be_visible()
        checkbox.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

        self._fill_expire_date(expire_date)
        self._select_approver(self.dropdown_subscribe_approver, approver)
        if reason:
            self.input_subscribe_reason.fill(reason)

        self.btn_subscribe_confirm.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self._confirm_msgbox()

        expect(self.dialog_subscribe).to_be_hidden(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        logger.info(f"API订阅申请提交成功（单选）: {api_keyword}")
        return True

    def _has_available_api(self, api_keyword: str) -> bool:
        """检查订阅弹窗中是否有可订阅的 API。"""
        rows = self.table_subscribe_body.get_by_role("row").filter(
            has=self.page.get_by_role("cell", name=api_keyword, exact=True)
        )
        return rows.count() > 0

    # ==================== 取消订阅完整流程 ====================

    def do_unsubscribe_selected(self, approver: str, reason: Optional[str] = None) -> None:
        """取消订阅已勾选的 API（前提：已勾选复选框）。"""
        self.click_unsubscribe()
        expect(self.dialog_unsubscribe).to_be_visible()

        self._select_approver(self.dropdown_unsubscribe_approver, approver)
        if reason:
            self.input_unsubscribe_reason.fill(reason)

        self.btn_unsubscribe_confirm.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

        try:
            self._confirm_msgbox()
            self.page.wait_for_timeout(UITimeout.STABILIZE)
        except Exception:
            self.page.wait_for_timeout(UITimeout.STABILIZE)

        expect(self.dialog_unsubscribe).to_be_hidden(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        logger.info("取消订阅已勾选API完成")

    def do_unsubscribe_all(self, approver: str, reason: str = "自动化测试清理-取消订阅") -> bool:
        """取消订阅全部 API（全选后取消订阅）。

        Returns:
            bool: True 表示执行了取消订阅，False 表示无已订阅API
        """
        if not self.checkbox_select_all.is_visible():
            logger.info("无已订阅API，无需取消订阅")
            return False

        # 切换 100 条/页确保全选覆盖所有 API
        self.text_main_per_page.click()
        self.option_100_per_page.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

        self.checkbox_select_all.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.do_unsubscribe_selected(approver, reason)
        logger.info("取消订阅全部API完成")
        return True

    # ==================== 统计 ====================

    def get_subscribed_api_count(self) -> int:
        """获取已订阅API表格数据行数。"""
        return self._get_subscribed_data_table().get_by_role("row").count()
