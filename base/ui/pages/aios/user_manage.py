"""用户管理 Page Object（AIOS -> 用户管理）。

页面结构：
    - 搜索区: 租户下拉 + 来源下拉 + 关键字搜索框 + 查询按钮 + 新增按钮
    - 数据表格: 用户账号、用户姓名、登录明细、租户、状态、来源、操作
    - 操作列图标: ri-file-list-2-line(详情) / ri-edit-line(编辑)
      / ri-delete-bin-line(删除) / ri-restart-line(重置密码)
    - 弹窗: 新增用户 / 编辑用户 / 重置密码 / 用户详情 / 删除提示确认

关键约定：
    - 本页面渲染在主文档中（非 iframe），直接使用 ``page`` 定位；
    - 表格行通过用户账号文本定位，操作图标通过 remixicon 类名定位；
    - 新增用户弹窗中的租户/角色为树形下拉，需先展开折叠节点或搜索过滤。
"""
import re
from typing import Dict, Optional

from playwright.sync_api import Locator, Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout

logger = get_logger(__name__)


class UserManagePage(BasePage):
    """用户管理 Page Object。"""

    def __init__(self, page: Page):
        """初始化用户管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("User Manage Page Initialized")

        # ==================== 搜索区 ====================
        self.input_search = page.get_by_role("textbox", name="请输入用户姓名/用户账号关键字")
        self.btn_search = page.get_by_role("button", name="查询")
        self.btn_add = page.get_by_role("button", name="新增")

        # 租户/来源筛选下拉
        self.dropdown_search_tenant = page.locator(
            ".ep-select__wrapper:has-text('请选择租户')"
        ).first
        self.dropdown_search_source = page.locator(
            ".ep-select__wrapper:has-text('请选择来源')"
        ).first

        # ==================== 数据表格 ====================
        self.table_body_rows = page.locator(".ep-table__body-wrapper tbody tr")

        # ==================== 提示消息 ====================
        self.alert = page.locator(".ep-message__content, .el-message__content")

        # ==================== 新增用户弹窗 ====================
        self.dialog_add_user = page.get_by_role("dialog", name=re.compile(re.escape("新增用户"))).first
        self.input_add_useraccount = self.dialog_add_user.get_by_placeholder("请输入用户账号")
        self.input_add_username = self.dialog_add_user.get_by_placeholder("请输入用户姓名")
        self.input_add_password = self.dialog_add_user.get_by_placeholder("请输入密码")
        self.input_add_phone = self.dialog_add_user.get_by_placeholder("请输入手机号码")
        self.input_add_email = self.dialog_add_user.get_by_placeholder("请输入邮箱")
        # 租户选择（combobox 无 placeholder，按名称含"租户"定位唯一 combobox）
        self.combobox_add_tenant = self.dialog_add_user.get_by_role("combobox", name=re.compile(r"租户"))
        # 角色选择（多选 tree 下拉，弹窗内第 2 个 ep-select）
        self.role_select_wrapper = self.dialog_add_user.locator(".ep-select").nth(1).locator(".ep-select__wrapper")
        self.role_combo_input = self.dialog_add_user.get_by_role("combobox").nth(1)

        # ==================== 编辑用户弹窗 ====================
        self.dialog_edit_user = page.get_by_role("dialog", name=re.compile(re.escape("编辑用户"))).first
        self.input_edit_username = self.dialog_edit_user.get_by_role("textbox", name=re.compile(r"用户姓名"))
        self.input_edit_useraccount = self.dialog_edit_user.get_by_role("textbox", name=re.compile(r"用户账号"))

        # ==================== 重置密码弹窗 ====================
        self.dialog_reset_password = page.get_by_role("dialog", name=re.compile(re.escape("重置密码"))).first
        self.input_new_password = self.dialog_reset_password.get_by_placeholder("请输入新密码")
        self.input_confirm_password = self.dialog_reset_password.get_by_placeholder("请输入确认密码")

        # ==================== 用户详情弹窗 ====================
        self.dialog_user_detail = page.get_by_role("dialog", name=re.compile(re.escape("用户详情"))).first
        self.btn_detail_close = self.dialog_user_detail.get_by_role("button", name="关闭", exact=True)

        # ==================== 删除/提示确认弹窗 ====================
        self.dialog_prompt = page.get_by_role("dialog", name=re.compile(r"提示|确认")).first
        self.btn_prompt_delete = self.dialog_prompt.get_by_role("button", name="删除")
        self.btn_prompt_confirm = self.dialog_prompt.get_by_role("button", name="确定")
        self.btn_prompt_cancel = self.dialog_prompt.get_by_role("button", name="取消")
        self.btn_prompt_close = self.dialog_prompt.get_by_role("button", name=re.compile(r"关闭|确定"))

        # ==================== 分页 ====================
        self.pagination = page.locator(".ep-pagination, .el-pagination").first
        self.pagination_total = page.locator(".ep-pagination__total, .el-pagination__total").first

    # ==================== 内部辅助方法 ====================

    def _get_user_row(self, user_account: str) -> Locator:
        """定位指定用户账号对应的表格行。"""
        return self.page.get_by_role("row", name=re.compile(re.escape(user_account)))

    def _click_row_action(self, user_account: str, icon_selector: str) -> None:
        """在指定用户行点击操作图标。

        Args:
            user_account: 用户账号，用于定位行
            icon_selector: 操作图标的 CSS 选择器（remixicon 类名）
        """
        row = self._get_user_row(user_account)
        expect(row).to_be_visible()
        row.locator(icon_selector).first.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def _get_dialog(self, dialog_name: str) -> Locator:
        """按弹窗名称定位 dialog。"""
        return self.page.get_by_role("dialog", name=re.compile(re.escape(dialog_name))).first

    # ==================== 搜索操作 ====================

    def search_user(self, keyword: str) -> None:
        """按关键字搜索用户。"""
        logger.info(f"搜索用户关键字：{keyword}")
        self.input_search.fill(keyword)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def clear_search(self) -> None:
        """清空搜索条件并重新查询。"""
        logger.info("清空搜索条件")
        self.input_search.clear()
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def select_tenant_filter(self, tenant_name: str) -> None:
        """在搜索区选择租户筛选下拉。"""
        if self.dropdown_search_tenant.is_visible():
            self.dropdown_search_tenant.click(force=True)
            self.page.wait_for_timeout(UITimeout.SHORT)
            self.page.get_by_role("tree").get_by_text(tenant_name, exact=True).click()
            self.page.wait_for_timeout(UITimeout.SHORT)

    def select_source_filter(self, source: str) -> None:
        """在搜索区选择来源筛选下拉。"""
        if self.dropdown_search_source.is_visible():
            self.dropdown_search_source.click(force=True)
            self.page.wait_for_timeout(UITimeout.SHORT)
            self.page.get_by_role("listbox").get_by_text(source, exact=True).click()
            self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 新增用户操作 ====================

    def click_add(self) -> None:
        """点击新增用户按钮。"""
        logger.info("点击【新增】用户按钮")
        self.btn_add.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def fill_add_form(self, user_account: str, user_name: str, password: str,
                      phone: str, email: str) -> None:
        """填写新增用户表单（不含租户和角色）。"""
        expect(self.dialog_add_user).to_be_visible()
        self.input_add_useraccount.fill(user_account)
        self.input_add_username.fill(user_name)
        self.input_add_password.fill(password)
        self.input_add_phone.fill(phone)
        self.input_add_email.fill(email)

    def select_tenant(self, tenant_name: str) -> None:
        """在新增用户弹窗中选择租户（支持子租户自动展开折叠节点）。"""
        expect(self.combobox_add_tenant).to_be_visible()
        logger.info(f"打开租户下拉树，目标租户【{tenant_name}】")
        self.combobox_add_tenant.click(force=True)
        self.page.wait_for_timeout(UITimeout.STABILIZE)

        # 租户树渲染在下拉 popper 中（可能在 dialog DOM 外部），全局搜索
        tree = self.page.get_by_role("tree").last
        tenant_node = tree.get_by_text(tenant_name, exact=True).first

        if not self._expand_tenant_tree(tree, tenant_node):
            # 展开后仍不可见，尝试搜索过滤
            self._filter_tenant_tree(tenant_name)
            tree = self.page.get_by_role("tree").last
            tenant_node = tree.get_by_text(tenant_name, exact=True).first

        logger.info(f"点击租户节点【{tenant_name}】")
        expect(tenant_node).to_be_visible(timeout=UITimeout.ELEMENT_VISIBLE_TIMEOUT)
        tenant_node.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def _expand_tenant_tree(self, tree: Locator, tenant_node: Locator) -> bool:
        """逐层展开折叠的树节点，返回目标租户是否可见。"""
        for round_idx in range(3):
            if tenant_node.is_visible():
                logger.info(f"租户已在第 {round_idx} 轮展开后可见")
                return True

            # 展开当前所有折叠的非叶子节点（兼容 ep-/el- 前缀）
            collapsed = tree.locator(
                ".ep-tree-node__expand-icon:not(.expanded):not(.is-leaf), "
                ".el-tree-node__expand-icon:not(.is-expanded):not(.is-leaf)"
            )
            cnt = collapsed.count()
            logger.info(f"发现 {cnt} 个折叠节点")
            if cnt == 0:
                break
            for i in range(cnt):
                try:
                    collapsed.nth(i).click()
                    self.page.wait_for_timeout(UITimeout.SHORT)
                except Exception as e:
                    logger.info(f"展开第 {i} 个节点异常: {e}")
        return tenant_node.is_visible()

    def _filter_tenant_tree(self, tenant_name: str) -> None:
        """通过下拉搜索框过滤租户树节点。"""
        logger.info(f"展开后仍不可见，尝试搜索过滤租户【{tenant_name}】")
        search_input = self.page.locator(
            "input[placeholder*='租户'], input[placeholder*='搜索'], input[placeholder*='过滤']"
        ).last
        if search_input.is_visible():
            search_input.fill(tenant_name)
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(UITimeout.STABILIZE)

    def select_role(self, role_name: str) -> None:
        """在新增用户弹窗中选择角色（多选 tree 下拉，输入过滤后选中）。"""
        expect(self.role_select_wrapper).to_be_visible()
        self.role_select_wrapper.click(force=True)
        self.page.wait_for_timeout(UITimeout.STABILIZE)

        self.role_combo_input.fill(role_name)
        self.page.wait_for_timeout(UITimeout.STABILIZE)

        role_option = self.page.get_by_role("option", name=role_name, exact=True)
        expect(role_option).to_be_visible()
        role_option.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        # 多选下拉不会自动关闭，按 Escape 关闭
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(UITimeout.SHORT)

    def add_user(self, user_account: str, user_name: str, password: str,
                 phone: str, email: str, tenant_name: str, role_name: str) -> None:
        """完整新增用户流程。"""
        self.click_add()
        self.fill_add_form(user_account, user_name, password, phone, email)
        self.select_tenant(tenant_name)
        self.select_role(role_name)
        self.click_confirm("新增用户")

    # ==================== 通用弹窗操作 ====================

    def click_confirm(self, dialog_name: Optional[str] = None) -> None:
        """点击确定按钮（force 避免下拉框 overlay 拦截）。"""
        if dialog_name:
            self._get_dialog(dialog_name).get_by_role("button", name="确定").click(force=True)
        else:
            self.page.get_by_role("button", name="确定").click(force=True)
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def click_cancel(self, dialog_name: Optional[str] = None) -> None:
        """点击取消按钮。"""
        if dialog_name:
            self._get_dialog(dialog_name).get_by_role("button", name="取消").click()
        else:
            self.page.get_by_role("button", name="取消").click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    # ==================== 编辑/删除/重置密码操作 ====================

    def click_detail(self, user_account: str) -> None:
        """点击查看详情图标。"""
        logger.info(f"点击【{user_account}】的查看详情图标")
        self._click_row_action(user_account, ".ri-file-list-2-line")

    def click_edit(self, user_account: str) -> None:
        """点击编辑图标。"""
        logger.info(f"点击【{user_account}】的编辑图标")
        self._click_row_action(user_account, ".ri-edit-line")

    def click_delete(self, user_account: str) -> None:
        """点击删除图标。"""
        logger.info(f"点击【{user_account}】的删除图标")
        self._click_row_action(user_account, ".ri-delete-bin-line")

    def click_reset_password(self, user_account: str) -> None:
        """点击重置密码图标。"""
        logger.info(f"点击【{user_account}】的重置密码图标")
        self._click_row_action(user_account, ".ri-restart-line")

    def edit_user_name(self, user_account: str, new_name: str) -> None:
        """编辑用户姓名并确认。"""
        self.click_edit(user_account)
        expect(self.dialog_edit_user).to_be_visible()
        self.input_edit_username.clear()
        self.input_edit_username.fill(new_name)
        self.click_confirm("编辑用户")

    def edit_user_name_cancel(self, user_account: str, new_name: str) -> None:
        """编辑用户姓名后点击取消。"""
        self.click_edit(user_account)
        expect(self.dialog_edit_user).to_be_visible()
        self.input_edit_username.clear()
        self.input_edit_username.fill(new_name)
        self.click_cancel("编辑用户")

    def edit_user_invalid_name(self, user_account: str, invalid_name: str) -> None:
        """编辑用户姓名为非法值并确认（验证校验提示）。"""
        self.click_edit(user_account)
        expect(self.dialog_edit_user).to_be_visible()
        self.input_edit_username.clear()
        self.input_edit_username.fill(invalid_name)
        self.click_confirm("编辑用户")

    def verify_edit_form_readonly(self, user_account: str) -> Dict[str, bool]:
        """验证编辑弹窗字段的只读状态。

        Returns:
            dict: ``account_disabled`` 账号是否只读，``name_editable`` 姓名是否可编辑
        """
        self.click_edit(user_account)
        expect(self.dialog_edit_user).to_be_visible()
        return {
            "account_disabled": self.input_edit_useraccount.is_disabled(),
            "name_editable": not self.input_edit_username.is_disabled(),
        }

    def reset_password(self, user_account: str, new_password: str) -> None:
        """重置用户密码。"""
        self.click_reset_password(user_account)
        expect(self.dialog_reset_password).to_be_visible()
        self.input_new_password.fill(new_password)
        self.input_confirm_password.fill(new_password)
        self.click_confirm("重置密码")

    def delete_user(self, user_account: str) -> None:
        """删除用户，处理确认弹窗（标准确认或提示无法删除）。"""
        self.click_delete(user_account)
        expect(self.dialog_prompt).to_be_visible()
        if self.btn_prompt_delete.is_visible():
            self.btn_prompt_delete.click()
        elif self.btn_prompt_close.is_visible():
            self.btn_prompt_close.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def delete_user_with_confirm(self, user_account: str, confirm: bool = True) -> None:
        """删除用户并在确认弹窗中点击"删除"/"取消"。"""
        self.click_delete(user_account)
        expect(self.dialog_prompt).to_be_visible()
        if confirm:
            if self.btn_prompt_delete.is_visible():
                self.btn_prompt_delete.click()
            elif self.btn_prompt_confirm.is_visible():
                self.btn_prompt_confirm.click()
        else:
            if self.btn_prompt_cancel.is_visible():
                self.btn_prompt_cancel.click()
            elif self.btn_prompt_close.is_visible():
                self.btn_prompt_close.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def delete_user_close_error(self, user_account: str) -> None:
        """点击删除图标后关闭错误提示弹窗（用户有角色绑定时）。"""
        self.click_delete(user_account)
        expect(self.dialog_prompt).to_be_visible()
        if self.btn_prompt_close.is_visible():
            self.btn_prompt_close.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def get_delete_dialog_text(self, user_account: str) -> str:
        """点击删除图标后获取确认弹窗文本。"""
        self.click_delete(user_account)
        expect(self.dialog_prompt).to_be_visible()
        return self.dialog_prompt.inner_text()

    def close_delete_dialog(self) -> None:
        """关闭当前打开的删除提示弹窗。"""
        if self.dialog_prompt.is_visible():
            btn = self.dialog_prompt.get_by_role("button", name=re.compile(r"关闭|确定|取消"))
            if btn.is_visible():
                btn.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    # ==================== 用户详情操作 ====================

    def view_user_detail(self, user_account: str) -> str:
        """查看用户详情，返回详情弹窗文本内容。"""
        self.click_detail(user_account)
        expect(self.dialog_user_detail).to_be_visible()
        return self.dialog_user_detail.inner_text()

    def get_user_detail_info(self) -> Dict[str, object]:
        """获取用户详情弹窗中的结构化信息。"""
        expect(self.dialog_user_detail).to_be_visible()
        content = self.dialog_user_detail.inner_text()
        return {
            "raw_text": content,
            "has_tenant": "关联的租户" in content,
            "has_role": "关联的角色" in content,
        }

    def close_user_detail(self) -> None:
        """关闭用户详情弹窗。"""
        expect(self.dialog_user_detail).to_be_visible()
        self.btn_detail_close.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 数据清理与分页 ====================

    def cleanup_user(self, user_account: str) -> None:
        """安全删除用户（先搜索再删除，忽略错误）。"""
        logger.info(f"清理用户：{user_account}")
        try:
            # 关闭可能残留的弹窗
            if self.page.get_by_role("dialog").count() > 0:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(UITimeout.ANIMATION)

            self.search_user(user_account)
            row = self._get_user_row(user_account)
            if row.is_visible():
                self.delete_user(user_account)
                logger.info(f"用户【{user_account}】删除处理完成")
            else:
                logger.info(f"用户【{user_account}】不存在，无需清理")
        except Exception as e:
            logger.info(f"清理用户【{user_account}】时出错：{e}")
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(UITimeout.ANIMATION)

    def get_pagination_text(self) -> str:
        """获取分页信息文本。"""
        if self.pagination.is_visible():
            return self.pagination.inner_text()
        return ""

    def get_total_count(self) -> int:
        """获取分页总条数。"""
        if self.pagination_total.is_visible():
            match = re.search(r"(\d+)", self.pagination_total.inner_text())
            if match:
                return int(match.group(1))
        return 0
