"""角色管理 Page Object（AIOS -> 角色管理）。

页面结构：
    - 搜索区: 角色名称关键字搜索框 + 查询按钮 + 新增按钮 + 展开/收起按钮
    - 树形表格: 角色层级列表（角色名称、编码、来源等），支持展开/收起
    - 操作列图标: ri-account-box-line(角色赋权) / ri-contacts-line(绑定用户)
      / ri-more-line(更多: 编辑/删除角色) / ri-add-line(新增下级角色)

关键约定：
    - 本页面渲染在主文档中（非 iframe），直接使用 ``page`` 定位；
    - 角色列表是树形表格，子角色通过展开箭头或"展开/收起"按钮展示；
    - 编辑/删除角色在"更多"下拉菜单中，需先点 ri-more-line 再选菜单项；
    - 角色赋权弹窗内含权限树，勾选前需先展开所有折叠节点；
    - 绑定用户弹窗含左右两个表格：左=可绑定，右=已绑定。
"""
import re
from typing import List, Optional

from playwright.sync_api import Locator, Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout

logger = get_logger(__name__)


class RoleManagePage(BasePage):
    """角色管理 Page Object。"""

    def __init__(self, page: Page):
        """初始化角色管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Role Manage Page Initialized")

        # ==================== 搜索区 ====================
        self.filter_role = page.get_by_placeholder("角色名称关键字")
        self.btn_search = page.get_by_role("button", name="查询")
        self.btn_add = page.locator("button").filter(has_text=re.compile(r"新增")).first
        self.btn_expand_collapse = page.get_by_label("角色赋权").get_by_role("button", name="展开/收起")
        self.row_platform_admin = page.get_by_role("row", name=re.compile(r"平台管理员")).first
        # 提示消息（用 last 获取最新 toast）
        self.alert = page.locator(".ep-message__content, .el-message__content").last

        # ==================== 数据表格 ====================
        self.table_body_rows = page.locator(".ep-table__body-wrapper tbody tr")
        self.table_body_col_first = page.locator(".ep-table__body-wrapper tbody tr td:nth-child(1)")

        # ==================== 角色赋权弹窗 ====================
        self.dialog_authorize = page.get_by_role("dialog", name="角色赋权")
        self.tree_authorize = self.dialog_authorize.locator('[role="tree"]')
        self.btn_authorize_expand = self.dialog_authorize.locator("button").filter(has_text="展开/收起").first
        self.btn_authorize_close = self.dialog_authorize.locator("button[aria-label='关闭此对话框']").first

        # ==================== 绑定用户弹窗 ====================
        self.dialog_bind_user = page.get_by_role("dialog", name=re.compile(re.escape("绑定用户"))).first
        self.btn_bind_close = self.dialog_bind_user.get_by_role("button", name="关闭").first

        # ==================== 新增角色弹窗 ====================
        self.dialog_add_role = page.get_by_role("dialog", name=re.compile(re.escape("新增角色"))).first
        self.input_add_role_name = self.dialog_add_role.get_by_placeholder("请输入角色名称")
        self.input_add_role_code = self.dialog_add_role.get_by_placeholder("请输入角色编码")

        # ==================== 编辑角色弹窗 ====================
        self.dialog_edit_role = page.get_by_role("dialog", name=re.compile(re.escape("编辑角色"))).first
        self.input_edit_role_name = self.dialog_edit_role.get_by_placeholder("请输入角色名称")

        # ==================== 新增下级角色弹窗 ====================
        self.dialog_sub_role = page.get_by_role("dialog", name=re.compile(re.escape("新增下级角色"))).first
        self.input_sub_role_name = self.dialog_sub_role.get_by_placeholder("请输入角色名称")
        self.input_sub_role_code = self.dialog_sub_role.get_by_placeholder("请输入角色编码")

        # ==================== 删除/提示确认弹窗 ====================
        self.dialog_prompt = page.get_by_role("dialog", name=re.compile(r"提示|确认")).first

        # ==================== 列表与空数据 ====================
        self.btn_list_expand_collapse = page.locator("button").filter(has_text=re.compile(r"展开/收起")).first
        self.text_empty = page.locator(".ep-table__empty-text, .el-table__empty-text, .ep-table__empty-block").first

    # ==================== 内部辅助方法 ====================

    def _get_role_row(self, role_name: str) -> Locator:
        """定位指定角色名称对应的表格行。"""
        return self.page.get_by_role("row", name=re.compile(re.escape(role_name))).first

    def _click_row_action(self, role_name: str, icon_selector: str) -> None:
        """在指定角色行点击操作图标。

        Args:
            role_name: 角色名称，用于定位行
            icon_selector: 操作图标的 CSS 选择器（remixicon 类名）
        """
        row = self._get_role_row(role_name)
        expect(row).to_be_visible()
        row.locator(icon_selector).first.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def _get_dialog(self, dialog_name: str) -> Locator:
        """按弹窗名称定位 dialog。"""
        return self.page.get_by_role("dialog", name=re.compile(re.escape(dialog_name))).first

    def _dismiss_message_boxes(self) -> None:
        """通过 JS 关闭页面上可能残留的 message-box 弹窗。"""
        try:
            self.page.evaluate(
                "() => { document.querySelectorAll('.ep-overlay-message-box button').forEach(btn => btn.click()); }"
            )
            self.page.wait_for_timeout(UITimeout.ANIMATION)
        except Exception:
            pass

    # ==================== 搜索与新增 ====================

    def search_role(self, keyword: str) -> None:
        """按关键字搜索角色。"""
        logger.info(f"搜索角色关键字：{keyword}")
        self.filter_role.fill(keyword)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def click_add(self) -> None:
        """点击新增角色按钮。"""
        logger.info("点击【新增】角色按钮")
        self.btn_add.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def clear_filter(self) -> None:
        """清空查询条件并重新查询。"""
        if self.filter_role.input_value() != "":
            self.filter_role.clear()
            self.btn_search.click()
            self.page.wait_for_timeout(UITimeout.STABILIZE)

    # ==================== 行操作图标 ====================

    def click_bind_user(self, role_name: str) -> None:
        """点击绑定用户图标（ri-contacts-line）。"""
        logger.info(f"点击【{role_name}】的绑定用户图标")
        self._click_row_action(role_name, ".ri-contacts-line")

    def click_authorize(self, role_name: str) -> None:
        """点击角色赋权图标（ri-account-box-line）。"""
        logger.info(f"点击【{role_name}】的角色赋权图标")
        self._click_row_action(role_name, ".ri-account-box-line")

    def _click_more_menu_item(self, role_name: str, menu_item: str) -> None:
        """点击角色行"更多"下拉菜单中的指定菜单项。"""
        row = self._get_role_row(role_name)
        expect(row).to_be_visible()
        row.locator(".ri-more-line").click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.page.locator(".ep-dropdown-menu:visible, .el-dropdown-menu:visible").get_by_role(
            "menuitem", name=menu_item
        ).click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_edit(self, role_name: str) -> None:
        """点击角色行"更多"菜单中的"编辑角色"。"""
        logger.info(f"点击【{role_name}】的编辑图标")
        self._click_more_menu_item(role_name, "编辑角色")

    def click_delete(self, role_name: str) -> None:
        """点击角色行"更多"菜单中的"删除角色"。"""
        logger.info(f"点击【{role_name}】的删除图标")
        self._click_more_menu_item(role_name, "删除角色")

    def click_add_sub_role(self, role_name: str) -> None:
        """点击角色行的"新增下级角色"图标。"""
        logger.info(f"点击【{role_name}】的新增下级角色图标")
        row = self._get_role_row(role_name)
        expect(row).to_be_visible()
        add_img = row.locator("img.table-action-icon")
        expect(add_img).to_be_visible()
        add_img.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_tree_expand_icon(self, role_name: str) -> None:
        """点击树形表格行的展开/收起箭头。"""
        logger.info(f"点击【{role_name}】的展开/收起箭头")
        row = self._get_role_row(role_name)
        expect(row).to_be_visible()
        row.locator(".ep-table__expand-icon, .el-table__expand-icon").first.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_expand_collapse_all(self) -> None:
        """点击角色列表的"展开/收起"按钮（全局展开/收起所有树节点）。"""
        logger.info("点击角色列表展开/收起按钮")
        expect(self.btn_list_expand_collapse).to_be_visible()
        self.btn_list_expand_collapse.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    # ==================== 新增/编辑/删除角色 ====================

    def fill_add_form(self, role_name: str, role_code: str) -> None:
        """填写新增角色表单。"""
        expect(self.dialog_add_role).to_be_visible()
        self.input_add_role_name.fill(role_name)
        self.input_add_role_code.fill(role_code)

    def fill_edit_form(self, new_name: str) -> None:
        """填写编辑角色表单。"""
        expect(self.dialog_edit_role).to_be_visible()
        self.input_edit_role_name.clear()
        self.input_edit_role_name.fill(new_name)

    def click_confirm(self, dialog_name: Optional[str] = None) -> None:
        """点击确定按钮（force 避免下拉框 overlay 拦截）。"""
        if dialog_name:
            self._get_dialog(dialog_name).get_by_role("button", name="确定").click(force=True)
        else:
            self.page.get_by_role("button", name="确定").click(force=True)
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_cancel(self, dialog_name: Optional[str] = None) -> None:
        """点击取消按钮。"""
        if dialog_name:
            self._get_dialog(dialog_name).get_by_role("button", name="取消").click()
        else:
            self.page.get_by_role("button", name="取消").click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def add_role(self, role_name: str, role_code: str) -> None:
        """完整流程：新增角色。"""
        self.click_add()
        self.fill_add_form(role_name, role_code)
        self.click_confirm("新增角色")

    def edit_role(self, role_name: str, new_name: str) -> None:
        """完整流程：编辑角色名称。"""
        self.click_edit(role_name)
        self.fill_edit_form(new_name)
        self.click_confirm("编辑角色")

    def delete_role(self, role_name: str) -> None:
        """删除角色，处理确认弹窗（标准确认或提示无法删除）。"""
        self.click_delete(role_name)
        expect(self.dialog_prompt).to_be_visible()
        delete_btn = self.dialog_prompt.get_by_role("button", name="删除")
        if delete_btn.is_visible():
            delete_btn.click(force=True)
        else:
            # 角色有绑定用户等情况无法删除，关闭提示弹窗
            close_btn = self.dialog_prompt.get_by_role("button", name=re.compile(r"确定|关闭|确认"))
            if close_btn.is_visible():
                close_btn.click(force=True)
        self.page.wait_for_timeout(UITimeout.SHORT)

    def delete_role_close(self, role_name: str) -> None:
        """点击删除图标后关闭提示弹窗（角色有绑定用户时）。"""
        self.click_delete(role_name)
        expect(self.dialog_prompt).to_be_visible()
        close_btn = self.dialog_prompt.get_by_role("button", name=re.compile(r"关闭|确定"))
        if close_btn.is_visible():
            close_btn.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def add_sub_role(self, parent_role_name: str, sub_role_name: str, sub_role_code: str) -> None:
        """完整流程：在指定角色下新增子角色。"""
        logger.info(f"在【{parent_role_name}】下新增子角色【{sub_role_name}】")
        parent_row = self._get_role_row(parent_role_name)
        expect(parent_row).to_be_visible()

        self.click_add_sub_role(parent_role_name)
        expect(self.dialog_sub_role).to_be_visible()
        self.input_sub_role_name.fill(sub_role_name)
        self.input_sub_role_code.fill(sub_role_code)
        self.click_confirm("新增下级角色")

        # 最终验证：弹窗仍在则刷新页面
        try:
            if self.dialog_sub_role.is_visible():
                logger.info("新增下级角色弹窗仍未关闭，刷新页面")
                self.page.reload()
                self.page.wait_for_load_state(state="load")
                self.page.wait_for_timeout(UITimeout.SHORT)
        except Exception:
            pass
        logger.info(f"子角色【{sub_role_name}】创建流程完成")

    # ==================== 数据清理 ====================

    def cleanup_role(self, role_name: str) -> None:
        """安全删除角色：清空查询条件后删除，忽略错误。"""
        self.clear_filter()
        row = self._get_role_row(role_name)
        if row.is_visible():
            self.delete_role(role_name)
        self._dismiss_message_boxes()

    def cleanup_role_with_unbind(self, role_name: str, tenant_name: str, user_accounts: List[str]) -> None:
        """先解绑所有用户，再删除角色。"""
        logger.info(f"清理角色（含解绑）：{role_name}")
        expect(self.row_platform_admin).to_be_visible()
        self.clear_filter()

        row = self._get_role_row(role_name)
        if row.is_visible():
            for user_account in user_accounts:
                try:
                    self.unbind_user(role_name, tenant_name, user_account)
                    logger.info(f"已解绑用户【{user_account}】")
                except Exception as e:
                    logger.info(f"解绑用户【{user_account}】异常: {e}")
            row = self._get_role_row(role_name)
            if row.is_visible():
                self.delete_role(role_name)
        self._dismiss_message_boxes()

    # ==================== 绑定/解绑用户 ====================

    def bind_user(self, role_name: str, tenant_name: str, user_account: str) -> None:
        """绑定用户到角色（含租户选择、已绑定检查、勾选绑定）。"""
        self.click_bind_user(role_name)
        dialog = self.dialog_bind_user
        expect(dialog).to_be_visible()

        self._dismiss_notice_in_dialog(dialog)
        self.select_tenant_in_bind(tenant_name)

        # 检查用户是否已在已绑定列表中
        try:
            self._search_and_check_bound(dialog, user_account)
            logger.info(f"用户【{user_account}】已在已绑定列表中，无需重复绑定")
            dialog.get_by_role("button", name="关闭", exact=True).click()
            self.page.wait_for_timeout(UITimeout.SHORT)
            return
        except Exception:
            pass

        # 搜索可绑定用户并勾选
        search_input = dialog.get_by_placeholder(re.compile(r"用户.*关键字")).first
        search_input.fill(user_account)
        dialog.get_by_role("button", name="查询").nth(0).click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

        self.select_bindable_user(user_account)
        self.click_bind()
        dialog.get_by_role("button", name="关闭", exact=True).click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def unbind_user(self, role_name: str, tenant_name: str, user_account: str) -> None:
        """从角色解绑用户。"""
        self.click_bind_user(role_name)
        dialog = self.dialog_bind_user
        expect(dialog).to_be_visible()

        self.select_tenant_in_bind(tenant_name)
        self.search_bound_users(user_account)

        # 勾选已绑定用户并解绑
        self.select_bound_user_checkbox(user_account)
        self.click_unbind()

        # 关闭弹窗（使用 header 关闭按钮，绕过 overlay 拦截）
        try:
            dialog.locator("button.ep-dialog__headerbtn").first.evaluate("el => el.click()")
        except Exception:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(UITimeout.SHORT)
        self._ensure_dialog_closed()

    def _dismiss_notice_in_dialog(self, dialog: Locator) -> None:
        """关闭弹窗内可能出现的通知横幅。"""
        try:
            notice_close = dialog.locator(
                ".ep-alert__close, .el-alert__close, .ep-notification__close"
            ).first
            if notice_close.is_visible():
                notice_close.click()
                self.page.wait_for_timeout(UITimeout.ANIMATION)
        except Exception:
            pass

    def _ensure_dialog_closed(self) -> None:
        """确保绑定用户弹窗已关闭（最多按 3 次 Escape）。"""
        for _ in range(3):
            try:
                dlg = self.page.get_by_role("dialog", name=re.compile(r"绑定用户"))
                if dlg.count() > 0 and dlg.first.is_visible():
                    self.page.keyboard.press("Escape")
                    self.page.wait_for_timeout(UITimeout.ANIMATION)
                else:
                    break
            except Exception:
                break

    def _search_and_check_bound(self, dialog: Locator, user_account: str) -> None:
        """搜索已绑定用户（右表格），检查用户是否已绑定。

        Raises:
            Exception: 用户不在已绑定列表中
        """
        search_inputs = dialog.get_by_placeholder(re.compile(r"用户.*关键字"))
        if search_inputs.count() < 2:
            raise Exception("未找到已绑定用户搜索框")
        search_inputs.nth(1).fill(user_account)
        dialog.get_by_role("button", name="查询").nth(1).click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

        tables = dialog.get_by_role("table")
        if tables.count() >= 4:
            right_table = tables.nth(3)
            row = right_table.get_by_role("row", name=re.compile(re.escape(user_account)))
            if row.is_visible():
                return
        raise Exception(f"用户【{user_account}】不在已绑定列表中")

    def select_tenant_in_bind(self, tenant_name: str) -> None:
        """在绑定用户弹窗中选择租户。"""
        dialog = self.dialog_bind_user
        expect(dialog).to_be_visible()
        tenant_input = dialog.get_by_role("combobox")
        expect(tenant_input).to_be_visible()
        tenant_input.click(force=True)
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.page.get_by_role("tree").get_by_text(tenant_name, exact=True).click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def search_bindable_users(self, keyword: str) -> None:
        """搜索可绑定用户（左表格）。"""
        dialog = self.dialog_bind_user
        expect(dialog).to_be_visible()
        search_input = dialog.get_by_placeholder(re.compile(r"用户.*关键字")).first
        search_input.fill(keyword)
        dialog.get_by_role("button", name="查询").nth(0).click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def search_bound_users(self, keyword: str) -> None:
        """搜索已绑定用户（右表格）。"""
        dialog = self.dialog_bind_user
        expect(dialog).to_be_visible()
        search_input = dialog.get_by_placeholder(re.compile(r"用户.*关键字")).nth(1)
        search_input.fill(keyword)
        dialog.get_by_role("button", name="查询").nth(1).click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def select_bindable_user(self, user_account: str) -> None:
        """在可绑定用户表格中勾选指定用户（Table[1]）。"""
        dialog = self.dialog_bind_user
        left_table = dialog.get_by_role("table").nth(1)
        row = left_table.get_by_role("row", name=re.compile(re.escape(user_account)))
        expect(row).to_be_visible()
        self._click_row_checkbox(row)

    def select_all_bindable_users(self) -> None:
        """在可绑定用户表格中全选。"""
        dialog = self.dialog_bind_user
        left_table = dialog.get_by_role("table").nth(1)
        select_all = left_table.get_by_role("checkbox", name="选择所有行")
        if select_all.is_visible():
            self._click_checkbox(select_all)

    def select_bound_user_checkbox(self, user_account: str) -> None:
        """在已绑定用户表格中勾选指定用户（Table[3]）。"""
        dialog = self.dialog_bind_user
        right_table = dialog.get_by_role("table").nth(3)
        row = right_table.get_by_role("row", name=re.compile(re.escape(user_account)))
        if row.is_visible():
            self._click_row_checkbox(row)

    def select_all_bound_users(self) -> None:
        """在已绑定用户表格中全选。"""
        dialog = self.dialog_bind_user
        right_table = dialog.get_by_role("table").nth(3)
        select_all = right_table.get_by_role("checkbox", name="选择所有行")
        if select_all.is_visible():
            self._click_checkbox(select_all)

    def _click_row_checkbox(self, row: Locator) -> None:
        """勾选指定行的 checkbox（force 失败则 JS 点击）。"""
        checkbox = row.get_by_role("checkbox", name="选择当前行")
        self._click_checkbox(checkbox)

    def _click_checkbox(self, checkbox: Locator) -> None:
        """点击 checkbox，force 失败则 JS 点击（处理 viewport 外元素）。"""
        try:
            checkbox.click(force=True)
        except Exception:
            checkbox.evaluate("el => el.click()")
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def click_bind(self) -> None:
        """点击绑定按钮。"""
        self.dialog_bind_user.get_by_role("button", name="绑定").click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_unbind(self) -> None:
        """点击解绑按钮。"""
        self.dialog_bind_user.get_by_role("button", name="解绑").click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def close_bind_dialog(self) -> None:
        """关闭绑定用户弹窗（先处理遮挡的 message-box，再点 header 关闭按钮）。"""
        try:
            msgbox = self.page.locator(".ep-overlay-message-box:visible").first
            if msgbox.is_visible():
                msgbox.locator("button").first.click(force=True)
                self.page.wait_for_timeout(UITimeout.ANIMATION)
        except Exception:
            pass

        self.page.evaluate(
            "() => { const btn = document.querySelector('.ep-dialog__headerbtn'); if (btn) btn.click(); }"
        )
        self.page.wait_for_timeout(UITimeout.SHORT)

        if self.dialog_bind_user.is_visible():
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 角色赋权 ====================

    def _get_authorize_dialog(self) -> Locator:
        """获取角色赋权弹窗。"""
        return self.page.get_by_role("dialog", name="角色赋权")

    def search_role_and_open_authorize(self, role_name: str) -> None:
        """搜索角色并打开角色赋权弹窗。"""
        logger.info(f"搜索角色【{role_name}】并打开角色赋权")
        row = self._get_role_row(role_name)
        expect(row).to_be_visible()
        row.locator("i.ri-account-box-line").first.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def _expand_all_tree_nodes(self) -> None:
        """点击"展开/收起"按钮展开所有树节点（最多重试 3 次）。"""
        expect(self.page.get_by_role("treeitem").locator("div").first).to_be_visible()
        for _ in range(3):
            collapsed = self.tree_authorize.locator(
                ".ep-tree-node__expand-icon:not(.expanded):not(.is-leaf)"
            )
            if collapsed.count() == 0:
                break
            self.btn_authorize_expand.click()
            self.page.wait_for_timeout(UITimeout.SHORT)

    def check_menu_with_children(self, menu_name: str) -> None:
        """勾选指定菜单及其所有子权限。"""
        logger.info(f"勾选菜单及所有子权限：【{menu_name}】")
        self._expand_all_tree_nodes()

        parent_node = self.tree_authorize.locator('[role="treeitem"]').filter(
            has_text=re.compile(rf"^{re.escape(menu_name)}")
        ).first
        expect(parent_node).to_be_visible()

        self._check_node_icon(parent_node, f"父节点【{menu_name}】")

        child_nodes = parent_node.locator('[role="treeitem"]')
        child_count = child_nodes.count()
        logger.info(f"【{menu_name}】下共有 {child_count} 个子节点")
        for i in range(child_count):
            child = child_nodes.nth(i)
            self._check_node_icon(child, f"子节点【{child.inner_text()}】")

    def check_menu_permission(self, menu_name: str) -> None:
        """在菜单赋权树中勾选指定菜单/按钮。"""
        logger.info(f"勾选菜单/按钮权限：【{menu_name}】")
        self._expand_all_tree_nodes()
        node = self._locate_tree_node(menu_name)
        expect(node).to_be_visible()
        self._check_node_icon(node, f"菜单【{menu_name}】")

    def uncheck_child_permission(self, parent_name: str, child_name: str) -> None:
        """在指定父菜单下取消勾选子权限。"""
        logger.info(f"取消勾选【{parent_name}】下的子权限【{child_name}】")
        self._expand_all_tree_nodes()

        parent_node = self.tree_authorize.locator('[role="treeitem"]').filter(
            has_text=re.compile(rf"^{re.escape(parent_name)}")
        ).first
        expect(parent_node).to_be_visible()

        child_nodes = parent_node.locator('[role="treeitem"]')
        for i in range(child_nodes.count()):
            child = child_nodes.nth(i)
            child_content = child.locator(":scope > .ep-tree-node__content").first
            if child_content.inner_text().strip() == child_name:
                child_icon = child_content.locator(".ri-checkbox-circle-fill.active").first
                child_icon.click()
                self.page.wait_for_timeout(UITimeout.ANIMATION)
                logger.info(f"已取消勾选【{parent_name}】下的子权限【{child_name}】")
                return
        logger.info(f"未在【{parent_name}】下找到子权限【{child_name}】")

    def uncheck_menu_permission(self, menu_name: str) -> None:
        """在菜单赋权树中取消勾选指定菜单/按钮。"""
        logger.info(f"取消勾选菜单/按钮权限：【{menu_name}】")
        self._expand_all_tree_nodes()
        node = self._locate_tree_node(menu_name)
        expect(node).to_be_visible()
        icon = node.locator(":scope > .ep-tree-node__content .ri-checkbox-circle-fill.active").first
        if icon.is_visible():
            icon.click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def verify_menu_permission_unchecked(self, menu_name: str) -> None:
        """验证菜单/按钮权限已取消勾选。"""
        logger.info(f"验证【{menu_name}】权限未勾选")
        self._expand_all_tree_nodes()
        node = self._locate_tree_node(menu_name)
        icon = node.locator(":scope > .ep-tree-node__content .ri-checkbox-circle-fill.active").first
        expect(icon).not_to_be_visible()

    def verify_menu_permission_checked(self, menu_name: str) -> None:
        """验证菜单/按钮权限已勾选。"""
        logger.info(f"验证【{menu_name}】权限已勾选")
        self._expand_all_tree_nodes()
        node = self._locate_tree_node(menu_name)
        icon = node.locator(":scope > .ep-tree-node__content .ri-checkbox-circle-fill.active").first
        expect(icon).to_be_visible()

    def verify_menus_checked(self, menus: List[str]) -> None:
        """批量验证多个菜单权限已勾选（仅展开一次树）。"""
        logger.info(f"批量验证 {len(menus)} 个菜单权限已勾选")
        self._expand_all_tree_nodes()
        for menu in menus:
            node = self._locate_tree_node(menu)
            icon = node.locator(":scope > .ep-tree-node__content .ri-checkbox-circle-fill.active").first
            expect(icon).to_be_visible()
        logger.info(f"批量验证 {len(menus)} 个菜单权限已勾选通过")

    def verify_menus_unchecked(self, menus: List[str]) -> None:
        """批量验证多个菜单权限未勾选（仅展开一次树）。"""
        logger.info(f"批量验证 {len(menus)} 个菜单权限未勾选")
        self._expand_all_tree_nodes()
        for menu in menus:
            node = self._locate_tree_node(menu)
            icon = node.locator(":scope > .ep-tree-node__content .ri-checkbox-circle-fill.active").first
            expect(icon).not_to_be_visible()
        logger.info(f"批量验证 {len(menus)} 个菜单权限未勾选通过")

    def _locate_tree_node(self, menu_name: str) -> Locator:
        """在赋权树中定位指定菜单节点（按名称前缀精确匹配）。"""
        return self.tree_authorize.locator('[role="treeitem"]').filter(
            has_text=re.compile(rf"^{re.escape(menu_name)}")
        ).first

    def _check_node_icon(self, node: Locator, description: str) -> None:
        """勾选树节点的 checkbox 图标（已勾选则跳过）。"""
        icon = node.locator(":scope > .ep-tree-node__content .ri-checkbox-circle-fill").first
        icon_class = icon.get_attribute("class") or ""
        if "active" not in icon_class:
            icon.click()
            self.page.wait_for_timeout(UITimeout.ANIMATION)
            logger.info(f"已勾选{description}")
        else:
            logger.info(f"{description}已是勾选状态")

    def switch_authorize_view(self, view_name: str) -> None:
        """在角色赋权弹窗中切换视图 tab（管理视图/用户视图）。"""
        logger.info(f"角色赋权弹窗切换到【{view_name}】")
        self.dialog_authorize.get_by_role("tab", name=view_name).click(force=True)
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def verify_menu_in_authorize_tree(self, menu_name: str, should_visible: bool = True) -> None:
        """验证菜单项在角色赋权树中是否可见。"""
        self._expand_all_tree_nodes()
        node = self._locate_tree_node(menu_name)
        if should_visible:
            logger.info(f"验证角色赋权树中展示【{menu_name}】")
            expect(node).to_be_visible()
        else:
            logger.info(f"验证角色赋权树中不展示【{menu_name}】")
            expect(node).not_to_be_visible()

    def close_authorize_dialog(self) -> None:
        """关闭角色赋权弹窗。"""
        logger.info("关闭角色赋权弹窗")
        self.btn_authorize_close.click(force=True)
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def save_permission(self) -> None:
        """关闭角色赋权弹窗以触发保存（弹窗关闭时自动 POST 保存）。"""
        logger.info("关闭角色赋权弹窗以保存赋权")
        self.btn_authorize_close.click(force=True)
        self.page.wait_for_timeout(UITimeout.STABILIZE)
        logger.info("已关闭角色赋权弹窗，赋权已保存")

    # ==================== 验证 ====================

    def verify_role_visible(self, role_name: str) -> None:
        """验证角色在列表中可见。"""
        expect(self._get_role_row(role_name)).to_be_visible()

    def verify_role_not_visible(self, role_name: str) -> None:
        """验证角色在列表中不可见。"""
        expect(self._get_role_row(role_name)).not_to_be_visible()

    def verify_empty_result(self) -> None:
        """验证搜索结果为空（表格无数据）。"""
        expect(self.text_empty).to_be_visible()
