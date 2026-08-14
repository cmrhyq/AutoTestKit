"""租户管理 Page Object（AIOS -> 租户管理）。

页面结构：
    - 搜索区: 租户名称关键字搜索框 + 租户类型下拉 + 查询按钮 + 用户关联按钮
    - 树形表格: 租户名称、租户编码、租户类型、磐基归属部门、租户层级、操作
    - 操作列: ri-user-settings-line(用户关联) / ri-more-line(更多: 编辑/删除/集群管理/新增下级/新增同级)
      / img.table-action-icon(新增下级/同级，SVG 图标)

关键约定：
    - 本页面渲染在主文档中（非 iframe），直接使用 ``page`` 定位；
    - 租户列表是树形表格，行内部分操作隐藏在"更多"下拉菜单中；
    - 新增下级/同级租户图标为 ``img.table-action-icon``（last=下级, first=同级）；
    - 用户关联弹窗含左右两个表格：左=可关联用户，右=已关联用户。
"""
import re
from typing import List, Optional

from playwright.sync_api import Locator, Page, expect

from base.ui.pages.base import BasePage
from core import get_logger
from core.constants import UITimeout

logger = get_logger(__name__)


class TenantManagePage(BasePage):
    """租户管理 Page Object。"""

    def __init__(self, page: Page):
        """初始化租户管理页元素定位器。

        Args:
            page: Playwright 的 :class:`~playwright.sync_api.Page` 对象。
        """
        super().__init__(page)
        logger.info("Tenant Manage Page Initialized")

        # ==================== 搜索区 ====================
        # 用 .first 避免 Element Plus 弹窗关闭后仍留 DOM 导致的 strict mode violation
        self.filter_tenant = page.get_by_placeholder("租户名称关键字").first
        self.btn_search = page.get_by_role("button", name="查询")
        self.btn_user_relation = page.get_by_role("button", name="用户关联")

        # 搜索区：租户类型下拉（form-item 定位，避开弹窗内同名下拉）
        self.formitem_search_tenant_type = page.locator(".ep-form-item:has-text('租户类型')").first
        self.select_wrapper_search_tenant_type = self.formitem_search_tenant_type.locator(".ep-select__wrapper").first

        # ==================== 数据表格 ====================
        self.table = page.get_by_role("table").first

        # ==================== 提示消息与确认弹窗 ====================
        self.alert = page.locator(".ep-message__content, .el-message__content").first
        self.btn_know = page.get_by_role("button", name="知道了")
        self.btn_delete_confirm = page.get_by_role("button", name="删除")
        self.btn_delete_cancel = page.get_by_role("button", name="取消")

        # 行操作"更多"下拉菜单
        self.dropdown_row_actions = page.locator(".ep-dropdown-menu, .el-dropdown-menu").last

        # ==================== 新增下级/同级租户弹窗 ====================
        self.dialog_add_child = page.get_by_role("dialog", name=re.compile(re.escape("新增下级租户")))
        self.input_add_child_code = self.dialog_add_child.get_by_placeholder("请输入租户编码")
        self.input_add_child_name = self.dialog_add_child.get_by_placeholder("请输入租户名称")

        self.dialog_add_sibling = page.get_by_role("dialog", name=re.compile(re.escape("新增同级租户")))
        self.input_add_sibling_code = self.dialog_add_sibling.get_by_placeholder("请输入租户编码")
        self.input_add_sibling_name = self.dialog_add_sibling.get_by_placeholder("请输入租户名称")

        # ==================== 编辑详情弹窗 ====================
        self.dialog_edit_detail = page.get_by_role("dialog", name=re.compile(re.escape("编辑详情")))
        self.input_edit_tenant_name = self.dialog_edit_detail.get_by_placeholder("请输入租户名称")

        # ==================== 用户关联弹窗 ====================
        self.dialog_user_relation = page.get_by_role("dialog", name=re.compile(re.escape("用户关联")))
        self.input_relation_tenant_search = self.dialog_user_relation.get_by_placeholder("租户名称关键字")
        self.table_relation_tenant = self.dialog_user_relation.locator("table").first
        self.input_relation_user_search_available = self.dialog_user_relation.get_by_placeholder(
            "用户账号、用户姓名关键字"
        ).first
        self.input_relation_user_search_bound = self.dialog_user_relation.get_by_placeholder(
            "用户账号、用户姓名关键字"
        ).nth(1)
        self.table_relation_available = self.dialog_user_relation.get_by_role("table").first
        self.table_relation_bound = self.dialog_user_relation.get_by_role("table").nth(1)
        self.btn_relation_query_available = self.dialog_user_relation.get_by_role("button", name="查询").nth(0)
        self.btn_relation_add = self.dialog_user_relation.get_by_role("button", name="添加")
        self.btn_relation_remove = self.dialog_user_relation.get_by_role("button", name="删除")
        self.btn_relation_close = self.dialog_user_relation.get_by_role("button", name="关闭", exact=True)

        # ==================== 提示/确认弹窗 ====================
        self.dialog_prompt = page.get_by_role("dialog", name=re.compile(r"提示|确认"))

    # ==================== 内部辅助方法 ====================

    def _get_tenant_row(self, tenant_name: str) -> Locator:
        """定位指定租户名称对应的表格行。"""
        return self.page.get_by_role("row", name=re.compile(re.escape(tenant_name))).first

    def _get_dialog(self, dialog_name: str) -> Locator:
        """按弹窗名称定位 dialog。"""
        return self.page.get_by_role("dialog", name=re.compile(re.escape(dialog_name)))

    def _click_row_action(self, tenant_name: str, icon_selector: str) -> None:
        """在指定租户行点击操作图标，图标隐藏时从"更多"下拉菜单点选。

        Args:
            tenant_name: 租户名称，用于定位行
            icon_selector: 操作图标的 CSS 选择器（remixicon 类名或自定义标识）
        """
        row = self._get_tenant_row(tenant_name)
        expect(row).to_be_visible()
        icon = row.locator(icon_selector).first
        if icon.is_visible():
            icon.click()
        else:
            # 图标隐藏在"更多"下拉菜单中
            more_btn = row.locator(".ri-more-line").first
            if more_btn.is_visible():
                more_btn.click()
                self.page.wait_for_timeout(UITimeout.SHORT)
                item = self._locate_more_menu_item(icon_selector)
                item.evaluate("el => el.click()")  # 用 evaluate 避免可见性检查
            else:
                icon.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def _locate_more_menu_item(self, icon_selector: str) -> Locator:
        """根据图标选择器映射"更多"下拉菜单中的目标选项。"""
        dropdown = self.dropdown_row_actions
        mapping = {
            ".ri-edit-2-line": ("编辑", False),
            ".ri-delete-bin-line": ("删除", False),
            ".ri-user-settings-line": ("用户关联", False),
            ".ri-add-child": ("新增下级", True),
            ".ri-add-sibling": ("新增同级租户", False),
        }
        if icon_selector not in mapping:
            raise Exception(f"未在下拉菜单中找到对应操作【{icon_selector}】")
        text, use_regex = mapping[icon_selector]
        if use_regex:
            return dropdown.get_by_text(re.compile(text)).first
        return dropdown.get_by_text(text).first

    def _select_tenant_type(self, dialog: Locator, tenant_type: str) -> None:
        """在弹窗表单中选择租户类型下拉（force 点击避开 placeholder 拦截）。"""
        form_item = dialog.locator(".ep-form-item:has-text('租户类型')").first
        select_wrapper = form_item.locator(".ep-select__wrapper").first
        select_wrapper.click(force=True)
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.page.get_by_role("option", name=tenant_type, exact=True).click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def _click_dropdown_type(self) -> None:
        """点击搜索区的租户类型下拉（form-item 定位，失败则 fallback）。"""
        try:
            expect(self.select_wrapper_search_tenant_type).to_be_visible()
            self.select_wrapper_search_tenant_type.click()
        except Exception:
            fallback = self.page.get_by_text("请选择租户类型查询用户关联").locator(".ep-select__wrapper")
            expect(fallback).to_be_visible()
            fallback.click()

    def _select_all_in_table(self, table: Locator) -> None:
        """在指定表格中点击"选择所有行"checkbox。"""
        select_all = table.get_by_role("checkbox", name="选择所有行")
        if select_all.is_visible():
            select_all.click(force=True)
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    # ==================== 搜索操作 ====================

    def search_tenant(self, keyword: str) -> None:
        """按关键字搜索租户。"""
        logger.info(f"搜索租户关键字：{keyword}")
        self.filter_tenant.fill(keyword)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.QUERY)

    def clear_search(self) -> None:
        """清空搜索条件并重新查询，恢复完整列表。"""
        logger.info("清空搜索条件")
        self.filter_tenant.clear()
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def search_by_tenant_type(self, tenant_type: str) -> None:
        """通过租户类型下拉筛选搜索。"""
        logger.info(f"按租户类型搜索: {tenant_type}")
        self._click_dropdown_type()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.page.get_by_role("option", name=tenant_type, exact=True).click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        self.btn_search.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def get_tenant_type_options(self) -> List[str]:
        """获取租户类型下拉中的所有选项文本。"""
        logger.info("获取租户类型下拉选项")
        self._click_dropdown_type()
        self.page.wait_for_timeout(UITimeout.SHORT)
        options = self.page.get_by_role("option")
        texts = [options.nth(i).inner_text() for i in range(options.count())]
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(UITimeout.ANIMATION)
        logger.info(f"租户类型选项: {texts}")
        return texts

    # ==================== 行操作 ====================

    def click_add_child(self, tenant_name: str) -> None:
        """点击指定租户行的"新增下级"图标（最后一个 img.table-action-icon）。"""
        logger.info(f"点击【{tenant_name}】的新增下级图标")
        row = self._get_tenant_row(tenant_name)
        expect(row).to_be_visible()
        add_icon = row.locator("img.table-action-icon").last
        expect(add_icon).to_be_visible()
        add_icon.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_add_sibling(self, tenant_name: str) -> None:
        """点击指定租户行的"新增同级"图标（第一个 img.table-action-icon）。"""
        logger.info(f"点击【{tenant_name}】的新增同级图标")
        row = self._get_tenant_row(tenant_name)
        expect(row).to_be_visible()
        add_icon = row.locator("img.table-action-icon").first
        expect(add_icon).to_be_visible()
        add_icon.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_cluster_manage(self, tenant_name: str) -> None:
        """点击指定租户行的"集群管理"按钮（在"更多"下拉菜单中）。"""
        logger.info(f"点击【{tenant_name}】的集群管理按钮")
        row = self._get_tenant_row(tenant_name)
        expect(row).to_be_visible()
        more_btn = row.locator(".ri-more-line").first
        expect(more_btn).to_be_visible()
        more_btn.click()
        self.page.wait_for_timeout(UITimeout.SHORT)
        item = self.dropdown_row_actions.get_by_text("集群管理").first
        expect(item).to_be_visible()
        item.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def click_edit(self, tenant_name: str) -> None:
        """点击编辑图标。"""
        logger.info(f"点击【{tenant_name}】的编辑图标")
        self._click_row_action(tenant_name, ".ri-edit-2-line")

    def click_delete(self, tenant_name: str) -> None:
        """点击删除图标。"""
        logger.info(f"点击【{tenant_name}】的删除图标")
        self._click_row_action(tenant_name, ".ri-delete-bin-line")

    def click_user_relation_icon(self, tenant_name: str) -> None:
        """点击行内用户关联图标。"""
        logger.info(f"点击【{tenant_name}】的用户关联图标")
        self._click_row_action(tenant_name, ".ri-user-settings-line")

    def click_user_relation_icon_for_tenant(self, tenant_name: str) -> None:
        """点击行内用户关联图标（含较长等待）。"""
        self.click_user_relation_icon(tenant_name)
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    # ==================== 新增/编辑/删除租户 ====================

    def fill_add_child_form(self, tenant_code: str, tenant_name: str, tenant_type: str = "省级公司") -> None:
        """填写新增下级租户表单。"""
        expect(self.dialog_add_child).to_be_visible()
        self.input_add_child_code.fill(tenant_code)
        self.input_add_child_name.fill(tenant_name)
        self._select_tenant_type(self.dialog_add_child, tenant_type)

    def fill_add_sibling_form(self, tenant_code: str, tenant_name: str, tenant_type: str = "省级公司") -> None:
        """填写新增同级租户表单。"""
        expect(self.dialog_add_sibling).to_be_visible()
        self.input_add_sibling_code.fill(tenant_code)
        self.input_add_sibling_name.fill(tenant_name)
        self._select_tenant_type(self.dialog_add_sibling, tenant_type)

    def click_confirm(self, dialog_name: Optional[str] = None) -> None:
        """点击确定按钮。"""
        if dialog_name:
            self._get_dialog(dialog_name).get_by_role("button", name="确定").click()
        else:
            self.page.get_by_role("button", name="确定").click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def click_cancel(self, dialog_name: Optional[str] = None) -> None:
        """点击取消按钮。"""
        if dialog_name:
            self._get_dialog(dialog_name).get_by_role("button", name="取消").click()
        else:
            self.page.get_by_role("button", name="取消").click()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def add_child_tenant(self, parent_name: str, tenant_code: str, tenant_name: str,
                         tenant_type: str = "省级公司") -> None:
        """完整流程：新增下级租户。"""
        self.click_add_child(parent_name)
        self.fill_add_child_form(tenant_code, tenant_name, tenant_type)
        self.click_confirm("新增下级租户")

    def add_sibling_tenant(self, sibling_name: str, tenant_code: str, tenant_name: str,
                           tenant_type: str = "省级公司") -> None:
        """完整流程：新增同级租户。"""
        self.click_add_sibling(sibling_name)
        self.fill_add_sibling_form(tenant_code, tenant_name, tenant_type)
        self.click_confirm("新增同级租户")

    def edit_tenant_name(self, tenant_name: str, new_name: str) -> None:
        """编辑租户名称。"""
        self.click_edit(tenant_name)
        expect(self.dialog_edit_detail).to_be_visible()
        self.input_edit_tenant_name.clear()
        self.input_edit_tenant_name.fill(new_name)
        self.click_confirm("编辑详情")

    def edit_tenant(self, tenant_name: str, new_name: str) -> None:
        """编辑租户名称（edit_tenant_name 的别名）。"""
        self.edit_tenant_name(tenant_name, new_name)

    def edit_tenant_type(self, tenant_name: str, new_type: str) -> None:
        """编辑租户类型。"""
        logger.info(f"编辑租户【{tenant_name}】类型为【{new_type}】")
        self.click_edit(tenant_name)
        expect(self.dialog_edit_detail).to_be_visible()
        self._select_tenant_type(self.dialog_edit_detail, new_type)
        self.click_confirm("编辑详情")

    def get_edit_dialog(self, tenant_name: str) -> Locator:
        """打开编辑弹窗并返回 dialog 定位器。"""
        self.click_edit(tenant_name)
        expect(self.dialog_edit_detail).to_be_visible()
        return self.dialog_edit_detail

    def delete_tenant(self, tenant_name: str) -> None:
        """删除租户（需已解绑用户和集群）。"""
        self.click_delete(tenant_name)
        expect(self.dialog_prompt).to_be_visible()
        self.dialog_prompt.get_by_role("button", name="删除").click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def delete_tenant_with_confirm(self, tenant_name: str, confirm: bool = True) -> None:
        """删除租户，在确认弹窗中点击"删除"或"取消"。"""
        self.click_delete(tenant_name)
        expect(self.dialog_prompt).to_be_visible()
        if confirm:
            self.dialog_prompt.get_by_role("button", name="删除").click()
        else:
            self.dialog_prompt.get_by_role("button", name="取消").click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    # ==================== 用户关联 ====================

    def open_user_relation_dialog(self) -> None:
        """点击顶部"用户关联"按钮。"""
        logger.info("点击顶部【用户关联】按钮")
        self.btn_user_relation.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def select_tenant_in_relation(self, tenant_name: str) -> None:
        """在用户关联弹窗中选择租户（左侧租户树中点击）。"""
        expect(self.dialog_user_relation).to_be_visible()
        self.input_relation_tenant_search.fill(tenant_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(UITimeout.STABILIZE)
        tenant_row = self.table_relation_tenant.get_by_text(tenant_name, exact=True).first
        expect(tenant_row).to_be_visible()
        tenant_row.click()
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def search_available_users(self, keyword: str) -> None:
        """在用户关联弹窗中搜索可关联用户。"""
        expect(self.dialog_user_relation).to_be_visible()
        self.input_relation_user_search_available.fill(keyword)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def search_bound_users(self, keyword: str) -> None:
        """在用户关联弹窗中搜索已关联用户。"""
        expect(self.dialog_user_relation).to_be_visible()
        self.input_relation_user_search_bound.fill(keyword)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(UITimeout.STABILIZE)

    def select_all_available_users(self) -> None:
        """在可关联用户表格中全选。"""
        self._select_all_in_table(self.table_relation_available)

    def select_all_bound_users(self) -> None:
        """在已关联用户表格中全选。"""
        self._select_all_in_table(self.table_relation_bound)

    def select_available_user(self, user_account: str) -> None:
        """在可关联用户表格中勾选指定用户。"""
        self._check_user_in_relation(user_account)

    def select_bound_user(self, user_account: str) -> None:
        """在已关联用户表格中勾选指定用户。"""
        self._check_user_in_relation(user_account)

    def _check_user_in_relation(self, user_account: str) -> None:
        """在用户关联弹窗中勾选指定用户行的 checkbox。"""
        row = self.dialog_user_relation.get_by_role("row", name=re.compile(re.escape(user_account))).first
        if row.is_visible():
            checkbox = row.locator(".ep-checkbox__input, .el-checkbox__input").first
            checkbox.evaluate("el => { el.querySelector('input').click(); }")
            self.page.wait_for_timeout(UITimeout.ANIMATION)

    def click_add_bind(self) -> None:
        """点击添加按钮（绑定用户）。"""
        if self.btn_relation_add.is_enabled():
            self.btn_relation_add.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def click_remove_bind(self) -> None:
        """点击删除按钮（解绑用户）。"""
        if self.btn_relation_remove.is_enabled():
            self.btn_relation_remove.click()
            self.page.wait_for_timeout(UITimeout.SHORT)

    def bind_user_to_tenant(self, tenant_name: str, user_account: str) -> None:
        """在用户关联弹窗中添加用户关联。"""
        expect(self.dialog_user_relation).to_be_visible()

        self.input_relation_user_search_available.fill(user_account)
        self.btn_relation_query_available.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

        row = self.dialog_user_relation.get_by_role("row", name=re.compile(re.escape(user_account)))
        expect(row).to_be_visible()
        row.get_by_role("checkbox", name="选择当前行").click(force=True)

        self.btn_relation_add.click()
        self.page.wait_for_timeout(UITimeout.SHORT)

    def close_user_relation_dialog(self) -> None:
        """关闭用户关联弹窗（关闭失败则按 Escape）。"""
        try:
            self.btn_relation_close.click(timeout=3000)
        except Exception:
            self.page.keyboard.press("Escape")
        expect(self.dialog_user_relation).to_be_hidden()
        self.page.wait_for_timeout(UITimeout.ANIMATION)

    def get_available_user_table(self) -> Locator:
        """获取可关联用户表格。"""
        return self.table_relation_available

    def get_bound_user_table(self) -> Locator:
        """获取已关联用户表格。"""
        return self.table_relation_bound

    # ==================== 数据清理 ====================

    def cleanup_tenant(self, tenant_name: str) -> None:
        """安全删除租户：先搜索再删除，忽略错误。"""
        logger.info(f"清理租户：{tenant_name}")
        try:
            self.search_tenant(tenant_name)
            self.page.wait_for_timeout(UITimeout.STABILIZE)
            row = self._get_tenant_row(tenant_name)
            if row.is_visible():
                self.delete_tenant(tenant_name)
                logger.info(f"租户【{tenant_name}】删除成功")
            else:
                logger.info(f"租户【{tenant_name}】不存在，无需清理")
        except Exception as e:
            logger.info(f"清理租户【{tenant_name}】时出错：{e}")

    def cleanup_tenant_recursive(self, tenant_name: str) -> None:
        """安全递归删除租户：有下级租户时关闭弹窗并提示无法删除。"""
        logger.info(f"递归清理租户：{tenant_name}")
        try:
            self.search_tenant(tenant_name)
            self.page.wait_for_timeout(UITimeout.SHORT)
            row = self._get_tenant_row(tenant_name)
            if not row.is_visible():
                logger.info(f"租户【{tenant_name}】不存在，无需清理")
                return

            self.click_delete(tenant_name)
            expect(self.dialog_prompt).to_be_visible()
            msg = self.dialog_prompt.inner_text()
            if "下级租户" in msg:
                # 有下级租户，无法直接删除，关闭弹窗
                close_btn = self.dialog_prompt.get_by_role("button", name=re.compile(r"关闭|确定|取消"))
                if close_btn.is_visible():
                    close_btn.click()
                self.page.wait_for_timeout(UITimeout.SHORT)
                logger.info(f"租户【{tenant_name}】有下级租户，无法直接删除")
            else:
                delete_btn = self.dialog_prompt.get_by_role("button", name="删除")
                if delete_btn.is_visible():
                    delete_btn.click()
                self.page.wait_for_timeout(UITimeout.SHORT)
                logger.info(f"租户【{tenant_name}】删除处理完成")
        except Exception as e:
            logger.info(f"清理租户【{tenant_name}】时出错：{e}")
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(UITimeout.ANIMATION)
            except Exception:
                pass
